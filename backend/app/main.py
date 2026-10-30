from __future__ import annotations

import base64
from io import BytesIO
import hashlib
import hmac
import json
import re
import secrets
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Any
from uuid import UUID

import httpx
import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from sqlalchemy import inspect, select, func, or_, and_, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import settings
from .auth_security import require_user, optional_user, user_payload, TOKEN_ALGORITHM
from .auth_routes import router as auth_router
from .phase5_routes import router as phase5_router
from .plan_routes import router as plan_router
from .phase5_service import record_review_result
from .practice_policy import (
    is_supported_practice_exercise,
    practice_exercise_kind,
    public_practice_type,
)
from .diagram_assets import validate_dynamic_diagram_model
from .plan_entitlements import (
    PLAN_DEFINITIONS,
    PLAN_PRIORITY,
    active_entitlements as resolve_active_entitlements,
    build_plan_snapshot,
    effective_plan_id,
    plan_features,
    plan_limits,
    can_access_exercise,
    required_exercise_plan,
    require_exercise_access,
    require_feature,
)
from .db import engine, get_db
from .project_guide_service import (
    build_project_guide,
    is_protected_project_path,
    project_guide_zip,
)
from .models import (
    AuditLog,
    Bookmark,
    Certificate,
    Course,
    Entitlement,
    ExamAttempt,
    Exercise,
    ExerciseProgress,
    Lesson,
    LessonProgress,
    Module,
    MockAssessmentAttempt,
    PracticalExamAttempt,
    PaymentRecord,
    User,
    UserActivityDay,
    WebhookEvent,
    XPTransaction,
)
from .schemas import (
    AvatarUpdate,
    ExerciseSubmission,
    LoginInput,
    PaymentCreateInput,
    PaymentVerifyInput,
    ProgressUpdate,
    RegisterInput,
)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Base API for CodeLeaf. Payment and account endpoints require configured PostgreSQL and provider secrets.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
)


@app.middleware("http")
async def enforce_allowed_origin(request: Request, call_next):
    # Origin validation plus a signed double-submit token protects cookie-authenticated writes.
    if (
        request.method in {"POST", "PUT", "PATCH", "DELETE"}
        and request.url.path != "/api/payments/webhook"
    ):
        origin = request.headers.get("origin")
        if origin and origin.rstrip("/") not in settings.allowed_origins:
            return JSONResponse(
                status_code=403, content={"detail": "Request origin is not allowed."}
            )
        session_cookie = request.cookies.get("codeleaf_session")
        if session_cookie:
            csrf_cookie = request.cookies.get("codeleaf_csrf", "")
            csrf_header = request.headers.get("x-csrf-token", "")
            try:
                claims = jwt.decode(
                    session_cookie, settings.jwt_secret, algorithms=[TOKEN_ALGORITHM]
                )
                csrf_claim = claims.get("csrf", "")
            except jwt.InvalidTokenError:
                csrf_claim = ""
            if (
                not origin
                or origin.rstrip("/") not in settings.allowed_origins
                or not csrf_cookie
                or not csrf_header
                or not csrf_claim
                or not hmac.compare_digest(csrf_cookie, csrf_header)
                or not hmac.compare_digest(csrf_cookie, csrf_claim)
            ):
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "CSRF validation failed. Refresh the page and try again."
                    },
                )
    return await call_next(request)


app.include_router(auth_router)
app.include_router(phase5_router)
app.include_router(plan_router)


SESSION_COOKIE = "codeleaf_session"
TOKEN_ALGORITHM = "HS256"
# Award rules are owned by the backend and exposed read-only through /api/public/config.
XP_REWARDS = {"lesson": 20, "exercise": 20, "max_multiplier": 1.5}


# Integer INR subunits (paise) are fixed by the server; the browser never supplies an amount.
PLAN_CONFIG: dict[str, dict[str, Any]] = {
    plan_id: {
        "title": definition["title"],
        "amount_paise": definition["amount_paise"],
        "currency": "INR",
        "kind": "subscription" if definition["billing"] == "monthly" else "order",
    }
    for plan_id, definition in PLAN_DEFINITIONS.items()
    if plan_id != "free"
}
COURSE_CONTENT_ROOT = Path(__file__).resolve().parents[1] / "content" / "courses"


def draft_course_preview_enabled() -> bool:
    """Enable draft course preview only when explicitly opted in for local development."""
    return (
        settings.app_env.strip().lower() in {"development", "local"}
        and settings.preview_draft_courses
    )


def get_course_visible_to_reader(db: Session, course_slug: str) -> Course:
    """Return published courses publicly, or draft courses in explicitly enabled local preview."""
    query = select(Course).where(Course.slug == course_slug)
    if not draft_course_preview_enabled():
        query = query.where(Course.published.is_(True))
    course = db.scalar(query)
    if course is None:
        raise HTTPException(status_code=404, detail="Published course was not found.")
    return course


PUBLIC_COURSES = [
    {
        "slug": "html",
        "title": "HTML",
        "description": "Structure accessible pages from the ground up.",
        "category": "Web Development",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "css",
        "title": "CSS",
        "description": "Style, layout, animation and responsive interfaces.",
        "category": "Web Development",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "javascript",
        "title": "JavaScript",
        "description": "Make websites interactive and dynamic.",
        "category": "Web Development",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "sql",
        "title": "SQL",
        "description": "Query, organize and understand relational data.",
        "category": "Databases",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "python",
        "title": "Python",
        "description": "Build programs, automation and data tools.",
        "category": "Programming",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "java",
        "title": "Java",
        "description": "Learn object-oriented programming and the Java ecosystem.",
        "category": "Programming",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "php",
        "title": "PHP",
        "description": "Build server-rendered websites and backend services.",
        "category": "Backend & APIs",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "c",
        "title": "C",
        "description": "Learn programming fundamentals and memory-aware code.",
        "category": "Programming",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "cpp",
        "title": "C++",
        "description": "Build efficient programs with modern C++.",
        "category": "Programming",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "csharp",
        "title": "C#",
        "description": ".NET programming for applications, games and services.",
        "category": "Programming",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "aws",
        "title": "AWS",
        "description": "Understand cloud computing and core AWS services.",
        "category": "Cloud & DevOps",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "bootstrap",
        "title": "Bootstrap",
        "description": "Build responsive interfaces with a component toolkit.",
        "category": "Web Development",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "react",
        "title": "React — From Beginner to Professional",
        "description": "Build interactive, accessible React applications from JSX and state through testing, performance, rendering architecture, and deployment.",
        "category": "Web Development",
        "level": "Beginner to Advanced",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "mysql",
        "title": "MySQL",
        "description": "Create tables, query data and manage relational databases.",
        "category": "Databases",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "jquery",
        "title": "jQuery",
        "description": "Understand the jQuery API and legacy web patterns.",
        "category": "Web Development",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "excel",
        "title": "Excel",
        "description": "Use formulas, tables, charts and practical data workflows.",
        "category": "Data & Analytics",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "xml",
        "title": "XML",
        "description": "Structure, validate and exchange data with XML.",
        "category": "Data Formats",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "django",
        "title": "Django",
        "description": "Build data-driven web apps with Django and Python.",
        "category": "Backend & APIs",
        "level": "Intermediate",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "flask",
        "title": "Flask",
        "description": "Build lightweight Python web apps and APIs with routes, templates and extensions.",
        "category": "Backend & APIs",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "numpy",
        "title": "NumPy",
        "description": "Work with arrays, vectorization and numerical computing.",
        "category": "Data & Analytics",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "pandas",
        "title": "Pandas",
        "description": "Clean, transform and analyze tabular datasets.",
        "category": "Data & Analytics",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "nodejs",
        "title": "Node.js",
        "description": "Run JavaScript on the server and build services.",
        "category": "Backend & APIs",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "dsa",
        "title": "DSA",
        "description": "Study data structures, algorithms and complexity.",
        "category": "Computer Science",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "typescript",
        "title": "TypeScript",
        "description": "Add static types and safer tooling to JavaScript projects.",
        "category": "Web Development",
        "level": "Intermediate",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "angular",
        "title": "Angular",
        "description": "Build structured web applications with Angular.",
        "category": "Web Development",
        "level": "Intermediate",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "angularjs",
        "title": "AngularJS",
        "description": "Understand AngularJS fundamentals and legacy maintenance.",
        "category": "Web Development",
        "level": "Intermediate",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "git",
        "title": "Git",
        "description": "Track changes, branch safely and collaborate.",
        "category": "Cloud & DevOps",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "postgresql",
        "title": "PostgreSQL",
        "description": "Design relational data and write robust PostgreSQL queries.",
        "category": "Databases",
        "level": "Intermediate",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "mongodb",
        "title": "MongoDB",
        "description": "Model documents and query a document database.",
        "category": "Databases",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "asp",
        "title": "ASP",
        "description": "Explore classic ASP concepts and the ASP.NET ecosystem.",
        "category": "Backend & APIs",
        "level": "Intermediate",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "ai",
        "title": "AI Foundations",
        "description": "Explore artificial intelligence concepts, models and responsible use.",
        "category": "AI & Machine Learning",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "r",
        "title": "R",
        "description": "Analyze data and create statistical visualizations with R.",
        "category": "Data & Analytics",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "go",
        "title": "Go",
        "description": "Build concurrent services with Go.",
        "category": "Programming",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "kotlin",
        "title": "Kotlin",
        "description": "Learn concise, type-safe Kotlin programming.",
        "category": "Programming",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "swift",
        "title": "Swift",
        "description": "Learn Swift fundamentals and Apple-platform development concepts.",
        "category": "Programming",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "sass",
        "title": "Sass",
        "description": "Write maintainable CSS with variables, nesting and modules.",
        "category": "Web Development",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "vue",
        "title": "Vue.js",
        "description": "Build reactive interfaces with Vue.",
        "category": "Web Development",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "generative-ai",
        "title": "Generative AI",
        "description": "Understand generative models, prompting and responsible applications.",
        "category": "AI & Machine Learning",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "scipy",
        "title": "SciPy",
        "description": "Use scientific computing algorithms and numerical tools.",
        "category": "Data & Analytics",
        "level": "Intermediate",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "cybersecurity",
        "title": "Cybersecurity",
        "description": "Learn defensive security concepts, risk and safe testing practices.",
        "category": "Security",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "data-science",
        "title": "Data Science",
        "description": "Move from data collection to analysis, modeling and communication.",
        "category": "Data & Analytics",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "bash",
        "title": "Bash",
        "description": "Automate command-line tasks with shell scripts.",
        "category": "Cloud & DevOps",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "rust",
        "title": "Rust",
        "description": "Build reliable systems with ownership and type safety.",
        "category": "Programming",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "nextjs",
        "title": "Next.js",
        "description": "Build React applications with routing and server features.",
        "category": "Web Development",
        "level": "Intermediate",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "tailwind-css",
        "title": "Tailwind CSS",
        "description": "Design responsive interfaces with utility-first CSS.",
        "category": "Web Development",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "expressjs",
        "title": "Express.js",
        "description": "Create web servers and APIs with Express.",
        "category": "Backend & APIs",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "fastapi",
        "title": "FastAPI",
        "description": "Build typed, high-performance APIs with Python.",
        "category": "Backend & APIs",
        "level": "Intermediate",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "rest-api-development",
        "title": "REST API Development",
        "description": "Design, document, secure and test RESTful APIs.",
        "category": "Backend & APIs",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "dart",
        "title": "Dart",
        "description": "Learn Dart syntax, asynchronous code and tooling.",
        "category": "Programming",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "powershell",
        "title": "PowerShell",
        "description": "Automate Windows and cross-platform administration tasks.",
        "category": "Cloud & DevOps",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "ruby",
        "title": "Ruby",
        "description": "Learn expressive programming and Ruby conventions.",
        "category": "Programming",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "lua",
        "title": "Lua",
        "description": "Use lightweight Lua for scripting and embedded logic.",
        "category": "Programming",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "solidity",
        "title": "Solidity",
        "description": "Understand smart-contract development and secure patterns.",
        "category": "Programming",
        "level": "Intermediate",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "sqlite",
        "title": "SQLite",
        "description": "Use an embedded relational database and SQL locally.",
        "category": "Databases",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "redis",
        "title": "Redis",
        "description": "Learn in-memory data structures, caching and key-value workflows.",
        "category": "Databases",
        "level": "Intermediate",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "docker",
        "title": "Docker",
        "description": "Package applications into repeatable containers.",
        "category": "Cloud & DevOps",
        "level": "Intermediate",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "linux",
        "title": "Linux",
        "description": "Navigate the shell, manage files, permissions and processes.",
        "category": "Cloud & DevOps",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "github-actions",
        "title": "GitHub Actions",
        "description": "Automate tests, builds and deployments with CI/CD workflows.",
        "category": "Cloud & DevOps",
        "level": "Intermediate",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "pytorch",
        "title": "PyTorch",
        "description": "Build and train neural networks with tensors and autograd.",
        "category": "AI & Machine Learning",
        "level": "Intermediate",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "scikit-learn",
        "title": "scikit-learn",
        "description": "Build machine-learning pipelines and evaluate models.",
        "category": "AI & Machine Learning",
        "level": "Intermediate",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "json-yaml",
        "title": "JSON & YAML",
        "description": "Read and write common data serialization and configuration formats.",
        "category": "Data Formats",
        "level": "Beginner",
        "lesson_count": 0,
        "status": "roadmap",
    },
    {
        "slug": "web-application-security",
        "title": "Web Application Security",
        "description": "Learn secure web design, threat modeling and defensive testing.",
        "category": "Security",
        "level": "Intermediate",
        "lesson_count": 0,
        "status": "roadmap",
    },
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def payment_checkout_readiness() -> dict[str, Any]:
    """Expose safe configuration readiness without returning any secret values."""
    common_missing: list[str] = []
    if not settings.razorpay_key_id:
        common_missing.append("RAZORPAY_KEY_ID")
    if not settings.razorpay_key_secret:
        common_missing.append("RAZORPAY_KEY_SECRET")
    if not settings.razorpay_webhook_secret:
        common_missing.append("RAZORPAY_WEBHOOK_SECRET")

    def plan_status(plan_id: str) -> dict[str, Any]:
        missing = list(common_missing)
        if plan_id == "pro" and not settings.razorpay_pro_plan_id:
            missing.append("RAZORPAY_PRO_PLAN_ID")
        elif plan_id == "max" and not settings.razorpay_max_plan_id:
            missing.append("RAZORPAY_MAX_PLAN_ID")
        return {"ready": not missing, "missing_environment": missing}

    return {
        "provider": "razorpay",
        "common_credentials_ready": not common_missing,
        "webhook_secret_configured": bool(settings.razorpay_webhook_secret),
        "plans": {
            "pro": plan_status("pro"),
            "max": plan_status("max"),
            "full_access": plan_status("full_access"),
        },
        # The API cannot prove that the merchant also saved the webhook URL/events
        # in the provider dashboard; that is an explicit deployment checklist item.
        "dashboard_webhook_setup_must_be_verified": True,
    }


def ensure_payment_config() -> tuple[str, str]:
    key_id, key_secret = settings.razorpay_key_id, settings.razorpay_key_secret
    missing: list[str] = []
    if not key_id:
        missing.append("RAZORPAY_KEY_ID")
    if not key_secret:
        missing.append("RAZORPAY_KEY_SECRET")
    if not settings.razorpay_webhook_secret:
        missing.append("RAZORPAY_WEBHOOK_SECRET")
    if missing:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "PAYMENT_CONFIGURATION_INCOMPLETE",
                "message": "Secure checkout is temporarily unavailable because the payment provider is not fully configured.",
                "missing_environment": missing,
            },
        )
    return str(key_id), str(key_secret)


def active_entitlements(db: Session, user_id: UUID) -> list[Entitlement]:
    """Compatibility wrapper; central plan service owns expiration semantics."""
    return resolve_active_entitlements(db, user_id)


async def razorpay_request(
    method: str, path: str, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    key_id, key_secret = ensure_payment_config()
    url = f"https://api.razorpay.com/v1/{path.lstrip('/')}"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.request(
                method, url, auth=(key_id, key_secret), json=payload
            )
    except httpx.HTTPError:
        raise HTTPException(
            status_code=502,
            detail="Could not reach the payment provider. Please try again.",
        )
    if response.status_code >= 400:
        try:
            body = response.json()
            provider_message = body.get("error", {}).get(
                "description", "Payment provider request failed."
            )
        except ValueError:
            provider_message = "Payment provider request failed."
        # Avoid returning raw credentials or unfiltered provider payloads to the browser.
        raise HTTPException(status_code=502, detail=provider_message[:240])
    try:
        return response.json()
    except ValueError:
        raise HTTPException(
            status_code=502, detail="Payment provider returned an invalid response."
        )


def grant_entitlement(
    db: Session,
    *,
    user_id: UUID,
    plan_id: str,
    payment_record: PaymentRecord,
    subscription_id: str | None = None,
    ends_at: datetime | None = None,
) -> Entitlement:
    # Idempotent per payment for one-time purchases and per subscription for recurring access.
    query = select(Entitlement).where(
        Entitlement.user_id == user_id, Entitlement.plan_id == plan_id
    )
    if subscription_id:
        query = query.where(Entitlement.provider_subscription_id == subscription_id)
    else:
        query = query.where(Entitlement.source_payment_id == payment_record.id)
    ent = db.scalar(query)
    is_new = ent is None
    old_end = ent.ends_at if ent is not None else None
    if ent is None:
        ent = Entitlement(
            user_id=user_id,
            plan_id=plan_id,
            status="active",
            source_payment_id=payment_record.id,
            provider_subscription_id=subscription_id,
            starts_at=utc_now(),
            ends_at=ends_at,
        )
        db.add(ent)
        db.flush()
    else:
        ent.status = "active"
        ent.ends_at = ends_at
    if is_new or old_end != ends_at:
        db.add(
            AuditLog(
                actor_user_id=user_id,
                action="entitlement.granted" if is_new else "entitlement.renewed",
                resource_type="entitlement",
                resource_id=str(ent.id),
                details={
                    "plan_id": plan_id,
                    "payment_record_id": str(payment_record.id),
                    "provider_subscription_id": subscription_id,
                    "ends_at": ends_at.isoformat() if ends_at else None,
                },
                created_at=utc_now(),
            )
        )
    return ent


async def schedule_superseded_subscriptions_for_cancellation(
    db: Session,
    *,
    user_id: UUID,
    target_plan_id: str,
    excluding_subscription_id: str | None = None,
) -> None:
    """Stop lower-tier renewals without sending cycle-end cancellation to unpaid checkouts."""
    target_priority = PLAN_PRIORITY.get(target_plan_id, 0)
    records = db.scalars(
        select(PaymentRecord).where(
            PaymentRecord.user_id == user_id,
            PaymentRecord.kind == "subscription",
        ).order_by(PaymentRecord.created_at.desc())
    ).all()
    terminal = {"cancelled", "completed", "expired", "failed", "refunded", "reversed"}
    for record in records:
        sub_id = record.provider_subscription_id
        stored_payload = dict(record.provider_payload or {})
        if (
            not sub_id
            or sub_id == excluding_subscription_id
            or PLAN_PRIORITY.get(record.plan_id, 0) >= target_priority
            or record.status.lower() in terminal
            or stored_payload.get("cancel_at_cycle_end") is True
            or stored_payload.get("pending_checkout_cancelled") is True
        ):
            continue
        try:
            provider_state = await razorpay_request("GET", f"/subscriptions/{sub_id}")
            provider_status = str(provider_state.get("status") or record.status).lower()
            if provider_status in terminal:
                record.status = provider_status
                continue

            current_start = parse_epoch(provider_state.get("current_start"))
            current_end = parse_epoch(provider_state.get("current_end"))
            has_paid_cycle = (
                provider_status == "active"
                and current_start is not None
                and current_end is not None
                and current_end > utc_now()
            )
            if has_paid_cycle:
                cancel_at_cycle_end = True
            elif provider_status in {"created", "authenticated"}:
                # No paid cycle exists yet. Cancel immediately; cycle-end cancellation
                # is invalid for these provider states.
                cancel_at_cycle_end = False
            else:
                record.provider_payload = {
                    **stored_payload,
                    "cancellation_required": True,
                    "cancellation_reason": f"superseded_by_{target_plan_id}",
                    "cancellation_error": (
                        "Provider state has no verifiable current paid billing cycle."
                    ),
                }
                continue

            provider_result = await razorpay_request(
                "POST",
                f"/subscriptions/{sub_id}/cancel",
                {"cancel_at_cycle_end": cancel_at_cycle_end},
            )
            record.status = str(provider_result.get("status") or provider_status)
            record.provider_payload = {
                **stored_payload,
                "cancel_at_cycle_end": cancel_at_cycle_end,
                "pending_checkout_cancelled": not cancel_at_cycle_end,
                "cancellation_requested_at": utc_now().isoformat(),
                "cancellation_reason": f"superseded_by_{target_plan_id}",
                "cancellation_required": False,
            }
        except Exception as exc:
            detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
            record.provider_payload = {
                **stored_payload,
                "cancellation_required": True,
                "cancellation_reason": f"superseded_by_{target_plan_id}",
                "cancellation_error": str(detail)[:240],
            }


def parse_epoch(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return None


@app.get("/api/health")
def health() -> dict[str, Any]:
    """Liveness check: the process is running; database readiness is checked separately."""
    return {
        "status": "ok",
        "service": "codeleaf-api",
        "database_configured": bool(
            settings.database_url and settings.database_url.strip()
        ),
        "environment": settings.app_env,
    }


@app.get("/api/ready")
def readiness() -> dict[str, Any]:
    """Readiness check used by the host; do not send traffic before PostgreSQL/schema is ready."""
    if engine is None:
        raise HTTPException(status_code=503, detail="Database is not configured.")
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            tables = set(inspect(connection).get_table_names())
    except Exception as exc:
        # Do not expose database URLs, credentials or driver error detail through health routes.
        raise HTTPException(status_code=503, detail="Database is not ready.") from exc
    required_tables = {"courses", "course_modules", "lessons", "exercises", "users"}
    if required_tables - tables:
        raise HTTPException(status_code=503, detail="Database schema is not ready.")
    return {"status": "ready", "service": "codeleaf-api", "database": "connected"}


@app.get("/api/public/config")
def get_public_config() -> dict[str, Any]:
    """Public, non-secret reward settings used by the frontend display."""
    return {"xp_rewards": {**XP_REWARDS}}


def _catalog_manifest_counts(course_slug: str) -> tuple[int, int]:
    """Count published references/projects from their structured manifests.

    The rules mirror the learner-facing collection endpoints: unpublished rows stay
    hidden in production, and draft rows are visible only in explicit local preview.
    """
    preview_mode = draft_course_preview_enabled()
    course_dir = (COURSE_CONTENT_ROOT / course_slug).resolve()
    try:
        if COURSE_CONTENT_ROOT.resolve() not in course_dir.parents:
            return 0, 0
        metadata_path = course_dir / "course.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if not isinstance(metadata, dict):
            return 0, 0
    except (OSError, json.JSONDecodeError):
        return 0, 0

    project_count = 0
    project_files = metadata.get("project_files") or []
    if isinstance(project_files, list):
        for relative in project_files:
            try:
                candidate = (course_dir / str(relative)).resolve()
                if (
                    course_dir not in candidate.parents
                    or candidate.suffix.lower() != ".json"
                ):
                    continue
                item = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError, ValueError):
                continue
            if isinstance(item, dict) and (
                item.get("status") == "published"
                or (preview_mode and item.get("status") == "draft")
            ):
                project_count += 1

    reference_count = 0
    reference_rel = metadata.get("reference_index") or "references/reference-index.json"
    try:
        index_path = (course_dir / str(reference_rel)).resolve()
        if course_dir not in index_path.parents or index_path.suffix.lower() != ".json":
            return reference_count, project_count
        index_doc = json.loads(index_path.read_text(encoding="utf-8"))
        if not isinstance(index_doc, dict):
            return reference_count, project_count
        if index_doc.get("status") not in {None, "published"} and not preview_mode:
            return reference_count, project_count
    except (OSError, json.JSONDecodeError, ValueError):
        # The learner-facing endpoint returns 404 when the index is missing/invalid;
        # do not infer availability from stale inline records in course.json.
        return 0, project_count

    rows = (
        index_doc.get("references")
        or index_doc.get("sources")
        or index_doc.get("items")
        or []
    )
    loaded_rows: list[dict[str, Any]] = []
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict):
                loaded_rows.append(row)
            elif isinstance(row, str):
                try:
                    candidate = (course_dir / row).resolve()
                    if (
                        course_dir not in candidate.parents
                        or candidate.suffix.lower() != ".json"
                    ):
                        continue
                    entry = json.loads(candidate.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError, ValueError):
                    continue
                if isinstance(entry, dict):
                    loaded_rows.append(entry)
    if not loaded_rows:
        legacy_rows = metadata.get("references") or []
        if isinstance(legacy_rows, list):
            loaded_rows = [row for row in legacy_rows if isinstance(row, dict)]

    from urllib.parse import urlsplit

    for row in loaded_rows:
        if row.get("status") not in {None, "published"} and not preview_mode:
            continue
        title = str(
            row.get("title") or row.get("name") or row.get("label") or ""
        ).strip()
        url = str(row.get("url") or row.get("href") or "").strip()
        parsed = urlsplit(url)
        if title and parsed.scheme in {"http", "https"} and parsed.netloc:
            reference_count += 1
    return reference_count, project_count


def _course_manifest_learning_details(course_slug: str) -> dict[str, list[str]]:
    """Return authored audience/prerequisites/outcomes only when their manifest is visible."""
    empty = {"audience": [], "prerequisites": [], "learning_outcomes": []}
    course_dir = (COURSE_CONTENT_ROOT / course_slug).resolve()
    try:
        if COURSE_CONTENT_ROOT.resolve() not in course_dir.parents:
            return empty
        metadata = json.loads((course_dir / "course.json").read_text(encoding="utf-8"))
        if not isinstance(metadata, dict):
            return empty
        if (
            metadata.get("status") not in {None, "published"}
            and not draft_course_preview_enabled()
        ):
            return empty
        course_meta = (
            metadata.get("course") if isinstance(metadata.get("course"), dict) else {}
        )

        def normalise(value: Any) -> list[str]:
            if isinstance(value, str):
                return [value.strip()] if value.strip() else []
            if isinstance(value, list):
                return [
                    str(item).strip()
                    for item in value
                    if isinstance(item, (str, int, float)) and str(item).strip()
                ]
            return []

        return {
            "audience": normalise(
                course_meta.get("audience") or metadata.get("audience")
            ),
            "prerequisites": normalise(
                course_meta.get("prerequisites") or metadata.get("prerequisites")
            ),
            "learning_outcomes": normalise(
                course_meta.get("learning_outcomes")
                or course_meta.get("outcomes")
                or metadata.get("learning_outcomes")
            ),
        }
    except (OSError, json.JSONDecodeError, ValueError):
        return empty


@app.get("/api/courses")
def list_courses(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return the catalog and overlay counts/status from genuinely published DB content."""
    items = {
        item["slug"]: {
            **dict(item),
            "module_count": 0,
            "reference_count": 0,
            "project_count": 0,
            "practice_count": 0,
            "estimated_minutes": 0,
            "audience": [],
            "prerequisites": [],
            "learning_outcomes": [],
        }
        for item in PUBLIC_COURSES
    }
    preview_mode = draft_course_preview_enabled()
    practice_query = (
        select(Course.slug, Exercise.exercise_type, Exercise.starter, Exercise.prompt)
        .join(Module, Module.course_id == Course.id)
        .join(Lesson, Lesson.module_id == Module.id)
        .join(Exercise, Exercise.lesson_id == Lesson.id)
    )
    if preview_mode:
        practice_query = practice_query.where(
            or_(
                and_(
                    Course.published.is_(True),
                    Lesson.is_published.is_(True),
                    Exercise.is_published.is_(True),
                ),
                Lesson.content["_codeleaf_course_slug"].as_string() == Course.slug,
            )
        )
    else:
        practice_query = practice_query.where(
            Course.published.is_(True),
            Lesson.is_published.is_(True),
            Exercise.is_published.is_(True),
        )
    practice_counts: dict[str, int] = {}
    for slug, exercise_type, starter, prompt in db.execute(practice_query).all():
        if is_supported_practice_exercise(exercise_type, starter, slug, prompt):
            practice_counts[slug] = practice_counts.get(slug, 0) + 1
    course_query = select(Course).order_by(Course.sort_order.asc())
    if not draft_course_preview_enabled():
        course_query = course_query.where(Course.published.is_(True))
    visible_courses = db.scalars(course_query).all()
    for course in visible_courses:
        # In preview mode, only include draft courses that have a content manifest on disk.
        if (
            not course.published
            and draft_course_preview_enabled()
            and not (COURSE_CONTENT_ROOT / course.slug / "course.json").is_file()
        ):
            continue
        count_query = (
            select(func.count(Lesson.id))
            .join(Module, Lesson.module_id == Module.id)
            .where(Module.course_id == course.id)
        )
        if draft_course_preview_enabled():
            count_query = count_query.where(
                or_(
                    Lesson.is_published.is_(True),
                    Lesson.content["_codeleaf_course_slug"].as_string() == course.slug,
                )
            )
        else:
            count_query = count_query.where(Lesson.is_published.is_(True))
        lesson_count = int(db.scalar(count_query) or 0)
        module_count_query = (
            select(func.count(func.distinct(Module.id)))
            .join(Lesson, Lesson.module_id == Module.id)
            .where(Module.course_id == course.id)
        )
        if preview_mode:
            module_count_query = module_count_query.where(
                or_(
                    Lesson.is_published.is_(True),
                    Lesson.content["_codeleaf_course_slug"].as_string() == course.slug,
                )
            )
        else:
            module_count_query = module_count_query.where(Lesson.is_published.is_(True))
        module_count = int(db.scalar(module_count_query) or 0)
        minutes_query = (
            select(func.coalesce(func.sum(Lesson.estimated_minutes), 0))
            .join(Module, Lesson.module_id == Module.id)
            .where(Module.course_id == course.id)
        )
        if preview_mode:
            minutes_query = minutes_query.where(
                or_(
                    Lesson.is_published.is_(True),
                    Lesson.content["_codeleaf_course_slug"].as_string() == course.slug,
                )
            )
        else:
            minutes_query = minutes_query.where(Lesson.is_published.is_(True))
        estimated_minutes = int(db.scalar(minutes_query) or 0)
        reference_count, project_count = _catalog_manifest_counts(course.slug)
        details = _course_manifest_learning_details(course.slug)
        course_status = (
            "published"
            if course.published and lesson_count
            else (
                "preview"
                if draft_course_preview_enabled() and lesson_count
                else "roadmap"
            )
        )
        items[course.slug] = {
            "slug": course.slug,
            "title": course.title,
            "description": course.description,
            "category": course.category,
            "level": course.level,
            "lesson_count": lesson_count,
            "module_count": module_count,
            "reference_count": reference_count,
            "project_count": project_count,
            "practice_count": practice_counts.get(course.slug, 0),
            "estimated_minutes": estimated_minutes,
            **details,
            "status": course_status,
        }
    return {"items": list(items.values())}


@app.get("/api/courses/{course_slug}/references")
def list_course_references(
    course_slug: str, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Return the learner-safe reference index for one visible course."""
    course = get_course_visible_to_reader(db, course_slug)
    course_dir = (COURSE_CONTENT_ROOT / course_slug).resolve()
    try:
        metadata_path = (course_dir / "course.json").resolve()
        if course_dir not in metadata_path.parents or not metadata_path.is_file():
            raise FileNotFoundError("Course manifest was not found.")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=404, detail="Course reference index was not found."
        ) from exc

    reference_rel = metadata.get("reference_index") or "references/reference-index.json"
    index_path = (course_dir / str(reference_rel)).resolve()
    if (
        course_dir not in index_path.parents
        or not index_path.is_file()
        or index_path.suffix.lower() != ".json"
    ):
        raise HTTPException(
            status_code=404, detail="Course reference index was not found."
        )
    try:
        index_doc = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500, detail="Course reference index is invalid."
        ) from exc
    if (
        index_doc.get("status") not in {None, "published"}
        and not draft_course_preview_enabled()
    ):
        raise HTTPException(
            status_code=404,
            detail="This course reference index has not been published.",
        )

    raw_items = (
        index_doc.get("references")
        or index_doc.get("sources")
        or index_doc.get("items")
        or []
    )
    if not isinstance(raw_items, list):
        raw_items = []
    # Accept separate structured entry files while retaining support for older inline indexes.
    loaded_items: list[dict[str, Any]] = []
    for row in raw_items:
        if isinstance(row, str):
            try:
                entry_path = _safe_course_json_path(course_dir, row, "Reference entry")
                entry = json.loads(entry_path.read_text(encoding="utf-8"))
            except (HTTPException, OSError, json.JSONDecodeError):
                continue
            if isinstance(entry, dict):
                loaded_items.append(entry)
        elif isinstance(row, dict):
            loaded_items.append(row)
    if not loaded_items:
        # Legacy CodeLeaf courses store source records directly in course.json.
        legacy_rows = metadata.get("references", [])
        if isinstance(legacy_rows, list):
            loaded_items = [row for row in legacy_rows if isinstance(row, dict)]
    items: list[dict[str, Any]] = []
    from urllib.parse import urlsplit

    for row in loaded_items:
        if (
            row.get("status") not in {None, "published"}
            and not draft_course_preview_enabled()
        ):
            continue
        title = str(
            row.get("title") or row.get("name") or row.get("label") or ""
        ).strip()
        url = str(row.get("url") or row.get("href") or "").strip()
        parsed = urlsplit(url)
        if not title or parsed.scheme not in {"http", "https"} or not parsed.netloc:
            continue
        supports = (
            row.get("supports")
            or row.get("concepts")
            or row.get("topics")
            or row.get("description")
            or ""
        )
        if isinstance(supports, list):
            supports = ", ".join(str(value) for value in supports if value)
        elif not isinstance(supports, str):
            supports = str(supports) if supports else ""
        generated_slug = (
            re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-")
            or f"reference-{len(items) + 1}"
        )
        reference_slug = str(row.get("slug") or generated_slug).strip()
        related_lessons = (
            row.get("related_lesson_slugs") or row.get("related_lessons") or []
        )
        if isinstance(related_lessons, str):
            related_lessons = [related_lessons]
        if not isinstance(related_lessons, list):
            related_lessons = []
        items.append(
            {
                "slug": reference_slug,
                "title": title,
                "url": url,
                "publisher": str(
                    row.get("publisher")
                    or row.get("organization")
                    or row.get("source")
                    or ""
                ).strip(),
                "checked_on": str(
                    row.get("checked_on")
                    or index_doc.get("checked_on")
                    or index_doc.get("version_checked_on")
                    or index_doc.get("last_checked")
                    or ""
                ).strip(),
                "source_type": str(
                    row.get("source_type") or row.get("type") or "reference"
                ).strip(),
                "supports": supports,
                "explanation": str(
                    row.get("explanation") or row.get("description") or supports
                ).strip(),
                "example": str(row.get("example") or "").strip(),
                "related_lesson_slugs": [
                    str(slug).strip()
                    for slug in related_lessons
                    if isinstance(slug, str) and slug.strip()
                ],
            }
        )
    return {
        "course_slug": course.slug,
        "course_title": course.title,
        "description": course.description,
        "checked_on": index_doc.get("checked_on")
        or index_doc.get("version_checked_on")
        or index_doc.get("last_checked")
        or "",
        "items": items,
    }


@app.get("/api/courses/{course_slug}/exercises")
def list_course_exercises(
    course_slug: str,
    limit: int = 100,
    offset: int = 0,
    user: User | None = Depends(optional_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return learner-safe practice tasks for one course, without solutions or grading keys."""
    get_course_visible_to_reader(db, course_slug)
    limit = max(1, min(int(limit), 100))
    offset = max(0, int(offset))
    preview_mode = draft_course_preview_enabled()
    query = (
        select(
            Exercise,
            Lesson.slug,
            Course.title,
            Course.published,
            Lesson.is_published,
            Lesson.content,
        )
        .join(Lesson, Exercise.lesson_id == Lesson.id)
        .join(Module, Lesson.module_id == Module.id)
        .join(Course, Module.course_id == Course.id)
        .where(Course.slug == course_slug)
    )
    if not preview_mode:
        query = query.where(
            Course.published.is_(True),
            Lesson.is_published.is_(True),
            Exercise.is_published.is_(True),
        )
    rows = db.execute(
        query.order_by(
            Module.sort_order.asc(), Lesson.sort_order.asc(), Exercise.sequence.asc()
        ).limit(10_000)
    ).all()
    items: list[dict[str, Any]] = []
    current_plan_id = effective_plan_id(db, user.id) if user else "free"
    for (
        exercise,
        lesson_slug,
        course_title,
        course_is_published,
        lesson_is_published,
        lesson_content,
    ) in rows:
        published_item = bool(
            course_is_published and lesson_is_published and exercise.is_published
        )
        imported_draft = (
            preview_mode
            and isinstance(lesson_content, dict)
            and lesson_content.get("_codeleaf_course_slug") == course_slug
        )
        if not (published_item or imported_draft):
            continue
        public_type = public_practice_type(
            exercise.exercise_type, exercise.starter, course_slug, exercise.prompt
        )
        if public_type is None:
            continue
        if not can_access_exercise(current_plan_id, exercise):
            required_plan = required_exercise_plan(exercise)
            items.append({
                "slug": exercise.slug,
                "title": exercise.title,
                "type": "locked",
                "is_locked": True,
                "required_plan": required_plan,
                "upgrade_url": "/plans",
                "course_slug": course_slug,
                "course_title": course_title,
                "lesson_slug": lesson_slug,
                "sequence": exercise.sequence,
                "difficulty": exercise.difficulty,
            })
            continue
        items.append(
            {
                "slug": exercise.slug,
                "title": exercise.title,
                "type": public_type,
                "prompt": exercise.prompt,
                "difficulty": exercise.difficulty,
                "course_slug": course_slug,
                "course_title": course_title,
                "lesson_slug": lesson_slug,
                "sequence": exercise.sequence,
                "xp_points": XP_REWARDS["exercise"],
            }
        )
    total = len(items)
    return {
        "items": items[offset : offset + limit],
        "total": total,
        "offset": offset,
        "limit": limit,
        "preview_mode": preview_mode,
    }


@app.get("/api/courses/{course_slug}/outline")
def get_published_course_outline(
    course_slug: str, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Return published content, or explicitly opted-in local draft previews, without protected answer data."""
    course = get_course_visible_to_reader(db, course_slug)
    modules = db.scalars(
        select(Module)
        .where(Module.course_id == course.id)
        .order_by(Module.sort_order.asc())
    ).all()
    result_modules: list[dict[str, Any]] = []
    preview_mode = draft_course_preview_enabled()
    module_lessons: dict[Any, list[Lesson]] = {module.id: [] for module in modules}
    if modules:
        lesson_query = (
            select(Lesson)
            .join(Module, Lesson.module_id == Module.id)
            .where(Module.course_id == course.id)
            .order_by(Module.sort_order.asc(), Lesson.sort_order.asc())
        )
        if not preview_mode:
            lesson_query = lesson_query.where(Lesson.is_published.is_(True))
        for lesson in db.scalars(lesson_query).all():
            if preview_mode and not (
                lesson.is_published
                or (lesson.content or {}).get("_codeleaf_course_slug") == course_slug
            ):
                # Exclude obsolete starter-course rows left behind by the importer.
                continue
            module_lessons.setdefault(lesson.module_id, []).append(lesson)
    for module in modules:
        lessons = module_lessons.get(module.id, [])
        if not lessons:
            continue
        result_modules.append(
            {
                "id": f"{course.slug}-module-{module.sort_order:02d}",
                "slug": module.slug,
                "title": module.title,
                "sequence": module.sort_order,
                "track": module.level,
                "lessons": [
                    {
                        "id": (lesson.content or {}).get("id")
                        or f"{course.slug}-lesson-{lesson.sort_order:03d}",
                        "slug": lesson.slug,
                        "title": lesson.title,
                        "sequence": lesson.sort_order,
                        "estimated_minutes": lesson.estimated_minutes,
                        "level": (lesson.content or {}).get("level", "beginner"),
                        "track": (lesson.content or {}).get("track", "core"),
                        "keywords": (lesson.content or {}).get("keywords", []),
                    }
                    for lesson in lessons
                ],
            }
        )
    if not result_modules:
        raise HTTPException(
            status_code=404, detail="Published course lessons were not found."
        )
    return {
        "slug": course.slug,
        "title": course.title,
        "description": course.description,
        "level": course.level,
        "status": "preview" if preview_mode and not course.published else "published",
        "modules": result_modules,
        "lesson_count": sum(len(module["lessons"]) for module in result_modules),
    }


def _safe_course_json_path(course_dir: Path, relative_path: Any, label: str) -> Path:
    """Resolve a content JSON path inside one course directory."""
    if (
        not isinstance(relative_path, str)
        or not relative_path.strip()
        or "\\" in relative_path
        or "\x00" in relative_path
    ):
        raise HTTPException(status_code=404, detail=f"{label} was not found.")
    candidate = (course_dir / relative_path).resolve()
    if (
        course_dir.resolve() not in candidate.parents
        or candidate.suffix.lower() != ".json"
        or not candidate.is_file()
    ):
        raise HTTPException(status_code=404, detail=f"{label} was not found.")
    return candidate


def _load_exam_blueprint(
    course_slug: str, db: Session
) -> tuple[Course, Path, dict[str, Any]]:
    """Load a course's blueprint without exposing answer keys to the public API."""
    course = get_course_visible_to_reader(db, course_slug)
    content_root = COURSE_CONTENT_ROOT.resolve()
    course_dir = (content_root / course_slug).resolve()
    if content_root not in course_dir.parents:
        raise HTTPException(status_code=404, detail="Course content was not found.")
    manifest_path = _safe_course_json_path(course_dir, "course.json", "Course manifest")
    try:
        course_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500, detail="Course manifest is invalid."
        ) from exc

    candidates = [
        item
        for item in course_manifest.get("assessment_files", [])
        if isinstance(item, str)
        and Path(item).name.lower() in {"exam-blueprint.json", "exam-blueprint"}
    ]
    if not candidates:
        candidates = ["exams/exam-blueprint.json"]
    blueprint_path = None
    for relative in candidates:
        try:
            blueprint_path = _safe_course_json_path(
                course_dir, relative, "Exam blueprint"
            )
            break
        except HTTPException:
            continue
    if blueprint_path is None:
        raise HTTPException(
            status_code=404, detail="This course does not have a final exam blueprint."
        )
    try:
        blueprint = json.loads(blueprint_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500, detail="Exam blueprint is invalid."
        ) from exc
    if not isinstance(blueprint, dict):
        raise HTTPException(status_code=500, detail="Exam blueprint is invalid.")
    course_metadata = course_manifest.get("course")
    manifest_status = (
        course_metadata.get("status")
        if isinstance(course_metadata, dict) and course_metadata.get("status")
        else course_manifest.get("status")
    )
    # Current course manifests publish through course.status. Some older manifests
    # still carry a stale top-level status="draft"; prefer the nested authoritative
    # field when it exists, otherwise preserve the legacy top-level behavior.
    if manifest_status == "draft" and not draft_course_preview_enabled():
        raise HTTPException(
            status_code=404, detail="This course has not been published."
        )
    if blueprint.get("status") != "published" and not draft_course_preview_enabled():
        raise HTTPException(
            status_code=404, detail="This final exam has not been published."
        )
    return course, course_dir, blueprint


def _exam_question_file_refs(blueprint: dict[str, Any]) -> list[str]:
    """Return the authored question-bank index, supporting the legacy source-pool key."""
    question_files = blueprint.get("question_files")
    if isinstance(question_files, list) and question_files:
        return question_files
    source_pool_files = blueprint.get("source_question_pool_files")
    if isinstance(source_pool_files, list):
        return source_pool_files
    if isinstance(question_files, list):
        return question_files
    raise HTTPException(status_code=500, detail="Exam question index is invalid.")


def _exam_question_rows(question_set: dict[str, Any]) -> list[dict[str, Any]]:
    """Support both question-set files and legacy files containing one question."""
    rows = question_set.get("questions")
    if isinstance(rows, list):
        return rows
    if (
        isinstance(question_set.get("options"), list)
        and isinstance(question_set.get("prompt") or question_set.get("question"), str)
    ):
        return [question_set]
    raise HTTPException(status_code=500, detail="An exam question set is malformed.")


def _normalize_exam_answer_key(options: list[str], answer_key: Any) -> str | None:
    """Resolve either an option's literal text or a conventional A/B/C/D key."""
    if not isinstance(answer_key, str):
        return None
    if answer_key in options:
        return answer_key
    letter = answer_key.strip().upper()
    if len(letter) == 1 and "A" <= letter <= "Z":
        option_index = ord(letter) - ord("A")
        if 0 <= option_index < len(options):
            return options[option_index]
    return None


def _exam_lesson_number(
    question_set_lesson_id: Any,
    question_lesson_id: Any,
    question_path: Path,
    fallback_number: int,
) -> int:
    """Get a real lesson number when present, otherwise assign a stable pool slot.

    Single-file final exams often contain topic/module labels rather than a lesson ID.
    They still need distinct positive sampling slots so the shared exam engine can draw
    from their bank instead of incorrectly treating every item as lesson zero.
    """
    for value in (question_lesson_id, question_set_lesson_id):
        if not isinstance(value, (str, int)) or not str(value).strip():
            continue
        text = str(value)
        match = re.search(r"lesson[-_ ]?(\d+)", text, re.IGNORECASE)
        if match:
            return max(1, int(match.group(1)))
        match = re.search(r"(\d+)$", text)
        if match:
            return max(1, int(match.group(1)))
    match = re.search(r"lesson[-_ ]?(\d+)", question_path.stem, re.IGNORECASE)
    if match:
        return max(1, int(match.group(1)))
    # Keep synthetic IDs away from authored lesson ranges and avoid collisions between
    # question IDs such as q001 reused in separate final-exam parts.
    return 1_000_000 + max(1, fallback_number)


def _load_exam_question_pool(
    course_dir: Path, blueprint: dict[str, Any]
) -> list[dict[str, Any]]:
    """Load valid published questions. Private answer keys remain server-only."""
    question_files = _exam_question_file_refs(blueprint)
    preview = draft_course_preview_enabled()
    pool: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    topic_ranges: list[tuple[str, int, int]] = []
    topic_distribution = blueprint.get("topic_distribution", [])
    for topic in topic_distribution if isinstance(topic_distribution, list) else []:
        if not isinstance(topic, dict):
            continue
        lesson_range = topic.get("lesson_range")
        if not isinstance(lesson_range, list) or len(lesson_range) != 2:
            continue
        try:
            start, end = int(lesson_range[0]), int(lesson_range[1])
        except (TypeError, ValueError):
            continue
        if start <= end:
            topic_ranges.append(
                (str(topic.get("topic") or "General skills"), start, end)
            )

    for relative in question_files:
        if not isinstance(relative, str) or not relative.strip() or "\\" in relative:
            raise HTTPException(status_code=500, detail="The exam question index contains an invalid file reference.")
        relative_path = relative if relative.startswith("exams/") else f"exams/{relative}"
        try:
            question_path = _safe_course_json_path(
                course_dir, relative_path, "Exam question set"
            )
        except HTTPException as exc:
            raise HTTPException(status_code=500, detail="A referenced exam question file is missing or invalid.") from exc
        try:
            question_set = json.loads(question_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise HTTPException(
                status_code=500, detail="An exam question set is invalid."
            ) from exc
        if not isinstance(question_set, dict):
            raise HTTPException(
                status_code=500, detail="An exam question set is invalid."
            )
        if question_set.get("status") != "published" and not preview:
            continue
        questions = _exam_question_rows(question_set)
        if not questions:
            raise HTTPException(
                status_code=500, detail="An exam question set is empty."
            )
        lesson_id = question_set.get("lesson_id")
        lesson_slug = question_set.get("lesson_slug")
        for question in questions:
            if not isinstance(question, dict):
                raise HTTPException(
                    status_code=500, detail="An exam question is malformed."
                )
            question_id = question.get("id")
            prompt = question.get("prompt") or question.get("question")
            options = question.get("options")
            if (
                not isinstance(question_id, str)
                or not question_id.strip()
                or not isinstance(prompt, str)
                or not prompt.strip()
                or not isinstance(options, list)
                or len(options) != 4
                or not all(isinstance(option, str) and option.strip() for option in options)
                or len({option.strip() for option in options}) != len(options)
            ):
                # Malformed items are not selectable. The readiness audit reports
                # them separately; a large valid bank can still remain usable.
                continue
            if question_id in seen_ids:
                raise HTTPException(
                    status_code=500,
                    detail="Exam question IDs must be unique across the complete question bank.",
                )
            answer_key = _normalize_exam_answer_key(options, question.get("answer_key"))
            if answer_key is None:
                continue
            seen_ids.add(question_id)
            lesson_number = _exam_lesson_number(
                lesson_id,
                question.get("lesson_id"),
                question_path,
                len(pool) + 1,
            )
            topic_name = str(
                question.get("topic")
                or question_set.get("topic")
                or question_set.get("domain")
                or next(
                    (
                        name
                        for name, start, end in topic_ranges
                        if start <= lesson_number <= end
                    ),
                    "General skills",
                )
            )
            pool.append(
                {
                    "id": question_id,
                    "lesson_id": str(question.get("lesson_id") or lesson_id or ""),
                    "lesson_slug": str(question.get("lesson_slug") or lesson_slug or ""),
                    "lesson_number": lesson_number,
                    "topic": topic_name,
                    "prompt": prompt,
                    "options": options,
                    "answer_key": answer_key,
                    "explanation": str(
                        question.get("explanation")
                        or "Review the relevant lesson and try again."
                    ),
                }
            )
    return pool


def _normalized_exam_prompt(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def _unique_exam_questions(pool: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove exact duplicate prompts from selection without mutating authored files."""
    unique: list[dict[str, Any]] = []
    seen_prompts: set[str] = set()
    for item in pool:
        prompt_key = _normalized_exam_prompt(item.get("prompt"))
        if not prompt_key or prompt_key in seen_prompts:
            continue
        seen_prompts.add(prompt_key)
        unique.append(item)
    return unique


def _exam_bank_readiness_from_pool(pool: list[dict[str, Any]], error: str | None = None) -> dict[str, Any]:
    selectable = _unique_exam_questions(pool)
    return {
        "valid_question_count": len(pool),
        "distinct_prompt_count": len(selectable),
        "required_question_count": 80,
        "available_question_count": min(80, len(selectable)),
        "ready": len(selectable) >= 80 and error is None,
        "error": error,
    }


def _exam_bank_readiness(course_dir: Path, blueprint: dict[str, Any]) -> dict[str, Any]:
    """Validate the selectable bank and report the minimum 80 distinct-question gate."""
    try:
        pool = _load_exam_question_pool(course_dir, blueprint)
        error = None
    except HTTPException as exc:
        pool = []
        error = str(exc.detail or "The exam question bank is invalid.")
    return _exam_bank_readiness_from_pool(pool, error)


def _has_published_exam_question_set(
    course_dir: Path, blueprint: dict[str, Any]
) -> bool:
    """Return true only when the bank can supply 80 valid, distinct prompts."""
    return bool(_exam_bank_readiness(course_dir, blueprint)["ready"])


@app.get("/api/exams/catalog")
def list_exam_catalog(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return live exam readiness for roadmap tracks without exposing question data."""
    items: list[dict[str, Any]] = []
    for track in PUBLIC_COURSES:
        slug = str(track.get("slug") or "").strip()
        if not slug:
            continue
        entry: dict[str, Any] = {
            "slug": slug,
            "title": str(track.get("title") or slug.title()),
            "available": False,
            "status": "roadmap",
            "message": "The course has not been published to the learner catalog yet.",
        }
        try:
            course, course_dir, blueprint = _load_exam_blueprint(slug, db)
            entry["title"] = course.title
            readiness = _exam_bank_readiness(course_dir, blueprint)
            entry.update({
                "valid_question_count": readiness["valid_question_count"],
                "distinct_question_count": readiness["distinct_prompt_count"],
                "required_question_count": 80,
                "question_count": 80 if readiness["ready"] else 0,
            })
            # Report practical publication independently from MCQ-bank readiness so
            # a learner can distinguish a missing practical from an undersized MCQ bank.
            practical_ready = False
            practical_message = "The practical certification assessment has not been published yet."
            try:
                _load_practical_exam(course_dir)
                practical_ready = True
                practical_message = "The practical assessment is published."
            except HTTPException as practical_error:
                practical_detail = practical_error.detail
                practical_message = (
                    str(practical_detail.get("message") or practical_message)
                    if isinstance(practical_detail, dict)
                    else str(practical_detail or practical_message)
                )
            entry["practical_available"] = practical_ready
            entry["practical_message"] = practical_message
            if readiness["ready"] and practical_ready:
                settings_doc = blueprint.get("recommended_settings") or {}
                is_preview = draft_course_preview_enabled() and (
                    not course.published or blueprint.get("status") != "published"
                )
                entry.update(
                    {
                        "available": True,
                        "status": "preview" if is_preview else "published",
                        "title": str(
                            blueprint.get("title")
                            or f"{course.title} Skills Assessment"
                        ),
                        "duration_minutes": int(
                            settings_doc.get("duration_minutes") or 60
                        ),
                        "pass_percent": int(
                            settings_doc.get("suggested_pass_percent") or 70
                        ),
                        "message": (
                            "The draft 80-question MCQ stage is available in local preview only."
                            if is_preview
                            else "The published 80-question MCQ stage and question bank are available."
                        ),
                    }
                )
            elif not readiness["ready"]:
                entry.update(
                    {
                        "status": "question_bank_incomplete",
                        "message": (
                            f"The MCQ stage is unavailable: it needs 80 valid, distinct questions; "
                            f"the bank currently has {readiness['distinct_prompt_count']} distinct prompts."
                            + (" The practical assessment is published." if practical_ready else f" {practical_message}")
                        ),
                    }
                )
            else:
                entry.update(
                    {
                        "status": "practical_exam_unavailable",
                        "message": (
                            "The MCQ bank is ready, but the certification track remains unavailable "
                            f"until its practical assessment is published. {practical_message}"
                        ),
                    }
                )
        except HTTPException as exc:
            detail = str(exc.detail or "")
            if exc.status_code == 500:
                entry.update(
                    {
                        "status": "configuration_error",
                        "message": "The exam configuration needs attention before it can be opened.",
                    }
                )
            elif "not published" in detail.lower() or "blueprint" in detail.lower():
                entry.update(
                    {
                        "status": "publication_required",
                        "message": "A published course blueprint and question bank are required.",
                    }
                )
        items.append(entry)
    return {"items": items}


def _choose_exam_questions(
    pool: list[dict[str, Any]], blueprint: dict[str, Any], count: int = 80
) -> list[dict[str, Any]]:
    """Sample distinct prompts with topic coverage, never reusing a question concept."""
    rng = secrets.SystemRandom()
    candidates = _unique_exam_questions(pool)
    if not candidates:
        return []
    target_count = min(max(1, int(count)), len(candidates))
    topics: list[tuple[str, int, int, float]] = []
    for row in blueprint.get("topic_distribution", []):
        if not isinstance(row, dict):
            continue
        lesson_range = row.get("lesson_range")
        try:
            start, end = int(lesson_range[0]), int(lesson_range[1])
            weight = max(0.0, float(row.get("weight_percent", 0)))
        except (TypeError, ValueError, IndexError):
            continue
        if start <= end and weight > 0:
            topics.append((str(row.get("topic") or "General skills"), start, end, weight))

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    total_weight = sum(item[3] for item in topics)
    if topics and total_weight > 0:
        raw = [target_count * item[3] / total_weight for item in topics]
        quotas = [int(value) for value in raw]
        remainder = target_count - sum(quotas)
        for idx in sorted(range(len(topics)), key=lambda i: raw[i] - quotas[i], reverse=True)[:remainder]:
            quotas[idx] += 1
        for (topic_name, start, end, _weight), quota in zip(topics, quotas):
            matching = [
                item for item in candidates
                if item["id"] not in selected_ids
                and start <= int(item.get("lesson_number") or 0) <= end
            ]
            rng.shuffle(matching)
            for item in matching[:quota]:
                copy = dict(item)
                copy["topic"] = topic_name
                selected.append(copy)
                selected_ids.add(str(copy["id"]))

    if len(selected) < target_count:
        remaining = [item for item in candidates if item["id"] not in selected_ids]
        rng.shuffle(remaining)
        selected.extend(dict(item) for item in remaining[:target_count - len(selected)])
    rng.shuffle(selected)
    return selected


def _course_progress_requirements(
    db: Session, user: User, course: Course
) -> dict[str, Any]:
    """Calculate prerequisites exclusively from published database content and persisted progress."""
    lesson_rows = db.execute(
        select(Lesson.id, LessonProgress.completed)
        .join(Module, Lesson.module_id == Module.id)
        .outerjoin(
            LessonProgress,
            (LessonProgress.lesson_id == Lesson.id)
            & (LessonProgress.user_id == user.id),
        )
        .where(
            Module.course_id == course.id,
            Lesson.is_published.is_(True),
        )
        .order_by(Module.sort_order.asc(), Lesson.sort_order.asc())
    ).all()
    total_lessons = len(lesson_rows)
    completed_lessons = sum(1 for _lesson_id, completed in lesson_rows if completed)

    exercise_records = db.execute(
        select(Exercise, ExerciseProgress.completed)
        .join(Lesson, Exercise.lesson_id == Lesson.id)
        .join(Module, Lesson.module_id == Module.id)
        .outerjoin(
            ExerciseProgress,
            (ExerciseProgress.exercise_id == Exercise.id)
            & (ExerciseProgress.user_id == user.id),
        )
        .where(
            Module.course_id == course.id,
            Lesson.is_published.is_(True),
            Exercise.is_published.is_(True),
        )
        .order_by(Module.sort_order.asc(), Lesson.sort_order.asc(), Exercise.sequence.asc())
    ).all()
    # Match the exact Practice task set shown to learners. Hidden short-answer and
    # ungraded review prompts must not remain a secret certification prerequisite.
    exercise_rows = [
        (exercise.id, completed)
        for exercise, completed in exercise_records
        if is_supported_practice_exercise(
            exercise.exercise_type, exercise.starter, course.slug, exercise.prompt
        )
    ]
    total_exercises = len(exercise_rows)
    completed_exercises = sum(1 for _exercise_id, completed in exercise_rows if completed)

    missing_lessons = max(0, total_lessons - completed_lessons)
    missing_exercises = max(0, total_exercises - completed_exercises)
    return {
        "total_lessons": total_lessons,
        "completed_lessons": completed_lessons,
        "missing_lessons": missing_lessons,
        "lessons_complete": total_lessons > 0 and missing_lessons == 0,
        "total_exercises": total_exercises,
        "completed_exercises": completed_exercises,
        "missing_exercises": missing_exercises,
        "exercises_complete": missing_exercises == 0,
        "prerequisites_complete": total_lessons > 0 and missing_lessons == 0 and missing_exercises == 0,
    }


def _require_course_prerequisites(db: Session, user: User, course: Course) -> dict[str, Any]:
    progress = _course_progress_requirements(db, user, course)
    if not progress["prerequisites_complete"]:
        missing = {}
        if not progress["lessons_complete"]:
            missing["lessons"] = {
                "completed": progress["completed_lessons"],
                "total": progress["total_lessons"],
                "remaining": progress["missing_lessons"],
            }
        if not progress["exercises_complete"]:
            missing["exercises"] = {
                "completed": progress["completed_exercises"],
                "total": progress["total_exercises"],
                "remaining": progress["missing_exercises"],
            }
        raise HTTPException(
            status_code=409,
            detail={
                "code": "exam_prerequisites_incomplete",
                "message": "Complete every required published lesson and exercise before starting the certification exam.",
                "missing_requirements": missing,
            },
        )
    return progress


def _load_practical_exam(course_dir: Path) -> dict[str, Any]:
    """Load only published, author-defined, deterministic practical assessments.

    Code-execution tasks are deliberately not accepted by this evaluator; those need
    the isolated runner's dedicated hidden-test contract, which this repository does
    not currently expose. No learner code is ever executed in the API process.
    """
    practical_path = (course_dir / "exams" / "practical-exam.json").resolve()
    resolved_dir = course_dir.resolve()
    if resolved_dir not in practical_path.parents or not practical_path.is_file():
        raise HTTPException(
            status_code=404,
            detail={
                "code": "practical_exam_unavailable",
                "message": "A published practical assessment has not been authored for this course yet.",
            },
        )
    try:
        practical = json.loads(practical_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="The practical assessment configuration is invalid.") from exc
    if not isinstance(practical, dict) or practical.get("status") != "published":
        raise HTTPException(
            status_code=404,
            detail={
                "code": "practical_exam_unavailable",
                "message": "The practical assessment is not published.",
            },
        )

    # Assessment files are publication-controlled by the course manifest.
    try:
        manifest = json.loads((resolved_dir / "course.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="The course manifest is invalid.") from exc
    assessment_files = manifest.get("assessment_files", []) if isinstance(manifest, dict) else []
    if "exams/practical-exam.json" not in assessment_files:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "practical_exam_unavailable",
                "message": "The practical assessment is not registered in the published course manifest.",
            },
        )

    difficulty = str(practical.get("difficulty") or "intermediate").strip().lower()
    if difficulty != "intermediate":
        raise HTTPException(status_code=409, detail="The published practical exam must be configured at intermediate difficulty.")
    try:
        pass_percent = int(practical.get("pass_percent") or 70)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=500, detail="The practical exam passing threshold is invalid.") from exc
    if not 1 <= pass_percent <= 100:
        raise HTTPException(status_code=500, detail="The practical exam passing threshold is invalid.")

    tasks = practical.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise HTTPException(status_code=409, detail="The practical assessment contains no tasks.")
    seen_ids: set[str] = set()
    for task in tasks:
        if not isinstance(task, dict):
            raise HTTPException(status_code=500, detail="A practical assessment task is malformed.")
        task_id = task.get("id")
        grader = task.get("grader")
        submission_type = task.get("submission_type", "text")
        if (
            not isinstance(task_id, str) or not task_id.strip() or task_id in seen_ids
            or not isinstance(task.get("prompt"), str) or not task["prompt"].strip()
            or submission_type != "text"
            or not isinstance(grader, dict)
            or grader.get("type") not in {"exact_text", "contains_all", "json_equal"}
        ):
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "practical_exam_not_ready",
                    "message": "The practical assessment has a task without a supported deterministic grader. Code execution must use the isolated runner and cannot run inside the API process.",
                },
            )
        points = task.get("points", 100)
        if not isinstance(points, int) or points < 1 or points > 1000:
            raise HTTPException(status_code=500, detail="A practical task has an invalid score weight.")
        if grader["type"] == "exact_text" and not isinstance(grader.get("expected"), (str, list)):
            raise HTTPException(status_code=500, detail="A practical exact-text grader is missing its expected answer.")
        if grader["type"] == "contains_all" and not isinstance(grader.get("required_strings"), list):
            raise HTTPException(status_code=500, detail="A practical contains-all grader is malformed.")
        if grader["type"] == "json_equal" and "expected" not in grader:
            raise HTTPException(status_code=500, detail="A practical JSON grader is missing its expected value.")
        seen_ids.add(task_id)

    return practical


def _practical_task_public(task: dict[str, Any]) -> dict[str, Any]:
    """Redact grader configuration, expected answers, hidden tests, and solutions."""
    return {
        "id": task["id"],
        "title": str(task.get("title") or "Practical task"),
        "prompt": task["prompt"],
        "submission_type": task.get("submission_type", "text"),
        "starter": str(task.get("starter") or ""),
        "rubric": [
            str(item) for item in task.get("rubric", [])
            if isinstance(item, str) and item.strip()
        ] if isinstance(task.get("rubric", []), list) else [],
        "points": int(task.get("points", 100)),
    }


def _latest_passed_mcq_attempt(db: Session, user: User, course: Course) -> ExamAttempt | None:
    return db.scalar(
        select(ExamAttempt)
        .where(
            ExamAttempt.user_id == user.id,
            ExamAttempt.course_id == course.id,
            ExamAttempt.submitted_at.is_not(None),
            ExamAttempt.passed.is_(True),
        )
        .order_by(ExamAttempt.submitted_at.desc())
        .limit(1)
    )


def _practical_attempt_for_mcq(
    db: Session, user: User, course: Course, attempt: ExamAttempt | None
) -> PracticalExamAttempt | None:
    if attempt is None:
        return None
    return db.scalar(
        select(PracticalExamAttempt)
        .where(
            PracticalExamAttempt.user_id == user.id,
            PracticalExamAttempt.course_id == course.id,
            PracticalExamAttempt.mcq_attempt_id == attempt.id,
            PracticalExamAttempt.submitted_at.is_not(None),
        )
        .order_by(PracticalExamAttempt.submitted_at.desc())
        .limit(1)
    )


def _certificate_eligibility_payload(
    db: Session,
    user: User,
    course: Course,
    blueprint: dict[str, Any],
    attempt: ExamAttempt | None,
    issue_if_eligible: bool = False,
) -> dict[str, Any]:
    progress = _course_progress_requirements(db, user, course)
    certificate = db.scalar(
        select(Certificate)
        .where(
            Certificate.user_id == user.id,
            Certificate.course_id == course.id,
            Certificate.revoked_at.is_(None),
        )
        .order_by(Certificate.issued_at.desc())
        .limit(1)
    )
    attempt_passed = bool(attempt and attempt.submitted_at and attempt.passed)
    practical_available = False
    practical_unavailable_reason = "A published practical assessment has not been authored for this course yet."
    try:
        _load_practical_exam(COURSE_CONTENT_ROOT / course.slug)
        practical_available = True
        practical_unavailable_reason = ""
    except HTTPException as exc:
        detail = exc.detail
        practical_unavailable_reason = (
            str(detail.get("message") or "The practical assessment is not ready.")
            if isinstance(detail, dict)
            else str(detail or "The practical assessment is not ready.")
        )
    practical_attempt = _practical_attempt_for_mcq(db, user, course, attempt if attempt_passed else None)
    practical_passed = bool(practical_attempt and practical_attempt.passed)

    status_text = "exam_required"
    reason = "Pass the server-graded MCQ exam first."
    if certificate:
        status_text, reason = (
            "issued",
            "A verified certificate has been issued for this course.",
        )
    elif not attempt_passed:
        if attempt and attempt.submitted_at:
            status_text, reason = (
                "exam_not_passed",
                "Review the result and pass the MCQ exam to continue.",
            )
    elif not progress["lessons_complete"]:
        status_text, reason = (
            "pending_lessons",
            "Complete every required published lesson before certification.",
        )
    elif not progress["exercises_complete"]:
        status_text, reason = (
            "pending_exercises",
            "Complete every required published exercise before certification.",
        )
    elif not practical_available:
        status_text, reason = (
            "practical_exam_unavailable",
            practical_unavailable_reason,
        )
    elif not practical_passed:
        status_text, reason = (
            "practical_exam_not_passed" if practical_attempt else "practical_exam_required",
            "Pass the practical examination before a certificate can be issued.",
        )
    else:
        status_text, reason = (
            "eligible",
            "The backend verified required lessons, exercises, MCQ and practical passing results.",
        )
        if issue_if_eligible:
            # Reuse an existing active certificate rather than issuing duplicates.
            certificate = Certificate(
                public_id=secrets.token_hex(8).upper(),
                user_id=user.id,
                course_id=course.id,
                exam_attempt_id=attempt.id if attempt else None,
            )
            db.add(certificate)
            db.flush()
            status_text, reason = (
                "issued",
                "A certificate was issued after backend verification of both exam stages.",
            )
    return {
        "course_slug": course.slug,
        "course_title": course.title,
        "status": status_text,
        "eligible": status_text in {"eligible", "issued"},
        "exam_passed": attempt_passed,
        "practical_exam_available": practical_available,
        "practical_exam_passed": practical_passed,
        "score_percent": (
            (attempt.answers_summary or {}).get("score_percent") if attempt else None
        ),
        **progress,
        "project_review_required": False,
        "message": reason,
        "certificate": (
            {
                "public_id": certificate.public_id,
                "issued_at": certificate.issued_at.isoformat(),
            }
            if certificate
            else None
        ),
    }


def _mock_public_questions(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {key: question[key] for key in ("id", "lesson_slug", "topic", "prompt", "options") if key in question}
        for question in questions if isinstance(question, dict)
    ]


def _mock_attempt_payload(attempt: MockAssessmentAttempt, *, include_report: bool = False) -> dict[str, Any]:
    summary = attempt.answers_summary or {}
    started_at = attempt.started_at
    if started_at is not None and started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    out = {
        "attempt_id": str(attempt.id),
        "status": "submitted" if attempt.submitted_at else "in_progress",
        "course_slug": summary.get("course_slug", ""),
        "title": summary.get("title", "Timed mock assessment"),
        "duration_minutes": int(summary.get("duration_minutes") or 20),
        "question_count": int(summary.get("question_count") or 20),
        "expires_at": (started_at + timedelta(minutes=int(summary.get("duration_minutes") or 20))).isoformat() if started_at else None,
        "started_at": started_at.isoformat() if started_at else None,
        "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
        "score_percent": int(attempt.score) if attempt.submitted_at else None,
        "passed": bool(attempt.passed) if attempt.submitted_at else None,
    }
    if attempt.submitted_at:
        if include_report:
            out["report"] = summary.get("report", {})
            out["message"] = "Mock assessment submitted. This practice result does not issue a certificate or award XP."
        return out
    out["questions"] = _mock_public_questions(summary.get("questions", []))
    return out


@app.get("/api/courses/{course_slug}/mock-exam")
def get_course_mock_exam_info(
    course_slug: str,
    user: User | None = Depends(optional_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Expose mock-exam availability without exposing question keys or bypassing tier checks."""
    course, course_dir, blueprint = _load_exam_blueprint(course_slug, db)
    pool = _unique_exam_questions(_load_exam_question_pool(course_dir, blueprint))
    required_count = 20
    if len(pool) < required_count:
        return {
            "available": False, "course_slug": course.slug, "course_title": course.title,
            "title": f"{course.title} Timed Mock Assessment", "question_count": required_count,
            "available_question_count": len(pool), "duration_minutes": 20,
            "required_plan": "pro", "upgrade_url": "/plans",
            "message": f"This mock assessment needs at least {required_count} distinct published questions; {len(pool)} are currently available.",
        }
    plan_id = effective_plan_id(db, user.id) if user else "free"
    entitled = bool(plan_features(plan_id).get("premium_practice"))
    return {
        "available": True, "can_start": bool(user and entitled),
        "course_slug": course.slug, "course_title": course.title,
        "title": f"{course.title} Timed Mock Assessment", "question_count": required_count,
        "available_question_count": len(pool), "duration_minutes": 20,
        "pass_percent": int((blueprint.get("recommended_settings") or {}).get("suggested_pass_percent") or 70),
        "current_plan": plan_id, "required_plan": "pro", "upgrade_url": "/plans",
        "message": "20 distinct questions in 20 minutes. Results include topic-level feedback and do not affect certificates or XP.",
    }


@app.post("/api/courses/{course_slug}/mock-exam/start", status_code=status.HTTP_201_CREATED)
def start_course_mock_exam(
    course_slug: str,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Start a Pro+ timed mock from the published course bank, separate from certification."""
    require_feature(db, user, "premium_practice")
    course, course_dir, blueprint = _load_exam_blueprint(course_slug, db)
    pool = _unique_exam_questions(_load_exam_question_pool(course_dir, blueprint))
    question_count = 20
    if len(pool) < question_count:
        raise HTTPException(status_code=409, detail={
            "code": "MOCK_ASSESSMENT_UNAVAILABLE", "available_question_count": len(pool),
            "required_question_count": question_count,
            "message": f"This mock assessment needs {question_count} distinct published questions; {len(pool)} are currently available.",
        })
    picked = secrets.SystemRandom().sample(pool, question_count)
    stored_questions = []
    for item in picked:
        options = list(item["options"])
        secrets.SystemRandom().shuffle(options)
        stored_questions.append({key: item[key] for key in ("id", "lesson_id", "lesson_slug", "lesson_number", "topic", "prompt", "answer_key", "explanation")} | {"options": options})
    recommended = blueprint.get("recommended_settings") or {}
    pass_percent = int(recommended.get("suggested_pass_percent") or 70)
    attempt = MockAssessmentAttempt(
        user_id=user.id, course_id=course.id, score=0, passed=False,
        answers_summary={
            "status": "in_progress", "course_slug": course_slug,
            "title": f"{course.title} Timed Mock Assessment", "question_count": question_count,
            "duration_minutes": 20, "pass_percent": pass_percent,
            "questions": stored_questions,
        },
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return {
        **_mock_attempt_payload(attempt),
        "pass_percent": pass_percent,
        "questions": _mock_public_questions(stored_questions),
    }


@app.get("/api/me/mock-exams/{attempt_id}")
def get_my_mock_exam_attempt(
    attempt_id: str, user: User = Depends(require_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    try:
        parsed_id = UUID(attempt_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=404, detail="Mock assessment attempt was not found.")
    attempt = db.scalar(select(MockAssessmentAttempt).where(MockAssessmentAttempt.id == parsed_id, MockAssessmentAttempt.user_id == user.id))
    if attempt is None:
        raise HTTPException(status_code=404, detail="Mock assessment attempt was not found.")
    return _mock_attempt_payload(attempt, include_report=True)


@app.post("/api/me/mock-exams/{attempt_id}/submit")
def submit_my_mock_exam_attempt(
    attempt_id: str,
    payload: dict[str, Any],
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        parsed_id = UUID(attempt_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=404, detail="Mock assessment attempt was not found.")
    attempt = db.scalar(select(MockAssessmentAttempt).where(MockAssessmentAttempt.id == parsed_id, MockAssessmentAttempt.user_id == user.id).with_for_update())
    if attempt is None:
        raise HTTPException(status_code=404, detail="Mock assessment attempt was not found.")
    if attempt.submitted_at:
        raise HTTPException(status_code=409, detail="This mock assessment attempt has already been submitted.")
    # Copy the top-level JSON object before replacing it. SQLAlchemy JSON does not
    # reliably track in-place nested mutations, which could persist the score but
    # lose the detailed report returned after submission.
    summary = dict(attempt.answers_summary or {})
    questions = summary.get("questions") if isinstance(summary.get("questions"), list) else []
    answers = payload.get("answers") if isinstance(payload, dict) else None
    if not isinstance(answers, dict):
        raise HTTPException(status_code=422, detail="Submit an answers object for the mock assessment.")
    by_id = {str(question.get("id")): question for question in questions if isinstance(question, dict)}
    if not set(answers.keys()).issubset(set(by_id.keys())):
        raise HTTPException(status_code=422, detail="The submission contains an unknown mock question.")
    for question_id, value in answers.items():
        if not isinstance(value, str) or value not in by_id[question_id].get("options", []):
            raise HTTPException(status_code=422, detail="Each selected answer must match an option in that question.")
    started = attempt.started_at if attempt.started_at.tzinfo else attempt.started_at.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    duration_seconds = int(summary.get("duration_minutes") or 20) * 60
    expired = (now - started).total_seconds() > duration_seconds + 5
    results = []
    correct_count = 0
    topics: dict[str, dict[str, int]] = {}
    for question in questions:
        qid = str(question.get("id"))
        selected = None if expired else answers.get(qid)
        correct = bool(selected is not None and selected == question.get("answer_key"))
        correct_count += int(correct)
        topic = str(question.get("topic") or "General skills")
        item = topics.setdefault(topic, {"correct": 0, "total": 0})
        item["correct"] += int(correct)
        item["total"] += 1
        results.append({
            "question_id": qid, "prompt": question.get("prompt", ""), "topic": topic,
            "lesson_slug": question.get("lesson_slug", ""), "selected_answer": selected or "",
            "correct_answer": question.get("answer_key", ""), "is_correct": correct,
            "explanation": question.get("explanation", "Review the related published lesson and try again."),
        })
    score = round(correct_count / max(1, len(questions)) * 100)
    pass_percent = int(summary.get("pass_percent") or 70)
    summary["status"] = "submitted"
    summary["timed_out"] = expired
    summary["report"] = {
        "score_percent": score, "correct_count": correct_count, "question_count": len(questions),
        "pass_percent": pass_percent, "passed": score >= pass_percent,
        "timed_out": expired,
        "topic_performance": [{"topic": name, "correct": values["correct"], "total": values["total"], "percent": round(values["correct"] / max(1, values["total"]) * 100)} for name, values in sorted(topics.items())],
        "results": results,
        "notice": "This is a practice assessment only. It does not issue or change certificates and does not award XP.",
    }
    attempt.score = score
    attempt.passed = score >= pass_percent
    attempt.answers_summary = summary
    attempt.submitted_at = now
    db.commit()
    db.refresh(attempt)
    return _mock_attempt_payload(attempt, include_report=True)


@app.get("/api/courses/{course_slug}/exam")
def get_course_exam_info(
    course_slug: str, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Return safe metadata only when the bank can supply 80 distinct, valid MCQs."""
    _course, course_dir, blueprint = _load_exam_blueprint(course_slug, db)
    readiness = _exam_bank_readiness(course_dir, blueprint)
    if not readiness["ready"]:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "exam_content_not_ready",
                "message": (
                    f"This MCQ exam needs 80 valid, distinct questions. "
                    f"The current bank has {readiness['distinct_prompt_count']} distinct prompts."
                ),
                **readiness,
            },
        )
    try:
        _load_practical_exam(course_dir)
    except HTTPException as exc:
        detail = exc.detail
        message = (
            str(detail.get("message") or "The mandatory practical exam is unavailable.")
            if isinstance(detail, dict)
            else str(detail or "The mandatory practical exam is unavailable.")
        )
        raise HTTPException(
            status_code=409,
            detail={
                "code": "practical_exam_unavailable",
                "message": f"The certification exam cannot start until its mandatory practical stage is published. {message}",
            },
        ) from exc
    settings_doc = blueprint.get("recommended_settings") or {}
    practical_ready = True
    return {
        "course_slug": course_slug,
        "title": str(
            blueprint.get("title") or f"{course_slug.title()} Skills Assessment"
        ),
        "duration_minutes": int(settings_doc.get("duration_minutes") or 60),
        "pass_percent": int(settings_doc.get("suggested_pass_percent") or 70),
        "question_count": 80,
        "question_bank_count": readiness["valid_question_count"],
        "distinct_question_count": readiness["distinct_prompt_count"],
        "required_question_count": 80,
        "practical_exam_available": practical_ready,
        "practical_exam_message": (
            "A published practical assessment is available after passing the MCQ stage."
            if practical_ready
            else "The practical certification stage has not been published for this course yet; passing the MCQ alone cannot issue a certificate."
        ),
        "status": (
            "preview"
            if draft_course_preview_enabled() and blueprint.get("status") != "published"
            else "published"
        ),
    }


@app.post("/api/courses/{course_slug}/exam/start", status_code=status.HTTP_201_CREATED)
def start_course_exam(
    course_slug: str, user: User = Depends(require_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Create a private 80-question attempt after server-verified prerequisites."""
    course, course_dir, blueprint = _load_exam_blueprint(course_slug, db)
    progress = _require_course_prerequisites(db, user, course)
    pool = _load_exam_question_pool(course_dir, blueprint)
    readiness = _exam_bank_readiness_from_pool(pool)
    if not readiness["ready"]:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "exam_content_not_ready",
                "message": (
                    f"This MCQ exam needs 80 valid, distinct questions. "
                    f"The current bank has {readiness['distinct_prompt_count']} distinct prompts."
                ),
                **readiness,
            },
        )
    try:
        _load_practical_exam(course_dir)
    except HTTPException as exc:
        detail = exc.detail
        message = (
            str(detail.get("message") or "The mandatory practical exam is unavailable.")
            if isinstance(detail, dict)
            else str(detail or "The mandatory practical exam is unavailable.")
        )
        raise HTTPException(
            status_code=409,
            detail={"code": "practical_exam_unavailable",
                    "message": f"The certification exam cannot start until its mandatory practical stage is published. {message}"},
        ) from exc
    picked = _choose_exam_questions(pool, blueprint, count=80)
    if len(picked) != 80 or len({q["id"] for q in picked}) != 80:
        raise HTTPException(status_code=409, detail="The question bank could not supply 80 distinct exam questions.")
    recommended = blueprint.get("recommended_settings") or {}
    stored_questions = []
    rng = secrets.SystemRandom()
    for item in picked:
        options = list(item["options"])
        rng.shuffle(options)
        stored_questions.append(
            {
                key: item[key]
                for key in (
                    "id",
                    "lesson_id",
                    "lesson_slug",
                    "lesson_number",
                    "topic",
                    "prompt",
                    "answer_key",
                    "explanation",
                )
            }
            | {"options": options}
        )
    attempt = ExamAttempt(
        user_id=user.id,
        course_id=course.id,
        score=0,
        passed=False,
        answers_summary={
            "status": "in_progress",
            "course_slug": course_slug,
            "exam_title": str(
                blueprint.get("title") or f"{course_slug.title()} Skills Assessment"
            ),
            "pass_percent": int(recommended.get("suggested_pass_percent") or 70),
            "duration_minutes": int(recommended.get("duration_minutes") or 60),
            "question_count": 80,
            "questions": stored_questions,
        },
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return {
        "attempt_id": str(attempt.id),
        "title": attempt.answers_summary["exam_title"],
        "duration_minutes": attempt.answers_summary["duration_minutes"],
        "pass_percent": attempt.answers_summary["pass_percent"],
        "question_count": 80,
        "questions": [
            {key: q[key] for key in ("id", "lesson_slug", "topic", "prompt", "options")}
            for q in stored_questions
        ],
    }


def _find_owned_exam_attempt(attempt_id: str, user: User, db: Session) -> ExamAttempt:
    try:
        parsed_id = UUID(attempt_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=404, detail="Exam attempt was not found.")
    attempt = db.scalar(
        select(ExamAttempt).where(
            ExamAttempt.id == parsed_id, ExamAttempt.user_id == user.id
        )
    )
    if not attempt:
        raise HTTPException(status_code=404, detail="Exam attempt was not found.")
    return attempt


@app.get("/api/me/exams/{attempt_id}")
def get_my_exam_attempt(
    attempt_id: str, user: User = Depends(require_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    attempt = _find_owned_exam_attempt(attempt_id, user, db)
    summary = attempt.answers_summary or {}
    if not attempt.submitted_at:
        course = db.get(Course, attempt.course_id)
        if course is None:
            raise HTTPException(status_code=404, detail="Course was not found.")
        _require_course_prerequisites(db, user, course)
        _same_course, course_dir, blueprint = _load_exam_blueprint(course.slug, db)
        readiness = _exam_bank_readiness(course_dir, blueprint)
        if not readiness["ready"]:
            raise HTTPException(
                status_code=409,
                detail={"code": "exam_content_not_ready", "message": "This exam's published question bank is no longer ready; restart after the course team restores it."},
            )
        _load_practical_exam(course_dir)
    if attempt.submitted_at:
        return {
            "attempt_id": str(attempt.id),
            "status": "submitted",
            "score": attempt.score,
            "passed": attempt.passed,
            **{
                key: value
                for key, value in summary.items()
                if key not in {"questions", "answer_key"}
            },
        }
    return {
        "attempt_id": str(attempt.id),
        "status": "in_progress",
        "title": summary.get("exam_title") or "Skills Assessment",
        "duration_minutes": summary.get("duration_minutes"),
        "pass_percent": summary.get("pass_percent", 70),
        "question_count": summary.get("question_count", 0),
        "questions": [
            {key: q[key] for key in ("id", "lesson_slug", "topic", "prompt", "options")}
            for q in summary.get("questions", [])
            if isinstance(q, dict)
        ],
    }


@app.post("/api/me/exams/{attempt_id}/submit")
def submit_course_exam(
    attempt_id: str,
    payload: dict[str, Any],
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    attempt = _find_owned_exam_attempt(attempt_id, user, db)
    if attempt.submitted_at:
        raise HTTPException(
            status_code=409, detail="This exam attempt has already been submitted."
        )
    course = db.get(Course, attempt.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course was not found.")
    _require_course_prerequisites(db, user, course)
    _same_course, course_dir, current_blueprint = _load_exam_blueprint(course.slug, db)
    current_readiness = _exam_bank_readiness(course_dir, current_blueprint)
    if not current_readiness["ready"]:
        raise HTTPException(
            status_code=409,
            detail={"code": "exam_content_not_ready", "message": "The published question bank is no longer ready; this attempt cannot be graded."},
        )
    _load_practical_exam(course_dir)
    summary = attempt.answers_summary or {}
    questions = summary.get("questions")
    answers = payload.get("answers") if isinstance(payload, dict) else None
    if not isinstance(questions, list) or not questions:
        raise HTTPException(
            status_code=409, detail="This exam attempt has no question set."
        )
    if not isinstance(answers, dict) or not answers:
        raise HTTPException(
            status_code=422,
            detail="Submit an answers object with one selected option per question.",
        )
    question_by_id = {str(q.get("id")): q for q in questions if isinstance(q, dict)}
    if set(answers) != set(question_by_id):
        raise HTTPException(
            status_code=422, detail="Answer every exam question exactly once."
        )
    results: list[dict[str, Any]] = []
    correct_count = 0
    for question_id, question in question_by_id.items():
        selected = answers.get(question_id)
        if not isinstance(selected, str) or selected not in question.get("options", []):
            raise HTTPException(
                status_code=422,
                detail="Each exam answer must match one of the offered options.",
            )
        correct = selected == question.get("answer_key")
        correct_count += int(correct)
        results.append(
            {
                "question_id": question_id,
                "prompt": question.get("prompt", ""),
                "topic": question.get("topic", "General skills"),
                "lesson_slug": question.get("lesson_slug", ""),
                "selected_answer": selected,
                "is_correct": correct,
                "correct_answer": question.get("answer_key"),
                "explanation": question.get(
                    "explanation", "Review the relevant lesson and try again."
                ),
            }
        )
    score_percent = round(correct_count / len(questions) * 100)
    pass_percent = int(summary.get("pass_percent") or 70)
    passed = score_percent >= pass_percent
    attempt.score = score_percent
    attempt.passed = passed
    attempt.submitted_at = utc_now()
    attempt.answers_summary = {
        "status": "submitted",
        "course_slug": summary.get("course_slug"),
        "exam_title": summary.get("exam_title"),
        "question_count": len(questions),
        "correct_count": correct_count,
        "score_percent": score_percent,
        "pass_percent": pass_percent,
        "results": results,
    }
    db.commit()
    db.refresh(attempt)
    eligibility = _certificate_eligibility_payload(
        db, user, course, current_blueprint, attempt, issue_if_eligible=passed
    )
    db.commit()
    if eligibility.get("certificate"):
        db.refresh(attempt)
    return {
        "attempt_id": str(attempt.id),
        "status": "submitted",
        "score": score_percent,
        "score_percent": score_percent,
        "correct_count": correct_count,
        "question_count": len(questions),
        "pass_percent": pass_percent,
        "passed": passed,
        "results": results,
        "certificate": eligibility.get("certificate"),
        "certificate_status": eligibility.get("status"),
        "certificate_message": eligibility.get("message"),
    }


def _require_mcq_pass_for_practical(
    db: Session, user: User, course: Course
) -> ExamAttempt:
    _require_course_prerequisites(db, user, course)
    attempt = _latest_passed_mcq_attempt(db, user, course)
    if attempt is None:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "mcq_pass_required",
                "message": "Pass the 80-question MCQ exam before starting the practical assessment.",
            },
        )
    return attempt


def _public_practical_result(attempt: PracticalExamAttempt) -> dict[str, Any]:
    summary = attempt.answers_summary or {}
    return {
        "attempt_id": str(attempt.id),
        "status": "submitted" if attempt.submitted_at else "in_progress",
        "score_percent": attempt.score if attempt.submitted_at else None,
        "passed": attempt.passed if attempt.submitted_at else None,
        "pass_percent": summary.get("pass_percent", 70),
        "results": summary.get("results", []) if attempt.submitted_at else [],
        "message": (
            "Practical assessment passed."
            if attempt.submitted_at and attempt.passed
            else "Practical assessment submitted; review the result and retry if needed."
            if attempt.submitted_at
            else "Complete each practical task and submit your answers."
        ),
    }


def _grade_practical_task(task: dict[str, Any], submitted: str) -> bool:
    grader = task.get("grader") or {}
    mode = grader.get("type")
    case_sensitive = bool(grader.get("case_sensitive", False))

    def normalize(value: Any) -> str:
        text_value = " ".join(str(value or "").strip().split())
        return text_value if case_sensitive else text_value.casefold()

    if mode == "exact_text":
        expected = grader.get("expected")
        accepted = expected if isinstance(expected, list) else [expected]
        return any(normalize(submitted) == normalize(item) for item in accepted if isinstance(item, str))
    if mode == "contains_all":
        required = grader.get("required_strings")
        if not isinstance(required, list) or not all(isinstance(item, str) for item in required):
            return False
        actual = submitted if case_sensitive else submitted.casefold()
        return all((item if case_sensitive else item.casefold()) in actual for item in required)
    if mode == "json_equal":
        try:
            actual_json = json.loads(submitted)
            expected = grader.get("expected")
            expected_json = json.loads(expected) if isinstance(expected, str) else expected
            return actual_json == expected_json
        except (json.JSONDecodeError, TypeError, ValueError):
            return False
    return False


@app.get("/api/courses/{course_slug}/practical-exam")
def get_course_practical_exam(
    course_slug: str, user: User = Depends(require_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Expose published practical tasks only after a learner passed the MCQ stage."""
    course = get_course_visible_to_reader(db, course_slug)
    mcq_attempt = _require_mcq_pass_for_practical(db, user, course)
    _same_course, course_dir, _blueprint = _load_exam_blueprint(course_slug, db)
    practical = _load_practical_exam(course_dir)
    previous = _practical_attempt_for_mcq(db, user, course, mcq_attempt)
    return {
        "course_slug": course_slug,
        "title": str(practical.get("title") or f"{course.title} Practical Assessment"),
        "difficulty": str(practical.get("difficulty") or "intermediate"),
        "pass_percent": int(practical.get("pass_percent") or 70),
        "mcq_attempt_id": str(mcq_attempt.id),
        "task_count": len(practical["tasks"]),
        "tasks": [_practical_task_public(task) for task in practical["tasks"]],
        "previous_attempt": _public_practical_result(previous) if previous else None,
    }


@app.post("/api/courses/{course_slug}/practical-exam/start", status_code=status.HTTP_201_CREATED)
def start_course_practical_exam(
    course_slug: str, user: User = Depends(require_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Create or resume an owned practical attempt linked to a passed MCQ attempt."""
    course = get_course_visible_to_reader(db, course_slug)
    mcq_attempt = _require_mcq_pass_for_practical(db, user, course)
    _same_course, course_dir, _blueprint = _load_exam_blueprint(course_slug, db)
    practical = _load_practical_exam(course_dir)
    existing = db.scalar(
        select(PracticalExamAttempt)
        .where(
            PracticalExamAttempt.user_id == user.id,
            PracticalExamAttempt.course_id == course.id,
            PracticalExamAttempt.mcq_attempt_id == mcq_attempt.id,
            PracticalExamAttempt.submitted_at.is_(None),
        )
        .order_by(PracticalExamAttempt.started_at.desc())
        .limit(1)
    )
    if existing is not None:
        attempt = existing
    else:
        task_definitions = [
            {
                **_practical_task_public(task),
                "grader": task["grader"],
                "feedback_correct": str(task.get("feedback_correct") or "Accepted."),
                "feedback_incorrect": str(task.get("feedback_incorrect") or "Review the task requirements and try again."),
            }
            for task in practical["tasks"]
        ]
        attempt = PracticalExamAttempt(
            user_id=user.id,
            course_id=course.id,
            mcq_attempt_id=mcq_attempt.id,
            score=0,
            passed=False,
            answers_summary={
                "status": "in_progress",
                "title": str(practical.get("title") or f"{course.title} Practical Assessment"),
                "pass_percent": int(practical.get("pass_percent") or 70),
                "tasks": task_definitions,
            },
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
    summary = attempt.answers_summary or {}
    return {
        **_public_practical_result(attempt),
        "title": summary.get("title") or "Practical Assessment",
        "tasks": [
            {key: task[key] for key in ("id", "title", "prompt", "submission_type", "starter", "rubric", "points")}
            for task in summary.get("tasks", []) if isinstance(task, dict)
        ],
    }


@app.get("/api/me/practical-exams/{attempt_id}")
def get_my_practical_exam_attempt(
    attempt_id: str, user: User = Depends(require_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    try:
        parsed_id = UUID(attempt_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=404, detail="Practical attempt was not found.")
    attempt = db.scalar(
        select(PracticalExamAttempt).where(
            PracticalExamAttempt.id == parsed_id,
            PracticalExamAttempt.user_id == user.id,
        )
    )
    if attempt is None:
        raise HTTPException(status_code=404, detail="Practical attempt was not found.")
    result = _public_practical_result(attempt)
    if not attempt.submitted_at:
        summary = attempt.answers_summary or {}
        result.update({
            "title": summary.get("title") or "Practical Assessment",
            "tasks": [
                {key: task[key] for key in ("id", "title", "prompt", "submission_type", "starter", "rubric", "points")}
                for task in summary.get("tasks", []) if isinstance(task, dict)
            ],
        })
    return result


@app.post("/api/me/practical-exams/{attempt_id}/submit")
def submit_course_practical_exam(
    attempt_id: str,
    payload: dict[str, Any],
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    try:
        parsed_id = UUID(attempt_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=404, detail="Practical attempt was not found.")
    attempt = db.scalar(
        select(PracticalExamAttempt).where(
            PracticalExamAttempt.id == parsed_id,
            PracticalExamAttempt.user_id == user.id,
        )
    )
    if attempt is None:
        raise HTTPException(status_code=404, detail="Practical attempt was not found.")
    if attempt.submitted_at:
        raise HTTPException(status_code=409, detail="This practical attempt has already been submitted.")

    course = db.get(Course, attempt.course_id)
    mcq_attempt = db.get(ExamAttempt, attempt.mcq_attempt_id)
    if (
        course is None or mcq_attempt is None
        or mcq_attempt.user_id != user.id
        or mcq_attempt.course_id != course.id
        or mcq_attempt.submitted_at is None
        or not mcq_attempt.passed
    ):
        raise HTTPException(status_code=403, detail="A passed MCQ attempt for this course is required.")
    _require_course_prerequisites(db, user, course)
    _same_course, course_dir, blueprint = _load_exam_blueprint(course.slug, db)
    practical = _load_practical_exam(course_dir)
    summary = attempt.answers_summary or {}
    tasks = summary.get("tasks")
    answers = payload.get("answers") if isinstance(payload, dict) else None
    if not isinstance(tasks, list) or not tasks or not isinstance(answers, dict):
        raise HTTPException(status_code=422, detail="Submit an answers object with one answer per practical task.")
    task_by_id = {str(task.get("id")): task for task in tasks if isinstance(task, dict)}
    if set(answers) != set(task_by_id):
        raise HTTPException(status_code=422, detail="Answer every practical task exactly once.")
    correct_points = 0
    maximum_points = 0
    results = []
    for task_id, task in task_by_id.items():
        submitted = answers.get(task_id)
        if not isinstance(submitted, str) or len(submitted) > 50_000:
            raise HTTPException(status_code=422, detail="Each practical answer must be text under 50,000 characters.")
        points = int(task.get("points") or 100)
        maximum_points += points
        correct = _grade_practical_task(task, submitted)
        earned = points if correct else 0
        correct_points += earned
        results.append({
            "task_id": task_id,
            "title": str(task.get("title") or "Practical task"),
            "is_correct": correct,
            "points_earned": earned,
            "points_possible": points,
            "feedback": task.get("feedback_correct") if correct else task.get("feedback_incorrect"),
        })
    score_percent = round(correct_points * 100 / max(1, maximum_points))
    pass_percent = int(summary.get("pass_percent") or practical.get("pass_percent") or 70)
    passed = score_percent >= pass_percent
    attempt.score = score_percent
    attempt.passed = passed
    attempt.submitted_at = utc_now()
    attempt.answers_summary = {
        **summary,
        "status": "submitted",
        "submitted_answers": answers,
        "score_percent": score_percent,
        "pass_percent": pass_percent,
        "results": results,
    }
    db.commit()
    db.refresh(attempt)
    eligibility = _certificate_eligibility_payload(
        db, user, course, blueprint, mcq_attempt, issue_if_eligible=passed
    )
    db.commit()
    certificate = eligibility.get("certificate")
    return {
        "attempt_id": str(attempt.id),
        "status": "submitted",
        "score_percent": score_percent,
        "pass_percent": pass_percent,
        "passed": passed,
        "task_count": len(tasks),
        "results": results,
        "certificate": certificate,
        "certificate_status": eligibility.get("status"),
        "certificate_message": eligibility.get("message"),
    }


@app.get("/api/courses/{course_slug}/lessons/{lesson_slug}")
def get_published_lesson_content(
    course_slug: str, lesson_slug: str, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Return learner-safe lesson content; no exercise solutions or exam answer keys are included."""
    lesson = find_published_lesson(db, course_slug, lesson_slug)
    module = db.get(Module, lesson.module_id)
    stored = lesson.content or {}
    return {
        "id": stored.get("id") or f"{course_slug}-lesson-{lesson.sort_order:03d}",
        "slug": lesson.slug,
        "title": lesson.title,
        "sequence": lesson.sort_order,
        "module_slug": (stored.get("module_slug") or (module.slug if module else "")),
        "module_title": module.title if module else "",
        "level": stored.get("level", "beginner"),
        "track": stored.get("track", "core"),
        "estimated_minutes": lesson.estimated_minutes,
        "keywords": stored.get("keywords", []),
        "prerequisites": stored.get("prerequisites", []),
        "previous_lesson_id": stored.get("previous_lesson_id"),
        "next_lesson_id": stored.get("next_lesson_id"),
        "learning_outcomes": stored.get("learning_outcomes", []),
        "content": {
            key: value
            for key, value in (stored.get("content", {}) or {}).items()
            if key
            not in {
                "knowledge_check_file",
                "answer_key",
                "solution_file",
                "reference_solution_file",
            }
        },
        "sources": stored.get("sources", []),
    }


def _load_lesson_knowledge_check(course_slug: str, lesson: Lesson) -> dict[str, Any]:
    """Load a repository-side question set without exposing its answer key by default."""
    stored = lesson.content or {}
    lesson_content = stored.get("content", {}) or {}
    relative_path = lesson_content.get("knowledge_check_file")
    if not isinstance(relative_path, str) or not relative_path:
        raise HTTPException(
            status_code=404, detail="No knowledge check is available for this lesson."
        )

    course_root = (COURSE_CONTENT_ROOT / course_slug).resolve()
    target = (course_root / relative_path).resolve()
    if (
        course_root not in target.parents
        or target.suffix.lower() != ".json"
        or not target.is_file()
    ):
        raise HTTPException(status_code=404, detail="Knowledge check was not found.")
    try:
        question_set = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500, detail="Knowledge-check content is invalid."
        ) from exc

    lesson_id = stored.get("id") or f"{course_slug}-lesson-{lesson.sort_order:03d}"
    if (
        not isinstance(question_set, dict)
        or question_set.get("lesson_id") != lesson_id
        or question_set.get("lesson_slug") != lesson.slug
        or not isinstance(question_set.get("questions"), list)
    ):
        raise HTTPException(
            status_code=500,
            detail="Knowledge-check content does not match this lesson.",
        )
    if question_set.get("status") != "published" and not (
        draft_course_preview_enabled() and question_set.get("status") == "draft"
    ):
        raise HTTPException(
            status_code=404, detail="Knowledge check is not published yet."
        )
    return question_set


@app.get("/api/courses/{course_slug}/lessons/{lesson_slug}/knowledge-check")
def get_lesson_knowledge_check(
    course_slug: str, lesson_slug: str, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Return only prompts and options; answer keys and explanations stay server-side."""
    lesson = find_published_lesson(db, course_slug, lesson_slug)
    question_set = _load_lesson_knowledge_check(course_slug, lesson)
    questions = []
    for question in question_set["questions"]:
        if (
            not isinstance(question, dict)
            or not isinstance(question.get("id"), str)
            or not isinstance(question.get("prompt"), str)
            or not isinstance(question.get("options"), list)
            or not question["options"]
            or not all(isinstance(option, str) for option in question["options"])
        ):
            raise HTTPException(
                status_code=500, detail="A knowledge-check question is malformed."
            )
        questions.append(
            {
                "id": question["id"],
                "type": question.get("type", "single_choice"),
                "prompt": question["prompt"],
                "options": question["options"],
            }
        )
    return {
        "id": question_set.get("id"),
        "title": question_set.get("title", "Knowledge check"),
        "questions": questions,
        "question_count": len(questions),
    }


@app.post("/api/courses/{course_slug}/lessons/{lesson_slug}/knowledge-check/submit")
def submit_lesson_knowledge_check(
    course_slug: str,
    lesson_slug: str,
    payload: dict[str, Any],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Grade only submitted options and reveal feedback only for those questions."""
    lesson = find_published_lesson(db, course_slug, lesson_slug)
    question_set = _load_lesson_knowledge_check(course_slug, lesson)
    answers = payload.get("answers") if isinstance(payload, dict) else None
    if not isinstance(answers, dict) or not answers:
        raise HTTPException(
            status_code=422,
            detail="Submit an answers object with at least one selected option.",
        )

    question_by_id = {
        question.get("id"): question
        for question in question_set["questions"]
        if isinstance(question, dict) and isinstance(question.get("id"), str)
    }
    unknown_ids = set(answers) - set(question_by_id)
    if unknown_ids:
        raise HTTPException(
            status_code=422, detail="One or more submitted question IDs are invalid."
        )

    results = []
    correct_count = 0
    for question_id, selected in answers.items():
        question = question_by_id[question_id]
        options = question.get("options", [])
        if not isinstance(selected, str) or selected not in options:
            raise HTTPException(
                status_code=422,
                detail="Each answer must match one of that question's options.",
            )
        correct_answer = question.get("answer_key")
        if not isinstance(correct_answer, str):
            raise HTTPException(
                status_code=500, detail="A knowledge-check answer key is missing."
            )
        is_correct = selected == correct_answer
        correct_count += int(is_correct)
        results.append(
            {
                "question_id": question_id,
                "selected_answer": selected,
                "is_correct": is_correct,
                "correct_answer": correct_answer,
                "explanation": str(
                    question.get("explanation", "Review the lesson and try again.")
                ),
            }
        )
    answered_count = len(results)
    return {
        "answered_count": answered_count,
        "correct_count": correct_count,
        "score_percent": round((correct_count / answered_count) * 100),
        "results": results,
        "message": "Knowledge check submitted. Review the feedback and revisit any concepts that need practice.",
    }


@app.get("/api/courses/{course_slug}/assets/{asset_path:path}")
def get_published_course_asset(
    course_slug: str, asset_path: str, db: Session = Depends(get_db)
) -> FileResponse:
    """Serve only safe course assets; never statically expose JSON with answer keys."""
    get_course_visible_to_reader(db, course_slug)
    if not asset_path or "\\" in asset_path or "\x00" in asset_path:
        raise HTTPException(status_code=400, detail="Invalid asset path.")
    # URL path segments must stay inside the course assets directory even when symlinks
    # or encoded traversal segments are involved.
    requested_parts = Path(asset_path).parts
    if (
        any(part in {".", ".."} for part in requested_parts)
        or Path(asset_path).is_absolute()
    ):
        raise HTTPException(status_code=404, detail="Course asset was not found.")
    root = (COURSE_CONTENT_ROOT / course_slug / "assets").resolve()
    try:
        target = (root / asset_path).resolve(strict=True)
    except (FileNotFoundError, RuntimeError, OSError):
        raise HTTPException(status_code=404, detail="Course asset was not found.")
    allowed_suffixes = {".svg", ".webp", ".png", ".jpg", ".jpeg", ".gif", ".mp4"}
    is_inside_assets = root in target.parents
    relative_parts = target.relative_to(root).parts if is_inside_assets else ()
    # Only public visual diagram models may be served as JSON. Never expose arbitrary
    # course JSON here because it may include exam answer keys or reference solutions.
    is_dynamic_diagram = (
        len(relative_parts) >= 2
        and relative_parts[0].lower() == "diagrams"
        and target.name.lower().endswith(".diagram.json")
    )
    if (
        not is_inside_assets
        or (target.suffix.lower() not in allowed_suffixes and not is_dynamic_diagram)
        or not target.is_file()
    ):
        raise HTTPException(status_code=404, detail="Course asset was not found.")
    if is_dynamic_diagram:
        try:
            validate_dynamic_diagram_model(
                target, f"public diagram {course_slug}/{asset_path}"
            )
        except ValueError as exc:
            # Invalid files in the diagram directory are not public assets. Do not
            # return the file or its contents, and keep private JSON unavailable.
            raise HTTPException(
                status_code=404, detail="Course asset was not found."
            ) from exc
    media_types = {
        ".svg": "image/svg+xml",
        ".webp": "image/webp",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".mp4": "video/mp4",
    }
    return FileResponse(
        target,
        media_type=(
            "application/json"
            if is_dynamic_diagram
            else media_types[target.suffix.lower()]
        ),
        headers={"Cache-Control": "public, max-age=3600"},
    )


def _is_premium_project(project_doc: dict[str, Any]) -> bool:
    """Keep explicit flags and advanced project tiers aligned with Max entitlements.

    Existing project manifests commonly identify capstones through `tier` instead
    of an `is_premium` flag, so relying only on the flag leaves those projects open.
    """
    if project_doc.get("is_premium") is True or project_doc.get("premium") is True:
        return True
    tier = re.sub(r"[_\s]+", "-", str(project_doc.get("tier") or "").strip().casefold())
    return tier in {"capstone", "advanced-capstone", "professional", "specialist", "interview-prep"}


@app.get("/api/courses/{course_slug}/projects")
def list_published_course_projects(
    course_slug: str,
    user: User | None = Depends(optional_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return learner-facing project briefs while withholding protected reference solutions."""
    get_course_visible_to_reader(db, course_slug)
    course_dir = (COURSE_CONTENT_ROOT / course_slug).resolve()
    try:
        metadata = json.loads((course_dir / "course.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500, detail="Course project index is invalid."
        ) from exc
    items = []
    for relative in metadata.get("project_files", []):
        path = (course_dir / str(relative)).resolve()
        if (
            course_dir not in path.parents
            or not path.is_file()
            or path.suffix.lower() != ".json"
        ):
            continue
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if item.get("status") != "published" and not (
            draft_course_preview_enabled() and item.get("status") == "draft"
        ):
            continue
        is_premium_project = _is_premium_project(item)
        has_premium_projects = bool(
            user and plan_features(effective_plan_id(db, user.id)).get("premium_projects")
        )
        if is_premium_project and not has_premium_projects:
            items.append({
                "id": item.get("id"), "slug": item.get("slug"),
                "title": item.get("title"), "sequence": item.get("sequence"),
                "tier": item.get("tier"), "status": item.get("status"),
                "is_locked": True, "required_plan": "max", "upgrade_url": "/plans",
            })
            continue
        safe_item = {
            key: item.get(key)
            for key in (
                "id",
                "slug",
                "title",
                "sequence",
                "tier",
                "objective",
                "prerequisite_lesson_ids",
                "recommended_lesson_range",
                "skills",
                "milestones",
                "required_features",
                "stretch_features",
                "rubric",
                "rubric_total",
                "review_method",
                "status",
                "starter_files",
                "starter_readme",
            )
            if key in item
        }
        if isinstance(safe_item.get("starter_files"), list):
            safe_item["starter_files"] = [
                row
                for row in safe_item["starter_files"]
                if not is_protected_project_path(
                    row
                    if isinstance(row, str)
                    else (
                        row.get("path") or row.get("name")
                        if isinstance(row, dict)
                        else None
                    )
                )
            ]
        if is_protected_project_path(safe_item.get("starter_readme")):
            safe_item.pop("starter_readme", None)
        items.append(safe_item)
    items.sort(key=lambda item: item.get("sequence", 0))
    return {"items": items}


def _load_project_manifest_for_guide(
    course_slug: str, project_slug: str, db: Session, user: User | None = None
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    """Load one visible project manifest without opening protected solution files."""
    get_course_visible_to_reader(db, course_slug)
    content_root = COURSE_CONTENT_ROOT.resolve()
    course_dir = (content_root / course_slug).resolve()
    metadata_path = (course_dir / "course.json").resolve()
    # Keep the course slug inside the configured content root even if a crafted path
    # reaches this route; only real course directories may be inspected.
    if (
        content_root not in course_dir.parents
        or course_dir not in metadata_path.parents
        or not metadata_path.is_file()
    ):
        raise HTTPException(status_code=404, detail="Course content was not found.")
    try:
        course_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500, detail="Course project index is invalid."
        ) from exc

    selected: dict[str, Any] | None = None
    project_files = course_metadata.get("project_files", [])
    if not isinstance(project_files, list):
        raise HTTPException(status_code=500, detail="Course project index is invalid.")
    for relative in project_files:
        if not isinstance(relative, str) or "\\" in relative:
            continue
        parts = Path(relative).parts
        # Never expose a solution file even if the course index is accidentally misconfigured.
        if any(
            part.lower() in {"solution", "solutions", "answer-keys", "answer_keys"}
            for part in parts
        ):
            continue
        project_path = (course_dir / relative).resolve()
        if (
            course_dir not in project_path.parents
            or project_path.suffix.lower() != ".json"
            or not project_path.is_file()
        ):
            continue
        try:
            project_doc = json.loads(project_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if (
            project_doc.get("slug") == project_slug
            or project_doc.get("id") == project_slug
        ):
            selected = project_doc
            break

    if selected is None:
        raise HTTPException(status_code=404, detail="Project guide was not found.")
    if selected.get("status") != "published" and not (
        draft_course_preview_enabled() and selected.get("status") == "draft"
    ):
        raise HTTPException(
            status_code=404, detail="Project guide is not published yet."
        )
    if _is_premium_project(selected):
        current = effective_plan_id(db, user.id) if user else "free"
        if not (user and plan_features(current).get("premium_projects")):
            raise HTTPException(status_code=403, detail={
                "code": "FEATURE_REQUIRES_UPGRADE", "feature": "premium_projects",
                "current_plan": current, "required_plan": "max", "upgrade_url": "/plans",
                "message": "This project requires the Max plan or Full Access.",
            })
    return course_dir, course_metadata, selected


@app.get("/api/courses/{course_slug}/projects/{project_slug}")
def get_published_course_project_guide(
    course_slug: str,
    project_slug: str,
    user: User | None = Depends(optional_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return a complete learner-facing build guide and explicitly declared starter code."""
    course_dir, course_metadata, project_doc = _load_project_manifest_for_guide(
        course_slug, project_slug, db, user
    )
    return build_project_guide(course_slug, course_metadata, project_doc, course_dir)


@app.get("/api/courses/{course_slug}/projects/{project_slug}/starter-kit.zip")
def download_published_course_project_starter_kit(
    course_slug: str,
    project_slug: str,
    user: User | None = Depends(optional_user),
    db: Session = Depends(get_db),
) -> Response:
    """Download learner-safe starter files; protected reference solutions are never included."""
    course_dir, course_metadata, project_doc = _load_project_manifest_for_guide(
        course_slug, project_slug, db, user
    )
    guide = build_project_guide(course_slug, course_metadata, project_doc, course_dir)
    archive_bytes = project_guide_zip(guide)
    raw_name = str(project_doc.get("slug") or project_doc.get("title") or "project")
    safe_name = (
        "".join(char for char in raw_name if char.isalnum() or char in "-_")[:80]
        or "project"
    )
    return Response(
        content=archive_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{safe_name}-starter-kit.zip"'
        },
    )


@app.get("/api/courses/{course_slug}/projects/{project_slug}/starter-files/{file_id}")
def get_published_course_project_starter_file(
    course_slug: str,
    project_slug: str,
    file_id: str,
    user: User | None = Depends(optional_user),
    db: Session = Depends(get_db),
) -> Response:
    """Download an explicitly declared learner starter file, never a reference solution."""
    get_course_visible_to_reader(db, course_slug)
    course_dir = (COURSE_CONTENT_ROOT / course_slug).resolve()
    try:
        metadata = json.loads((course_dir / "course.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500, detail="Course project index is invalid."
        ) from exc

    selected: dict[str, Any] | None = None
    for relative in metadata.get("project_files", []):
        project_path = (course_dir / str(relative)).resolve()
        if (
            course_dir not in project_path.parents
            or project_path.suffix.lower() != ".json"
            or not project_path.is_file()
        ):
            continue
        try:
            project_doc = json.loads(project_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if project_doc.get("slug") == project_slug:
            selected = project_doc
            break

    if selected is None:
        raise HTTPException(status_code=404, detail="Project was not found.")
    if selected.get("status") != "published" and not (
        draft_course_preview_enabled() and selected.get("status") == "draft"
    ):
        raise HTTPException(status_code=404, detail="Project is not published yet.")
    if _is_premium_project(selected):
        current = effective_plan_id(db, user.id) if user else "free"
        if not (user and plan_features(current).get("premium_projects")):
            raise HTTPException(status_code=403, detail={
                "code": "FEATURE_REQUIRES_UPGRADE", "feature": "premium_projects",
                "current_plan": current, "required_plan": "max", "upgrade_url": "/plans",
                "message": "This project requires the Max plan or Full Access.",
            })

    if file_id == "readme":
        relative_file = selected.get("starter_readme")
    elif file_id.isascii() and file_id.isdigit() and len(file_id) <= 3:
        starter_files = selected.get("starter_files", [])
        index = int(file_id)
        relative_file = (
            starter_files[index]
            if isinstance(starter_files, list) and index < len(starter_files)
            else None
        )
    else:
        relative_file = None

    if (
        not isinstance(relative_file, str)
        or not relative_file
        or is_protected_project_path(relative_file)
    ):
        raise HTTPException(
            status_code=404, detail="Project starter file was not found."
        )
    target = (course_dir / relative_file).resolve()
    # Project files are explicit metadata references constrained beneath the course
    # root. Allow known text-based starter artifacts, including Rust source and Cargo
    # manifests, while continuing to reject other executable/binary formats by default.
    allowed_suffixes = {
        ".cpp",
        ".h",
        ".hpp",
        ".md",
        ".sql",
        ".xml",
        ".xsd",
        ".xsl",
        ".xslt",
        ".dtd",
        ".xq",
        ".txt",
        ".swift",
        ".rs",
        ".toml",
        ".dart",
        ".yaml",
        ".yml",
    }
    if (
        course_dir not in target.parents
        or target.suffix.lower() not in allowed_suffixes
        or not target.is_file()
    ):
        raise HTTPException(
            status_code=404, detail="Project starter file was not found."
        )
    try:
        source = target.read_text(encoding="utf-8")
    except OSError as exc:
        raise HTTPException(
            status_code=500, detail="Project starter file could not be read."
        ) from exc
    return Response(
        content=source,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{target.name}"'},
    )


@app.get("/api/plans")
def list_plans() -> dict[str, Any]:
    """Public, server-owned plan catalog; prices and quotas come from one definition."""
    return {
        "integrations": {
            "ai_available": bool(
                settings.ai_api_base_url and settings.ai_api_key and settings.ai_model
            ),
            "supported_runner_languages": ["python", "javascript"],
        },
        "items": [
            {
                "id": plan_id,
                "title": definition["title"],
                "amount_paise": definition["amount_paise"],
                "currency": "INR",
                "billing": definition["billing"],
                "description": definition["description"],
                "features": dict(definition["features"]),
                "limits": dict(definition["limits"]),
            }
            for plan_id, definition in PLAN_DEFINITIONS.items()
        ],
        "payments": payment_checkout_readiness(),
    }


@app.get("/api/me")
def who_am_i(
    user: User = Depends(require_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    entitlements = active_entitlements(db, user.id)
    total_xp = (
        db.scalar(
            select(func.coalesce(func.sum(XPTransaction.awarded_points), 0)).where(
                XPTransaction.user_id == user.id
            )
        )
        or 0
    )
    completed_lessons = (
        db.scalar(
            select(func.count(LessonProgress.id)).where(
                LessonProgress.user_id == user.id, LessonProgress.completed.is_(True)
            )
        )
        or 0
    )
    bookmarks = (
        db.scalar(select(func.count(Bookmark.id)).where(Bookmark.user_id == user.id))
        or 0
    )
    certificates = (
        db.scalar(
            select(func.count(Certificate.id)).where(
                Certificate.user_id == user.id, Certificate.revoked_at.is_(None)
            )
        )
        or 0
    )
    current_plan = effective_plan_id(db, user.id)
    return {
        "user": user_payload(user),
        "current_plan": {
            "id": current_plan,
            "title": PLAN_DEFINITIONS[current_plan]["title"],
            "billing": PLAN_DEFINITIONS[current_plan]["billing"],
            "lifetime": current_plan == "full_access",
        },
        "features": plan_features(current_plan),
        "limits": plan_limits(current_plan),
        "entitlements": [
            {
                "plan_id": e.plan_id,
                "status": e.status,
                "ends_at": e.ends_at.isoformat() if e.ends_at else None,
            }
            for e in entitlements
        ],
        "stats": {
            "total_xp": int(total_xp),
            "completed_lessons": completed_lessons,
            "bookmarks": bookmarks,
            "certificates": certificates,
        },
    }


@app.patch("/api/me/profile")
def update_profile(
    body: AvatarUpdate,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    # Restrict the theme values and cap avatar JSON size to avoid turning profile preferences into arbitrary payload storage.
    if len(json.dumps(body.avatar, ensure_ascii=False)) > 2_000:
        raise HTTPException(status_code=413, detail="Avatar settings are too large.")
    user.avatar = body.avatar
    user.theme = body.theme
    if body.display_name is not None:
        user.display_name = body.display_name.strip()
    if body.username is not None:
        candidate = body.username.strip().lower()
        duplicate = db.scalar(
            select(User).where(User.username == candidate, User.id != user.id)
        )
        if duplicate:
            raise HTTPException(
                status_code=409, detail="That username is already in use."
            )
        user.username = candidate
    db.commit()
    db.refresh(user)
    return {"user": user_payload(user)}


@app.post("/api/payments/create")
async def create_payment(
    body: PaymentCreateInput,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    # Serialize checkout creation per account. This prevents parallel clicks from
    # creating multiple provider orders/subscriptions for the same user and plan.
    db.scalar(select(User).where(User.id == user.id).with_for_update())
    key_id, _ = ensure_payment_config()
    plan = PLAN_CONFIG[body.plan_id]
    current_plan = effective_plan_id(db, user.id)
    if current_plan == "full_access":
        raise HTTPException(
            status_code=409,
            detail="Full Access is already active on this account. It is a lifetime entitlement and does not renew.",
        )
    if body.plan_id == current_plan:
        raise HTTPException(
            status_code=409,
            detail=f"The {PLAN_DEFINITIONS[current_plan]['title']} plan is already active on this account.",
        )
    if body.plan_id == "pro" and current_plan in {"pro", "max"}:
        raise HTTPException(
            status_code=409,
            detail=f"This account already has {PLAN_DEFINITIONS[current_plan]['title']} access. Choose Max or Full Access to upgrade.",
        )

    def order_checkout_response(record: PaymentRecord, *, resumed: bool) -> dict[str, Any]:
        return {
            "kind": "order",
            "key_id": key_id,
            "order_id": record.provider_order_id,
            "amount": record.amount_paise,
            "currency": record.currency,
            "name": "CodeLeaf",
            "description": "Full Access — lifetime platform access",
            "prefill": {"email": user.email, "name": user.display_name},
            "resumed": resumed,
        }

    def subscription_checkout_response(
        record: PaymentRecord, *, resumed: bool, provider_status: str
    ) -> dict[str, Any]:
        return {
            "kind": "subscription",
            "key_id": key_id,
            "subscription_id": record.provider_subscription_id,
            "plan_id": body.plan_id,
            "name": "CodeLeaf",
            "description": f"{plan['title']} monthly membership",
            "prefill": {"email": user.email, "name": user.display_name},
            "status": provider_status,
            "billing_cycles": int((record.provider_payload or {}).get("total_count") or settings.razorpay_subscription_total_count),
            "resumed": resumed,
        }

    if body.plan_id == "full_access":
        # A created/attempted Razorpay order remains payable. Reuse it instead of
        # creating a new order or blocking the learner with a permanent 409.
        open_orders = db.scalars(
            select(PaymentRecord).where(
                PaymentRecord.user_id == user.id,
                PaymentRecord.plan_id == "full_access",
                PaymentRecord.kind == "order",
                PaymentRecord.status.in_({"created", "attempted", "authorized", "authenticated", "pending", "failed"}),
            ).order_by(PaymentRecord.created_at.desc())
        ).all()
        for record in open_orders:
            if not record.provider_order_id:
                continue
            try:
                provider_order = await razorpay_request(
                    "GET", f"/orders/{record.provider_order_id}"
                )
            except HTTPException as exc:
                if exc.status_code == 404:
                    record.status = "expired"
                    continue
                raise HTTPException(
                    status_code=503,
                    detail={
                        "code": "PENDING_ORDER_CHECK_FAILED",
                        "message": "CodeLeaf could not verify the unfinished Full Access checkout. Refresh billing status and try again; no new order was created.",
                    },
                ) from exc

            provider_status = str(provider_order.get("status") or "").lower()
            if provider_status in {"created", "attempted"}:
                if (
                    int(provider_order.get("amount") or 0) != record.amount_paise
                    or provider_order.get("currency") != record.currency
                ):
                    raise HTTPException(
                        status_code=409,
                        detail={
                            "code": "PENDING_ORDER_MISMATCH",
                            "message": "The existing checkout does not match the configured Full Access price. Contact support before retrying.",
                        },
                    )
                record.status = "created"
                db.commit()
                return order_checkout_response(record, resumed=True)
            if provider_status == "paid":
                record.provider_payload = {
                    **(record.provider_payload or {}),
                    "provider_order_paid_seen": True,
                    "payment_reconciliation_pending": True,
                }
                db.commit()
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": "PAYMENT_RECONCILIATION_PENDING",
                        "message": "Razorpay reports that this order has been paid. CodeLeaf is waiting for verified payment confirmation; refresh your membership status before starting another payment.",
                    },
                )
            if provider_status in {"cancelled", "expired"}:
                record.status = provider_status
                continue
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "PENDING_ORDER_STATUS_UNCLEAR",
                    "message": "The previous Full Access checkout is still being checked by Razorpay. Please refresh billing status before trying again.",
                },
            )

        receipt = f"ca-{secrets.token_hex(12)}"
        provider = await razorpay_request(
            "POST",
            "/orders",
            {
                "amount": plan["amount_paise"],
                "currency": plan["currency"],
                "receipt": receipt,
                "notes": {"user_id": str(user.id), "plan_id": body.plan_id},
            },
        )
        record = PaymentRecord(
            user_id=user.id,
            plan_id=body.plan_id,
            amount_paise=plan["amount_paise"],
            currency="INR",
            kind="order",
            status="created",
            provider_order_id=provider["id"],
            provider_payload={"receipt": receipt},
        )
        db.add(record)
        db.commit()
        return order_checkout_response(record, resumed=False)

    provider_plan_id = (
        settings.razorpay_pro_plan_id
        if body.plan_id == "pro"
        else settings.razorpay_max_plan_id
    )
    if not provider_plan_id:
        raise HTTPException(
            status_code=503,
            detail=f"Set RAZORPAY_{body.plan_id.upper()}_PLAN_ID after creating the matching monthly plan in Razorpay.",
        )

    pending_statuses = {"created", "authenticated", "pending", "active", "halted", "past_due"}
    pending_records = db.scalars(
        select(PaymentRecord).where(
            PaymentRecord.user_id == user.id,
            PaymentRecord.plan_id == body.plan_id,
            PaymentRecord.kind == "subscription",
            PaymentRecord.status.in_(pending_statuses),
        ).order_by(PaymentRecord.created_at.desc())
    ).all()
    for record in pending_records:
        if not record.provider_subscription_id:
            continue
        try:
            provider_state = await razorpay_request(
                "GET", f"/subscriptions/{record.provider_subscription_id}"
            )
        except HTTPException as exc:
            if exc.status_code == 404:
                record.status = "expired"
                continue
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "PENDING_SUBSCRIPTION_CHECK_FAILED",
                    "message": "CodeLeaf could not verify the unfinished subscription. Refresh billing status and try again; a duplicate subscription was not created.",
                },
            ) from exc

        provider_status = str(provider_state.get("status") or "").lower()
        record.status = provider_status or record.status
        if provider_state.get("plan_id") and provider_state.get("plan_id") != provider_plan_id:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "PENDING_SUBSCRIPTION_PLAN_MISMATCH",
                    "message": "The existing subscription is attached to a different Razorpay plan. Contact support before creating another subscription.",
                },
            )
        if provider_status == "created":
            expire_by = parse_epoch(provider_state.get("expire_by"))
            if expire_by is not None and expire_by <= utc_now():
                try:
                    cancelled = await razorpay_request(
                        "POST",
                        f"/subscriptions/{record.provider_subscription_id}/cancel",
                        {"cancel_at_cycle_end": False},
                    )
                    record.status = str(cancelled.get("status") or "cancelled")
                    record.provider_payload = {
                        **(record.provider_payload or {}),
                        "pending_checkout_cancelled": True,
                        "expired_authorization_cancelled_at": utc_now().isoformat(),
                    }
                    db.flush()
                    continue
                except Exception as exc:
                    detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
                    raise HTTPException(
                        status_code=409,
                        detail={
                            "code": "EXPIRED_CHECKOUT_CLEANUP_REQUIRED",
                            "message": f"The previous authorization window has expired and Razorpay could not close it automatically. Contact support before retrying. {str(detail)[:180]}",
                        },
                    ) from exc
            db.commit()
            return subscription_checkout_response(
                record, resumed=True, provider_status=provider_status
            )
        if provider_status in {"authenticated", "active", "pending"}:
            db.commit()
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "SUBSCRIPTION_CONFIRMATION_PENDING",
                    "message": "Razorpay has already advanced this subscription. CodeLeaf is waiting for its signed billing event; refresh membership status instead of creating another subscription.",
                },
            )
        if provider_status == "halted":
            try:
                cancelled = await razorpay_request(
                    "POST",
                    f"/subscriptions/{record.provider_subscription_id}/cancel",
                    {"cancel_at_cycle_end": False},
                )
                record.status = str(cancelled.get("status") or "cancelled")
                record.provider_payload = {
                    **(record.provider_payload or {}),
                    "superseded_after_halt_at": utc_now().isoformat(),
                }
                db.flush()
                continue
            except Exception as exc:
                detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": "HALTED_SUBSCRIPTION_CLEANUP_REQUIRED",
                        "message": f"The previous subscription is halted and must be reconciled before another can be created. {str(detail)[:180]}",
                    },
                ) from exc
        if provider_status in {"cancelled", "completed", "expired"}:
            record.status = provider_status
            db.flush()
            continue
        raise HTTPException(
            status_code=409,
            detail={
                "code": "SUBSCRIPTION_STATUS_UNCLEAR",
                "message": "The previous subscription has an unrecognized provider state. Contact support before creating another subscription.",
            },
        )

    provider_plan = await razorpay_request("GET", f"/plans/{provider_plan_id}")
    item = provider_plan.get("item") or {}
    if (
        int(item.get("amount") or 0) != plan["amount_paise"]
        or item.get("currency") != "INR"
        or provider_plan.get("period") != "monthly"
        or int(provider_plan.get("interval") or 1) != 1
    ):
        raise HTTPException(
            status_code=409,
            detail="The configured Razorpay plan does not match the app's INR price and monthly billing. Update the provider plan or server configuration before checkout.",
        )
    total_count = settings.razorpay_subscription_total_count
    if total_count < 1:
        raise HTTPException(
            status_code=503,
            detail="Set RAZORPAY_SUBSCRIPTION_TOTAL_COUNT to a provider-supported positive number of monthly billing cycles.",
        )
    provider = await razorpay_request(
        "POST",
        "/subscriptions",
        {
            "plan_id": provider_plan_id,
            "total_count": total_count,
            "quantity": 1,
            "customer_notify": 1,
            "notes": {"user_id": str(user.id), "plan_id": body.plan_id},
        },
    )
    record = PaymentRecord(
        user_id=user.id,
        plan_id=body.plan_id,
        amount_paise=plan["amount_paise"],
        currency="INR",
        kind="subscription",
        status=provider.get("status", "created"),
        provider_subscription_id=provider["id"],
        provider_payload={
            "total_count": total_count,
            "provider_plan_id": provider_plan_id,
        },
    )
    db.add(record)
    db.commit()
    return subscription_checkout_response(
        record,
        resumed=False,
        provider_status=str(provider.get("status") or "created").lower(),
    )


@app.post("/api/payments/verify")
async def verify_full_access_payment(
    body: PaymentVerifyInput,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    key_id, key_secret = ensure_payment_config()
    record = db.scalar(
        select(PaymentRecord).where(
            PaymentRecord.provider_order_id == body.razorpay_order_id,
            PaymentRecord.user_id == user.id,
            PaymentRecord.plan_id == "full_access",
        )
    )
    if not record:
        raise HTTPException(
            status_code=404,
            detail="Matching payment order was not found for this account.",
        )
    if str(record.status or "").lower() in {"refunded", "reversed", "failed", "cancelled"}:
        raise HTTPException(
            status_code=409,
            detail="This order is no longer eligible to grant Full Access. Contact support if you believe this is incorrect.",
        )
    expected = hmac.new(
        key_secret.encode(),
        f"{body.razorpay_order_id}|{body.razorpay_payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, body.razorpay_signature):
        raise HTTPException(
            status_code=400, detail="Payment signature could not be verified."
        )
    payment = await razorpay_request("GET", f"/payments/{body.razorpay_payment_id}")
    if (
        payment.get("order_id") != body.razorpay_order_id
        or payment.get("currency") != "INR"
        or int(payment.get("amount") or 0) != record.amount_paise
    ):
        raise HTTPException(
            status_code=400,
            detail="Payment amount, currency or order does not match this checkout.",
        )
    if payment.get("status") != "captured":
        raise HTTPException(
            status_code=409,
            detail="The payment is not captured yet. Access will be enabled after confirmed payment.",
        )
    record.provider_payment_id = body.razorpay_payment_id
    record.status = "paid"
    record.provider_payload = {
        **(record.provider_payload or {}),
        "captured_payment_status": payment.get("status"),
    }
    grant_entitlement(db, user_id=user.id, plan_id="full_access", payment_record=record)
    await schedule_superseded_subscriptions_for_cancellation(
        db, user_id=user.id, target_plan_id="full_access"
    )
    db.commit()
    return {
        "ok": True,
        "plan_id": "full_access",
        "message": "Payment verified. Full Access is now enabled.",
    }


@app.post("/api/payments/verify-subscription")
async def verify_subscription_payment(
    request: Request, user: User = Depends(require_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    body = await request.json()
    subscription_id = str(body.get("razorpay_subscription_id", ""))
    payment_id = str(body.get("razorpay_payment_id", ""))
    signature = str(body.get("razorpay_signature", ""))
    if not subscription_id or not payment_id or not signature:
        raise HTTPException(
            status_code=422, detail="The Razorpay subscription callback is incomplete."
        )
    _, key_secret = ensure_payment_config()
    record = db.scalar(
        select(PaymentRecord).where(
            PaymentRecord.provider_subscription_id == subscription_id,
            PaymentRecord.user_id == user.id,
            PaymentRecord.kind == "subscription",
        )
    )
    if not record:
        raise HTTPException(
            status_code=404,
            detail="Matching subscription was not found for this account.",
        )
    expected = hmac.new(
        key_secret.encode(), f"{payment_id}|{subscription_id}".encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(
            status_code=400, detail="Subscription signature could not be verified."
        )
    provider_payment = await razorpay_request("GET", f"/payments/{payment_id}")
    provider_subscription = await razorpay_request(
        "GET", f"/subscriptions/{subscription_id}"
    )
    configured_plan_id = (
        settings.razorpay_pro_plan_id
        if record.plan_id == "pro"
        else settings.razorpay_max_plan_id
    )
    if provider_subscription.get("plan_id") != configured_plan_id:
        raise HTTPException(
            status_code=400,
            detail="The provider subscription does not match the server-configured plan.",
        )
    if provider_payment.get("currency") != "INR" or provider_payment.get(
        "status"
    ) not in {"captured", "authorized"}:
        raise HTTPException(
            status_code=409,
            detail="The subscription authorization/payment has not been confirmed yet.",
        )
    if provider_subscription.get("status") not in {"active", "authenticated"}:
        raise HTTPException(
            status_code=409,
            detail="The provider has not activated this subscription yet.",
        )
    record.provider_payment_id = payment_id
    record.status = provider_subscription.get("status", "created")
    record.provider_payload = {
        **(record.provider_payload or {}),
        "checkout_signature_verified": True,
    }
    db.commit()
    # Do not grant a recurring entitlement from the browser callback. The signed webhook activates it.
    return {
        "ok": True,
        "plan_id": record.plan_id,
        "message": "Checkout signature verified. Membership access is enabled after the signed provider webhook confirms the active billing period.",
    }


@app.get("/api/me/billing")
def get_billing(
    user: User = Depends(require_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    entitlements = active_entitlements(db, user.id)
    subscription_records = db.scalars(
        select(PaymentRecord)
        .where(PaymentRecord.user_id == user.id, PaymentRecord.kind == "subscription")
        .order_by(PaymentRecord.created_at.desc())
    ).all()
    order_records = db.scalars(
        select(PaymentRecord)
        .where(
            PaymentRecord.user_id == user.id,
            PaymentRecord.kind == "order",
            PaymentRecord.plan_id == "full_access",
        )
        .order_by(PaymentRecord.created_at.desc())
    ).all()
    entitlement_by_subscription = {
        e.provider_subscription_id: e
        for e in entitlements
        if e.provider_subscription_id
    }
    current_plan = effective_plan_id(db, user.id)
    now = utc_now()

    memberships: list[dict[str, Any]] = []
    pending_checkouts: list[dict[str, Any]] = []
    seen_pending_plans: set[str] = set()

    # A subscription is shown as a membership only when it has a matching,
    # currently valid, server-verified entitlement.
    for record in subscription_records:
        subscription_id = record.provider_subscription_id
        if not subscription_id:
            continue
        entitlement = entitlement_by_subscription.get(subscription_id)
        payload = dict(record.provider_payload or {})
        if entitlement is not None:
            period_end = entitlement.ends_at
            if period_end is not None and period_end.tzinfo is None:
                period_end = period_end.replace(tzinfo=timezone.utc)
            memberships.append({
                "subscription_id": subscription_id,
                "plan_id": record.plan_id,
                "status": record.status,
                "amount_paise": record.amount_paise,
                "ends_at": period_end.isoformat() if period_end else None,
                "cancelable": bool(
                    record.status.lower() in {"active", "halted"}
                    and period_end is not None
                    and period_end > now
                    and not payload.get("cancel_at_cycle_end")
                ),
                "cancellation_scheduled": bool(payload.get("cancel_at_cycle_end")),
                "cancellation_required": bool(payload.get("cancellation_required")),
                "cancellation_error": payload.get("cancellation_error"),
            })
            continue

        status_value = record.status.lower()
        if status_value == "created" and record.plan_id not in seen_pending_plans:
            pending_checkouts.append({
                "kind": "subscription",
                "subscription_id": subscription_id,
                "plan_id": record.plan_id,
                "status": status_value,
                "state": "awaiting_payment",
                "cancelable": True,
                "message": "Payment has not been confirmed. This is not an active membership.",
            })
            seen_pending_plans.add(record.plan_id)
        elif status_value == "authenticated" and record.plan_id not in seen_pending_plans:
            pending_checkouts.append({
                "kind": "subscription",
                "subscription_id": subscription_id,
                "plan_id": record.plan_id,
                "status": status_value,
                "state": "awaiting_verification",
                "cancelable": True,
                "message": "Razorpay has authenticated the subscription, but CodeLeaf has not received a verified paid billing period yet.",
            })
            seen_pending_plans.add(record.plan_id)
        elif status_value in {"active", "pending", "halted", "past_due"} and record.plan_id not in seen_pending_plans:
            pending_checkouts.append({
                "kind": "subscription",
                "subscription_id": subscription_id,
                "plan_id": record.plan_id,
                "status": status_value,
                "state": "awaiting_verification",
                "cancelable": False,
                "message": "Razorpay has advanced this subscription, but CodeLeaf has not received a verified active entitlement yet.",
            })
            seen_pending_plans.add(record.plan_id)

    if current_plan != "full_access":
        for record in order_records:
            if record.status.lower() not in {"created", "attempted", "authorized", "authenticated", "pending", "failed"}:
                continue
            if "full_access" in seen_pending_plans:
                break
            pending_checkouts.append({
                "kind": "order",
                "order_id": record.provider_order_id,
                "plan_id": "full_access",
                "status": record.status,
                "state": "awaiting_payment",
                "cancelable": False,
                "message": "Full Access has not been purchased yet. Resume this checkout to continue; no lifetime entitlement is active.",
            })
            seen_pending_plans.add("full_access")

    return {
        "current_plan": {
            "id": current_plan,
            "title": PLAN_DEFINITIONS[current_plan]["title"],
            "billing": PLAN_DEFINITIONS[current_plan]["billing"],
            "lifetime": current_plan == "full_access",
        },
        "features": plan_features(current_plan),
        "limits": plan_limits(current_plan),
        "entitlements": [
            {
                "plan_id": entitlement.plan_id,
                "status": entitlement.status,
                "ends_at": entitlement.ends_at.isoformat() if entitlement.ends_at else None,
            }
            for entitlement in entitlements
        ],
        "subscriptions": memberships,
        "pending_checkouts": pending_checkouts,
    }


@app.post("/api/payments/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: str,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    record = db.scalar(
        select(PaymentRecord).where(
            PaymentRecord.provider_subscription_id == subscription_id,
            PaymentRecord.user_id == user.id,
            PaymentRecord.kind == "subscription",
        )
    )
    if not record:
        raise HTTPException(
            status_code=404, detail="Subscription was not found for this account."
        )

    try:
        provider_state = await razorpay_request(
            "GET", f"/subscriptions/{subscription_id}"
        )
    except HTTPException as exc:
        if exc.status_code == 404:
            record.status = "expired"
            db.commit()
            return {
                "ok": True,
                "cancelled": True,
                "message": "The unpaid checkout no longer exists with Razorpay. No membership was active.",
            }
        raise

    provider_status = str(provider_state.get("status") or record.status).lower()
    if provider_status in {"cancelled", "completed", "expired"}:
        record.status = provider_status
        db.commit()
        return {
            "ok": True,
            "cancelled": True,
            "message": "This subscription is already closed. No further cancellation is required.",
        }

    user_entitlements = active_entitlements(db, user.id)
    matching_entitlement = next(
        (
            entitlement
            for entitlement in user_entitlements
            if entitlement.provider_subscription_id == subscription_id
        ),
        None,
    )
    current_start = parse_epoch(provider_state.get("current_start"))
    current_end = parse_epoch(provider_state.get("current_end"))
    has_paid_current_cycle = (
        matching_entitlement is not None
        and provider_status in {"active", "halted"}
        and current_start is not None
        and current_end is not None
        and current_end > utc_now()
    )
    payload = dict(record.provider_payload or {})
    if payload.get("cancel_at_cycle_end") is True:
        return {
            "ok": True,
            "status": provider_status,
            "cancellation_scheduled": True,
            "message": "Auto-renewal cancellation is already scheduled.",
        }

    if has_paid_current_cycle:
        cancel_at_cycle_end = True
    elif matching_entitlement is None and provider_status in {"created", "authenticated"}:
        # An unpaid/unauthorized checkout has no paid cycle to preserve. Close it now.
        cancel_at_cycle_end = False
    else:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "SUBSCRIPTION_NOT_CANCELLABLE",
                "message": "This subscription has no verified paid billing cycle to cancel at period end. Refresh membership status; no cancellation request was sent.",
                "provider_status": provider_status,
            },
        )

    provider_result = await razorpay_request(
        "POST",
        f"/subscriptions/{subscription_id}/cancel",
        {"cancel_at_cycle_end": cancel_at_cycle_end},
    )
    record.status = str(provider_result.get("status") or provider_status)
    record.provider_payload = {
        **payload,
        "cancel_at_cycle_end": cancel_at_cycle_end,
        "pending_checkout_cancelled": not cancel_at_cycle_end,
        "cancellation_requested_at": utc_now().isoformat(),
    }
    db.commit()
    if cancel_at_cycle_end:
        return {
            "ok": True,
            "status": record.status,
            "cancellation_scheduled": True,
            "message": "Auto-renewal is scheduled to stop at the end of the paid billing period. Existing paid access remains until then.",
        }
    return {
        "ok": True,
        "status": record.status,
        "cancelled_pending": True,
        "message": "Unpaid checkout cancelled immediately. No membership access was removed because no paid entitlement was active.",
    }


@app.post("/api/payments/webhook")
async def payment_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: str | None = Header(default=None),
    x_razorpay_event_id: str | None = Header(default=None),
) -> dict[str, bool]:
    secret = settings.razorpay_webhook_secret
    if not secret:
        raise HTTPException(
            status_code=503, detail="Razorpay webhook secret is not configured."
        )
    raw = await request.body()
    expected = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    if not x_razorpay_signature or not hmac.compare_digest(
        expected, x_razorpay_signature
    ):
        raise HTTPException(status_code=400, detail="Invalid webhook signature.")
    event_id = x_razorpay_event_id or hashlib.sha256(raw).hexdigest()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise HTTPException(status_code=400, detail="Webhook body is not valid JSON.")

    event = WebhookEvent(
        provider_event_id=event_id,
        event_type=str(payload.get("event", "unknown")),
        payload=payload,
        processed=False,
    )
    db.add(event)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return {"ok": True}  # The provider retried an event we already accepted.

    event_name = str(payload.get("event") or "unknown")
    entities = payload.get("payload") or {}
    order_entity = (entities.get("order") or {}).get("entity") or {}
    payment_entity = (entities.get("payment") or {}).get("entity") or {}
    subscription_entity = (entities.get("subscription") or {}).get("entity") or {}
    refund_entity = (entities.get("refund") or {}).get("entity") or {}
    event_created_at = int(payload.get("created_at") or 0)

    if event_name == "order.paid":
        order_id = order_entity.get("id") or payment_entity.get("order_id")
        record = (
            db.scalar(
                select(PaymentRecord).where(PaymentRecord.provider_order_id == order_id)
            )
            if order_id
            else None
        )
        amount = payment_entity.get("amount") or order_entity.get("amount")
        currency = payment_entity.get("currency") or order_entity.get("currency")
        if (
            record
            and record.plan_id == "full_access"
            and record.status not in {"refunded", "reversed"}
            and int(amount or 0) == record.amount_paise
            and currency == "INR"
        ):
            record.status = "paid"
            if payment_entity.get("id"):
                record.provider_payment_id = payment_entity["id"]
            grant_entitlement(
                db, user_id=record.user_id, plan_id="full_access", payment_record=record
            )
            await schedule_superseded_subscriptions_for_cancellation(
                db, user_id=record.user_id, target_plan_id="full_access"
            )
    elif event_name in {
        "subscription.activated",
        "subscription.charged",
        "subscription.updated",
        "subscription.cancelled",
        "subscription.halted",
        "subscription.paused",
        "subscription.resumed",
        "subscription.completed",
        "subscription.expired",
    }:
        sub_id = subscription_entity.get("id")
        record = (
            db.scalar(
                select(PaymentRecord).where(
                    PaymentRecord.provider_subscription_id == sub_id
                )
            )
            if sub_id
            else None
        )
        if record:
            stored_payload = dict(record.provider_payload or {})
            last_event_at = int(stored_payload.get("last_subscription_event_at") or 0)
            # Provider events may be delivered out of order. Apply only the newest
            # subscription transition; duplicate event IDs are already deduplicated above.
            if event_created_at >= last_event_at:
                provider_status = str(
                    subscription_entity.get("status", event_name.split(".")[-1])
                ).lower()
                record.status = provider_status
                stored_payload["last_subscription_event_at"] = event_created_at
                stored_payload["last_subscription_event_type"] = event_name
                record.provider_payload = stored_payload
                existing = db.scalar(
                    select(Entitlement).where(
                        Entitlement.provider_subscription_id == sub_id,
                        Entitlement.user_id == record.user_id,
                    )
                )
                period_end = parse_epoch(subscription_entity.get("current_end"))
                if provider_status == "active" and period_end is not None:
                    grant_entitlement(
                        db,
                        user_id=record.user_id,
                        plan_id=record.plan_id,
                        payment_record=record,
                        subscription_id=sub_id,
                        ends_at=period_end,
                    )
                    if record.plan_id == "max":
                        await schedule_superseded_subscriptions_for_cancellation(
                            db, user_id=record.user_id, target_plan_id="max",
                            excluding_subscription_id=sub_id,
                        )
                elif existing:
                    existing.ends_at = period_end or existing.ends_at
                    existing.cancelled_at = (
                        utc_now()
                        if event_name in {"subscription.cancelled", "subscription.completed", "subscription.expired"}
                        else existing.cancelled_at
                    )
                    if event_name in {"subscription.halted", "subscription.paused"}:
                        existing.status = "past_due" if event_name == "subscription.halted" else "paused"
                    elif event_name in {"subscription.completed", "subscription.expired"}:
                        existing.status = "expired"
                    elif event_name == "subscription.cancelled" and (
                        not existing.ends_at or (existing.ends_at.replace(tzinfo=timezone.utc) if existing.ends_at.tzinfo is None else existing.ends_at.astimezone(timezone.utc)) <= utc_now()
                    ):
                        existing.status = "cancelled"
    elif event_name == "payment.failed":
        order_id = payment_entity.get("order_id")
        sub_id = payment_entity.get("subscription_id")
        record = None
        if order_id:
            record = db.scalar(
                select(PaymentRecord).where(PaymentRecord.provider_order_id == order_id)
            )
        if record is None and sub_id:
            record = db.scalar(
                select(PaymentRecord).where(PaymentRecord.provider_subscription_id == sub_id)
            )
        if record and record.status not in {"paid", "refunded", "reversed"}:
            record.provider_payload = {
                **(record.provider_payload or {}),
                "last_payment_failed_at": utc_now().isoformat(),
                "last_payment_failure_code": str(payment_entity.get("error_code") or "")[:80],
                "last_payment_failure_description": str(payment_entity.get("error_description") or "")[:240],
            }
            # A failed attempt does not close a Razorpay order or prove a subscription
            # is terminal. Keep the provider object resumable; signed subscription
            # lifecycle events remain authoritative for access.
    elif event_name in {"payment.refunded", "refund.processed"}:
        payment_id = payment_entity.get("id") or refund_entity.get("payment_id")
        order_id = payment_entity.get("order_id")
        record = None
        if payment_id:
            record = db.scalar(
                select(PaymentRecord).where(PaymentRecord.provider_payment_id == payment_id)
            )
        if record is None and order_id:
            record = db.scalar(
                select(PaymentRecord).where(PaymentRecord.provider_order_id == order_id)
            )
        if record and record.plan_id == "full_access":
            provider_details = dict(record.provider_payload or {})
            previous_refunds = int(provider_details.get("refund_amount_paise_total") or 0)
            refund_event_amount = int(refund_entity.get("amount") or 0)
            if event_name == "payment.refunded" and payment_entity.get("amount_refunded") is not None:
                cumulative_refund = int(payment_entity.get("amount_refunded") or 0)
            else:
                cumulative_refund = previous_refunds + refund_event_amount
            provider_details["refund_amount_paise_total"] = max(previous_refunds, cumulative_refund)
            if provider_details["refund_amount_paise_total"] >= record.amount_paise:
                record.status = "refunded"
                provider_details = dict(record.provider_payload or {})
                provider_details["refund_amount_paise_total"] = max(previous_refunds, cumulative_refund)
                provider_details["fully_refunded_at"] = utc_now().isoformat()
                record.provider_payload = provider_details
                entitlement = db.scalar(
                    select(Entitlement).where(
                        Entitlement.user_id == record.user_id,
                        Entitlement.plan_id == "full_access",
                        Entitlement.source_payment_id == record.id,
                    )
                )
                if entitlement and entitlement.status == "active":
                    entitlement.status = "refunded"
                    entitlement.cancelled_at = utc_now()
                    db.add(
                        AuditLog(
                            actor_user_id=record.user_id,
                            action="entitlement.revoked_refund",
                            resource_type="entitlement",
                            resource_id=str(entitlement.id),
                            details={"plan_id": "full_access", "payment_record_id": str(record.id)},
                            created_at=utc_now(),
                        )
                    )
            else:
                provider_details["partial_refund_amount_paise"] = provider_details["refund_amount_paise_total"]
                record.provider_payload = provider_details

    event.processed = True
    event.processed_at = utc_now()
    db.commit()
    return {"ok": True}


def get_timezone(timezone_name: str | None) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name or "UTC")
    except (ZoneInfoNotFoundError, ValueError):
        return ZoneInfo("UTC")


def record_activity_day(db: Session, user_id: UUID, timezone_name: str | None) -> date:
    zone = get_timezone(timezone_name)
    day = utc_now().astimezone(zone).date()
    existing = db.scalar(
        select(UserActivityDay).where(
            UserActivityDay.user_id == user_id, UserActivityDay.activity_date == day
        )
    )
    if existing is None:
        db.add(
            UserActivityDay(user_id=user_id, activity_date=day, timezone_name=zone.key)
        )
    else:
        existing.timezone_name = zone.key
    return day


def calculate_streaks(days: list[date], timezone_name: str | None) -> dict[str, Any]:
    zone = get_timezone(timezone_name)
    today = utc_now().astimezone(zone).date()
    day_set = set(days)
    start = (
        today
        if today in day_set
        else (
            today - timedelta(days=1) if today - timedelta(days=1) in day_set else None
        )
    )
    current = 0
    cursor = start
    while cursor is not None and cursor in day_set:
        current += 1
        cursor -= timedelta(days=1)
    longest = 0
    running = 0
    previous = None
    for active_day in sorted(day_set):
        running = (
            running + 1
            if previous is not None and active_day == previous + timedelta(days=1)
            else 1
        )
        longest = max(longest, running)
        previous = active_day
    seven_days = [
        {
            "date": (today - timedelta(days=offset)).isoformat(),
            "active": (today - timedelta(days=offset)) in day_set,
        }
        for offset in range(6, -1, -1)
    ]
    return {
        "current_streak": current,
        "longest_streak": longest,
        "today_active": today in day_set,
        "activity_days": seven_days,
        "activity_dates": sorted(day.isoformat() for day in day_set),
    }


def user_gamification_stats(
    db: Session, user_id: UUID, timezone_name: str | None = None
) -> dict[str, Any]:
    """Build the profile summary in one aggregate round-trip plus two small lookups."""
    # Scalar subqueries keep the counts independent (so joins cannot multiply rows)
    # but execute together in a single SQL statement instead of 8 separate round-trips.
    aggregate = (
        db.execute(
            select(
                select(func.coalesce(func.sum(XPTransaction.awarded_points), 0))
                .where(XPTransaction.user_id == user_id)
                .scalar_subquery()
                .label("total_xp"),
                select(func.count(LessonProgress.id))
                .where(
                    LessonProgress.user_id == user_id,
                    LessonProgress.completed.is_(True),
                )
                .scalar_subquery()
                .label("completed_lessons"),
                select(func.count(ExerciseProgress.id))
                .where(
                    ExerciseProgress.user_id == user_id,
                    ExerciseProgress.completed.is_(True),
                )
                .scalar_subquery()
                .label("completed_exercises"),
                select(func.coalesce(func.sum(ExerciseProgress.attempts), 0))
                .where(ExerciseProgress.user_id == user_id)
                .scalar_subquery()
                .label("exercises_attempted"),
                select(func.count(ExamAttempt.id))
                .where(ExamAttempt.user_id == user_id)
                .scalar_subquery()
                .label("exams_attempted"),
                select(func.count(ExamAttempt.id))
                .where(ExamAttempt.user_id == user_id, ExamAttempt.passed.is_(True))
                .scalar_subquery()
                .label("exams_passed"),
                select(func.count(Bookmark.id))
                .where(Bookmark.user_id == user_id)
                .scalar_subquery()
                .label("bookmarks"),
                select(func.count(Certificate.id))
                .where(Certificate.user_id == user_id, Certificate.revoked_at.is_(None))
                .scalar_subquery()
                .label("certificates"),
            )
        )
        .mappings()
        .one()
    )

    activity_dates = db.scalars(
        select(UserActivityDay.activity_date)
        .where(UserActivityDay.user_id == user_id)
        .order_by(UserActivityDay.activity_date)
    ).all()
    boosted = any(
        item.plan_id in {"max", "full_access"}
        for item in active_entitlements(db, user_id)
    )
    multiplier = XP_REWARDS["max_multiplier"] if boosted else 1.0
    return {
        "total_xp": int(aggregate["total_xp"] or 0),
        "completed_lessons": int(aggregate["completed_lessons"] or 0),
        "completed_exercises": int(aggregate["completed_exercises"] or 0),
        "exercises_attempted": int(aggregate["exercises_attempted"] or 0),
        "exams_attempted": int(aggregate["exams_attempted"] or 0),
        "exams_passed": int(aggregate["exams_passed"] or 0),
        "bookmarks": int(aggregate["bookmarks"] or 0),
        "certificates": int(aggregate["certificates"] or 0),
        "xp_multiplier": multiplier,
        "lesson_xp": int(XP_REWARDS["lesson"] * multiplier),
        "exercise_xp": int(XP_REWARDS["exercise"] * multiplier),
        **calculate_streaks(list(activity_dates), timezone_name),
    }


def xp_award(db: Session, user_id: UUID, activity_type: str) -> tuple[int, int, bool]:
    base_points = XP_REWARDS[activity_type]
    boosted = any(
        e.plan_id in {"max", "full_access"} for e in active_entitlements(db, user_id)
    )
    awarded = (
        int(base_points * XP_REWARDS["max_multiplier"]) if boosted else base_points
    )
    return base_points, awarded, boosted


@app.get("/api/me/stats")
def get_my_gamification_stats(
    timezone: str = "UTC",
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    return user_gamification_stats(db, user.id, timezone)


@app.get("/api/leaderboard")
def get_leaderboard(
    period: str = "week", limit: int = 20,
    user: User = Depends(require_user), db: Session = Depends(get_db),
) -> dict[str, Any]:
    # Pro introduces competitive learning leagues; standard lesson XP stays available
    # on Free, but the expanded leaderboard view is a plan-gated productivity feature.
    require_feature(db, user, "leaderboards")
    if period not in {"week", "all_time"}:
        raise HTTPException(status_code=422, detail="period must be week or all_time")
    limit = max(1, min(limit, 100))
    query = select(
        User.id,
        User.display_name,
        User.username,
        func.sum(XPTransaction.awarded_points).label("xp"),
    ).join(XPTransaction, XPTransaction.user_id == User.id)
    if period == "week":
        query = query.where(XPTransaction.created_at >= utc_now() - timedelta(days=7))
    rows = db.execute(
        query.group_by(User.id, User.display_name, User.username)
        .order_by(func.sum(XPTransaction.awarded_points).desc(), User.username.asc())
        .limit(limit)
    ).all()
    items = [
        {
            "rank": index,
            "display_name": row[1],
            "username": row[2],
            "avatar": {},
            "xp": int(row[3] or 0),
        }
        for index, row in enumerate(rows, start=1)
    ]
    return {"period": period, "items": items}


def find_published_lesson(db: Session, course_slug: str, lesson_slug: str) -> Lesson:
    query = (
        select(Lesson)
        .join(Module, Lesson.module_id == Module.id)
        .join(Course, Module.course_id == Course.id)
        .where(Course.slug == course_slug, Lesson.slug == lesson_slug)
    )
    if not draft_course_preview_enabled():
        query = query.where(
            Course.published.is_(True),
            Lesson.is_published.is_(True),
        )
    lesson = db.scalar(query)
    if lesson is not None and draft_course_preview_enabled():
        module = db.get(Module, lesson.module_id)
        course = db.get(Course, module.course_id) if module else None
        is_public = bool(course and course.published and lesson.is_published)
        is_imported_draft = (lesson.content or {}).get(
            "_codeleaf_course_slug"
        ) == course_slug
        if not is_public and not is_imported_draft:
            lesson = None
    if not lesson:
        raise HTTPException(
            status_code=404,
            detail="Published lesson was not found. Import course content first; draft preview is available only in explicitly enabled local development.",
        )
    return lesson


@app.get("/api/me/progress")
def list_progress(
    user: User = Depends(require_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    rows = db.execute(
        select(
            Course.slug,
            Lesson.slug,
            Lesson.title,
            LessonProgress.completed,
            LessonProgress.last_opened_at,
            LessonProgress.completed_at,
        )
        .join(Module, Course.id == Module.course_id)
        .join(Lesson, Module.id == Lesson.module_id)
        .join(LessonProgress, Lesson.id == LessonProgress.lesson_id)
        .where(LessonProgress.user_id == user.id)
        .order_by(LessonProgress.last_opened_at.desc())
    ).all()
    stats = user_gamification_stats(db, user.id)
    return {
        "items": [
            {
                "course_slug": row[0],
                "lesson_slug": row[1],
                "title": row[2],
                "completed": row[3],
                "last_opened_at": row[4].isoformat() if row[4] else None,
                "completed_at": row[5].isoformat() if row[5] else None,
            }
            for row in rows
        ],
        **stats,
    }


@app.post("/api/me/progress/{course_slug}/{lesson_slug}")
def mark_lesson_complete(
    course_slug: str,
    lesson_slug: str,
    body: ProgressUpdate,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    lesson = find_published_lesson(db, course_slug, lesson_slug)
    progress = db.scalar(
        select(LessonProgress).where(
            LessonProgress.user_id == user.id, LessonProgress.lesson_id == lesson.id
        )
    )
    newly_completed = progress is None or not progress.completed
    if progress is None:
        progress = LessonProgress(
            user_id=user.id,
            lesson_id=lesson.id,
            completed=True,
            time_spent_seconds=body.time_spent_seconds,
            completed_at=utc_now(),
            last_opened_at=utc_now(),
        )
        db.add(progress)
    else:
        progress.completed = True
        progress.time_spent_seconds = min(
            86_400, progress.time_spent_seconds + body.time_spent_seconds
        )
        progress.last_opened_at = utc_now()
        progress.completed_at = progress.completed_at or utc_now()
    xp_awarded = 0
    base_points = XP_REWARDS["lesson"]
    boost_applied = False
    if newly_completed:
        existing_xp = db.scalar(
            select(XPTransaction).where(
                XPTransaction.user_id == user.id,
                XPTransaction.source_type == "lesson_completed",
                XPTransaction.source_id == str(lesson.id),
            )
        )
        if existing_xp is None:
            base_points, xp_awarded, boost_applied = xp_award(db, user.id, "lesson")
            db.add(
                XPTransaction(
                    user_id=user.id,
                    source_type="lesson_completed",
                    source_id=str(lesson.id),
                    base_points=base_points,
                    awarded_points=xp_awarded,
                    boost_applied=boost_applied,
                )
            )
    record_activity_day(db, user.id, body.timezone)
    if newly_completed:
        # Lesson completion seeds a later retrieval review; this is not represented as skill mastery.
        record_review_result(db, user.id, course_slug, "lesson", lesson_slug, True)
    course_id = db.scalar(select(Module.course_id).where(Module.id == lesson.module_id))
    db.flush()
    published_lesson_count = (
        db.scalar(
            select(func.count(Lesson.id))
            .join(Module, Module.id == Lesson.module_id)
            .where(Module.course_id == course_id, Lesson.is_published.is_(True))
        )
        or 0
    )
    completed_lesson_count = (
        db.scalar(
            select(func.count(LessonProgress.id))
            .join(Lesson, LessonProgress.lesson_id == Lesson.id)
            .join(Module, Module.id == Lesson.module_id)
            .where(
                LessonProgress.user_id == user.id,
                LessonProgress.completed.is_(True),
                Module.course_id == course_id,
                Lesson.is_published.is_(True),
            )
        )
        or 0
    )
    course_completed_now = bool(
        newly_completed
        and published_lesson_count > 0
        and completed_lesson_count >= published_lesson_count
    )
    db.commit()
    db.refresh(progress)
    stats = user_gamification_stats(db, user.id, body.timezone)
    return {
        "ok": True,
        "course_slug": course_slug,
        "lesson_slug": lesson_slug,
        "completed": progress.completed,
        "newly_completed": newly_completed,
        "course_completed_now": course_completed_now,
        "base_xp": base_points,
        "xp_awarded": xp_awarded,
        "stats": stats,
    }


def find_published_exercise(
    db: Session, course_slug: str, lesson_slug: str, exercise_slug: str
) -> Exercise:
    lesson = find_published_lesson(db, course_slug, lesson_slug)
    query = select(Exercise).where(
        Exercise.lesson_id == lesson.id, Exercise.slug == exercise_slug
    )
    if not draft_course_preview_enabled():
        query = query.where(Exercise.is_published.is_(True))
    exercise = db.scalar(query)
    if exercise is None:
        raise HTTPException(
            status_code=404,
            detail="Published exercise was not found. Import course content first; draft preview is available only in explicitly enabled local development.",
        )
    if practice_exercise_kind(
        exercise.exercise_type, exercise.starter, course_slug, exercise.prompt
    ) is None:
        raise HTTPException(
            status_code=404,
            detail="Only multiple-choice questions and code challenges are available in Practice.",
        )
    return exercise


def grade_exercise(exercise: Exercise, body: ExerciseSubmission) -> bool:
    """Only allow explicit server-supported graders; never trust a client-sent correct flag."""
    config = exercise.grading_config or {}
    mode = config.get("mode")
    if mode == "choice":
        submitted = body.answer
        return str(submitted).strip() == str(config.get("correct_answer", "")).strip()
    if mode == "exact_text":
        submitted = body.source_code if body.source_code is not None else body.answer
        expected = config.get("expected_text", "")
        return (
            isinstance(submitted, str)
            and " ".join(submitted.strip().split()).casefold()
            == " ".join(str(expected).strip().split()).casefold()
        )
    if mode == "contains_all":
        submitted = body.source_code if body.source_code is not None else body.answer
        required = config.get("required_strings", [])
        return (
            isinstance(submitted, str)
            and isinstance(required, list)
            and all(str(item) in submitted for item in required)
        )
    raise HTTPException(
        status_code=422,
        detail="This exercise needs a supported grader before it can award XP.",
    )


@app.get("/api/me/courses/{course_slug}/exercise-progress")
def list_my_course_exercise_progress(
    course_slug: str,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return authoritative completion for only the authenticated learner's published exercises."""
    course = get_course_visible_to_reader(db, course_slug)
    rows = db.execute(
        select(Exercise, Lesson.slug, ExerciseProgress.completed, ExerciseProgress.attempts,
               ExerciseProgress.completed_at)
        .join(Lesson, Exercise.lesson_id == Lesson.id)
        .join(Module, Lesson.module_id == Module.id)
        .join(Course, Module.course_id == Course.id)
        .outerjoin(
            ExerciseProgress,
            (ExerciseProgress.exercise_id == Exercise.id)
            & (ExerciseProgress.user_id == user.id),
        )
        .where(
            Course.id == course.id,
            Course.published.is_(True),
            Lesson.is_published.is_(True),
            Exercise.is_published.is_(True),
        )
        .order_by(Module.sort_order.asc(), Lesson.sort_order.asc(), Exercise.sequence.asc())
    ).all()
    items = []
    current_plan_id = effective_plan_id(db, user.id)
    for exercise, lesson_slug, completed, attempts, completed_at in rows:
        if not can_access_exercise(current_plan_id, exercise):
            # Preserve historical progress in the database, but don't expose a
            # restricted practice collection in an account's visible progress set.
            continue
        if not is_supported_practice_exercise(
            exercise.exercise_type, exercise.starter, course_slug, exercise.prompt
        ):
            continue
        items.append(
            {
                "exercise_slug": exercise.slug,
                "lesson_slug": lesson_slug,
                "completed": bool(completed),
                "attempts": int(attempts or 0),
                "completed_at": completed_at.isoformat() if completed_at else None,
            }
        )
    return {"course_slug": course.slug, "items": items}


@app.get("/api/exercises/featured")
def list_featured_exercises(
    limit: int = 12,
    user: User | None = Depends(optional_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """List published exercises, plus learner-safe imported drafts in local preview."""
    limit = max(1, min(limit, 50))
    preview_mode = draft_course_preview_enabled()
    query = (
        select(
            Exercise,
            Course.slug,
            Lesson.slug,
            Course.title,
            Course.published,
            Lesson.is_published,
            Lesson.content,
        )
        .join(Lesson, Exercise.lesson_id == Lesson.id)
        .join(Module, Lesson.module_id == Module.id)
        .join(Course, Module.course_id == Course.id)
    )
    if not preview_mode:
        query = query.where(
            Course.published.is_(True),
            Lesson.is_published.is_(True),
            Exercise.is_published.is_(True),
        )
    rows = db.execute(
        query.order_by(
            Course.sort_order.asc(),
            Module.sort_order.asc(),
            Lesson.sort_order.asc(),
            Exercise.sequence.asc(),
        ).limit(limit if not preview_mode else 10_000)
    ).all()

    visible_items = []
    current_plan_id = effective_plan_id(db, user.id) if user else "free"
    for (
        exercise,
        course_slug,
        lesson_slug,
        course_title,
        course_is_published,
        lesson_is_published,
        lesson_content,
    ) in rows:
        published_item = bool(
            course_is_published and lesson_is_published and exercise.is_published
        )
        imported_draft = (
            preview_mode
            and isinstance(lesson_content, dict)
            and lesson_content.get("_codeleaf_course_slug") == course_slug
        )
        if not (published_item or imported_draft):
            continue
        public_type = public_practice_type(
            exercise.exercise_type, exercise.starter, course_slug, exercise.prompt
        )
        if public_type is None:
            continue
        if not can_access_exercise(current_plan_id, exercise):
            continue
        # Never expose the grader, solution or answer key in this learner-facing list.
        visible_items.append(
            {
                "slug": exercise.slug,
                "title": exercise.title,
                "type": public_type,
                "prompt": exercise.prompt,
                "difficulty": exercise.difficulty,
                "course_slug": course_slug,
                "course_title": course_title,
                "lesson_slug": lesson_slug,
                "xp_points": XP_REWARDS["exercise"],
            }
        )
        if len(visible_items) >= limit:
            break
    return {"items": visible_items, "preview_mode": preview_mode}


@app.get("/api/courses/{course_slug}/lessons/{lesson_slug}/exercises")
def list_lesson_exercises(
    course_slug: str,
    lesson_slug: str,
    user: User | None = Depends(optional_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    lesson = find_published_lesson(db, course_slug, lesson_slug)
    exercise_query = select(Exercise).where(Exercise.lesson_id == lesson.id)
    if not draft_course_preview_enabled():
        exercise_query = exercise_query.where(Exercise.is_published.is_(True))
    rows = db.scalars(exercise_query.order_by(Exercise.sequence.asc())).all()
    module = db.get(Module, lesson.module_id)
    course = db.get(Course, module.course_id) if module else None
    items = []
    current_plan_id = effective_plan_id(db, user.id) if user else "free"
    for item in rows:
        public_type = public_practice_type(
            item.exercise_type, item.starter, course_slug, item.prompt
        )
        if public_type is None:
            continue
        if not can_access_exercise(current_plan_id, item):
            required_plan = required_exercise_plan(item)
            items.append({
                "slug": item.slug,
                "title": item.title,
                "type": "locked",
                "is_locked": True,
                "required_plan": required_plan,
                "upgrade_url": "/plans",
                "sequence": item.sequence,
                "course_slug": course_slug,
                "lesson_slug": lesson_slug,
                "difficulty": item.difficulty,
            })
            continue
        items.append(
            {
                "slug": item.slug,
                "title": item.title,
                "type": public_type,
                "prompt": item.prompt,
                "starter": item.starter,
                "public_tests": item.public_tests,
                "acceptance_criteria": item.acceptance_criteria,
                "hints": item.hints,
                "sequence": item.sequence,
                "difficulty": item.difficulty,
                "xp_points": XP_REWARDS["exercise"],
                "course_slug": course_slug,
                "course_title": course.title if course else "",
                "lesson_slug": lesson.slug,
                "lesson_title": lesson.title,
                "module_title": module.title if module else "",
            }
        )
    return {
        "items": items
    }


def _safe_exercise_solution_payload(solution_doc: dict[str, Any]) -> dict[str, Any]:
    """Return learner-facing worked-solution fields, preferring complete examples over placeholders."""
    def display_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        try:
            return json.dumps(value, ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            return str(value)

    answer = solution_doc.get("answer", "")
    example_code = solution_doc.get("reference_code") or solution_doc.get("example_code") or solution_doc.get("solution_code")
    answer_text = display_text(answer).strip()
    # Older exercise rows contain an explanation that only points to the protected file, or a
    # generic "implement X" summary. When the linked solution has worked code, show that code.
    placeholder_markers = (
        "protected reference solution is stored",
        "not exposed in learner-facing",
        "implement ",
        "a strong solution should",
        "reference approach:",
        "required implementation evidence includes",
    )
    if example_code and (not answer_text or any(marker in answer_text.lower() for marker in placeholder_markers)):
        answer = example_code
    elif not answer_text and solution_doc.get("starter_code"):
        answer = solution_doc.get("starter_code")

    steps = solution_doc.get("steps")
    if not isinstance(steps, list) or not steps:
        steps = solution_doc.get("verification_steps")
    if not isinstance(steps, list) or not steps:
        steps = solution_doc.get("manual_validation_checklist")
    if not isinstance(steps, list):
        steps = []
    test_cases = solution_doc.get("test_cases")
    if not isinstance(test_cases, list):
        test_cases = []
    explanation = solution_doc.get("explanation", "")
    if not display_text(explanation).strip() and solution_doc.get("review_notes"):
        explanation = "\n".join(display_text(note) for note in solution_doc["review_notes"] if note)
    return {
        "answer": answer,
        "expected_result": display_text(solution_doc.get("expected_result") or solution_doc.get("expected_output")),
        "explanation": display_text(explanation),
        "steps": [display_text(step) for step in steps if isinstance(step, (str, int, float, dict, list)) and str(step).strip()],
        "test_cases": [
            {"input": display_text(item.get("input", "")), "expected": display_text(item.get("expected", item.get("expected_output", "")))}
            for item in test_cases
            if isinstance(item, dict)
        ],
    }


def _load_exercise_manifest(course_slug: str, lesson_slug: str, exercise_slug: str) -> tuple[Path, dict[str, Any]]:
    """Find the repository manifest for a published exercise without following user paths."""
    content_root = COURSE_CONTENT_ROOT.resolve()
    course_root = (content_root / course_slug).resolve()
    if content_root not in course_root.parents or not course_root.is_dir():
        raise HTTPException(status_code=404, detail="Exercise solution was not found.")

    for manifest_path in course_root.rglob("*.json"):
        if manifest_path.parent.name != "exercises" or "solutions" in manifest_path.parts:
            continue
        try:
            resolved_manifest = manifest_path.resolve()
            if content_root not in resolved_manifest.parents or course_root not in resolved_manifest.parents:
                continue
            manifest = json.loads(resolved_manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(manifest, dict) or manifest.get("slug") != exercise_slug:
            continue
        manifest_lesson = str(manifest.get("lesson_slug") or "").strip()
        if manifest_lesson and manifest_lesson != lesson_slug:
            continue
        return resolved_manifest, manifest
    raise HTTPException(status_code=404, detail="Exercise solution was not found.")


@app.get("/api/courses/{course_slug}/lessons/{lesson_slug}/exercises/{exercise_slug}/solution")
def reveal_exercise_solution(
    course_slug: str,
    lesson_slug: str,
    exercise_slug: str,
    user: User | None = Depends(optional_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Reveal the authored worked answer on request; prefer the linked reference file over legacy placeholders."""
    exercise = find_published_exercise(db, course_slug, lesson_slug, exercise_slug)
    require_exercise_access(db, user, exercise)
    manifest_path, manifest = _load_exercise_manifest(course_slug, lesson_slug, exercise_slug)
    content_root = COURSE_CONTENT_ROOT.resolve()
    course_root = (content_root / course_slug).resolve()
    solution_rel = manifest.get("solution_file")

    if isinstance(solution_rel, str) and solution_rel.strip():
        solution_path = (manifest_path.parent / solution_rel).resolve()
        try:
            relative_solution = solution_path.relative_to(course_root)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="Exercise solution was not found.") from exc
        if solution_path.suffix.lower() != ".json" or "solutions" not in {part.lower() for part in relative_solution.parts}:
            raise HTTPException(status_code=404, detail="Exercise solution was not found.")
        if solution_path.is_file():
            try:
                solution_doc = json.loads(solution_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise HTTPException(status_code=500, detail="The worked solution file is invalid.") from exc
            if not isinstance(solution_doc, dict):
                raise HTTPException(status_code=500, detail="The worked solution file is invalid.")
            expected_exercise_id = str(manifest.get("id") or "").strip()
            linked_exercise_id = str(solution_doc.get("exercise_id") or "").strip()
            if linked_exercise_id and expected_exercise_id and linked_exercise_id != expected_exercise_id:
                raise HTTPException(status_code=404, detail="Exercise solution was not found.")
            payload = _safe_exercise_solution_payload(solution_doc)
            if any(payload.get(key) for key in ("answer", "explanation", "expected_result", "steps", "test_cases")):
                return {"exercise_slug": exercise_slug, **payload}

    # Older database rows can contain only a generic explanation while the checked-in
    # manifest has since gained the complete worked answer. Do not let that stale row
    # mask the fuller, versioned source content.
    stored_solution = exercise.solution if isinstance(exercise.solution, dict) else {}
    stored_payload = _safe_exercise_solution_payload(stored_solution)
    inline_solution = manifest.get("solution") if isinstance(manifest.get("solution"), dict) else {}
    inline_payload = _safe_exercise_solution_payload(inline_solution)

    stored_answer = str(stored_payload.get("answer") or "").strip()
    inline_answer = str(inline_payload.get("answer") or "").strip()
    generic_answer_markers = (
        "reference approach:",
        "a strong solution should",
        "implement ",
        "protected reference solution is stored",
        "required implementation evidence includes",
        "this exercise checks",
    )
    stored_answer_is_generic = not stored_answer or any(
        marker in stored_answer.lower() for marker in generic_answer_markers
    )
    if inline_answer and stored_answer_is_generic:
        return {"exercise_slug": exercise_slug, **inline_payload}

    if any(stored_payload.get(key) for key in ("answer", "explanation", "expected_result", "steps", "test_cases")):
        if "protected reference solution is stored" not in str(stored_payload.get("explanation", "")).lower():
            return {"exercise_slug": exercise_slug, **stored_payload}

    if any(inline_payload.get(key) for key in ("answer", "explanation", "expected_result", "steps", "test_cases")):
        return {"exercise_slug": exercise_slug, **inline_payload}
    raise HTTPException(status_code=404, detail="A worked solution has not been authored for this exercise yet.")


@app.post("/api/me/exercises/{course_slug}/{lesson_slug}/{exercise_slug}/submit")
def submit_exercise(
    course_slug: str,
    lesson_slug: str,
    exercise_slug: str,
    body: ExerciseSubmission,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    exercise = find_published_exercise(db, course_slug, lesson_slug, exercise_slug)
    require_exercise_access(db, user, exercise)
    progress = db.scalar(
        select(ExerciseProgress).where(
            ExerciseProgress.user_id == user.id,
            ExerciseProgress.exercise_id == exercise.id,
        )
    )
    if progress is None:
        progress = ExerciseProgress(user_id=user.id, exercise_id=exercise.id)
        db.add(progress)
        db.flush()
    progress.attempts += 1
    progress.last_attempt_at = utc_now()
    correct = grade_exercise(exercise, body)
    # Review intervals update only from this server-side grading result; clients cannot submit correctness.
    record_review_result(db, user.id, course_slug, "exercise", exercise.slug, correct)
    xp_awarded = 0
    base_points = XP_REWARDS["exercise"]
    boost_applied = False
    newly_completed = correct and not progress.completed
    # Attempts count as learning activity; XP only arrives once, after a correct server-side check.
    record_activity_day(db, user.id, body.timezone)
    if correct:
        progress.completed = True
        progress.completed_at = progress.completed_at or utc_now()
        existing_xp = db.scalar(
            select(XPTransaction).where(
                XPTransaction.user_id == user.id,
                XPTransaction.source_type == "exercise_completed",
                XPTransaction.source_id == str(exercise.id),
            )
        )
        if newly_completed and existing_xp is None:
            base_points, xp_awarded, boost_applied = xp_award(db, user.id, "exercise")
            db.add(
                XPTransaction(
                    user_id=user.id,
                    source_type="exercise_completed",
                    source_id=str(exercise.id),
                    base_points=base_points,
                    awarded_points=xp_awarded,
                    boost_applied=boost_applied,
                )
            )
    db.commit()
    stats = user_gamification_stats(db, user.id, body.timezone)
    return {
        "ok": True,
        "correct": correct,
        "completed": progress.completed,
        "newly_completed": newly_completed,
        "attempts": progress.attempts,
        "base_xp": base_points,
        "xp_awarded": xp_awarded,
        "stats": stats,
    }


@app.put("/api/me/bookmarks/{course_slug}/{lesson_slug}")
def create_bookmark(
    course_slug: str,
    lesson_slug: str,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    lesson = find_published_lesson(db, course_slug, lesson_slug)
    bookmark = db.scalar(
        select(Bookmark).where(
            Bookmark.user_id == user.id, Bookmark.lesson_id == lesson.id
        )
    )
    if bookmark is None:
        bookmark = Bookmark(user_id=user.id, lesson_id=lesson.id)
        db.add(bookmark)
        db.commit()
    return {"ok": True, "lesson_slug": lesson_slug, "bookmarked": True}


@app.delete("/api/me/bookmarks/{course_slug}/{lesson_slug}")
def delete_bookmark(
    course_slug: str,
    lesson_slug: str,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    lesson = find_published_lesson(db, course_slug, lesson_slug)
    bookmark = db.scalar(
        select(Bookmark).where(
            Bookmark.user_id == user.id, Bookmark.lesson_id == lesson.id
        )
    )
    if bookmark is not None:
        db.delete(bookmark)
        db.commit()
    return {"ok": True, "lesson_slug": lesson_slug, "bookmarked": False}


@app.get("/api/me/bookmarks")
def list_bookmarks(
    user: User = Depends(require_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    rows = db.execute(
        select(Bookmark, Lesson, Course.slug)
        .join(Lesson, Bookmark.lesson_id == Lesson.id)
        .join(Module, Lesson.module_id == Module.id)
        .join(Course, Module.course_id == Course.id)
        .where(Bookmark.user_id == user.id)
        .order_by(Bookmark.created_at.desc())
    ).all()
    return {
        "items": [
            {
                "id": str(bookmark.id),
                "lesson_id": str(lesson.id),
                "course_slug": course_slug,
                "lesson_slug": lesson.slug,
                "title": lesson.title,
                "created_at": bookmark.created_at.isoformat(),
            }
            for bookmark, lesson, course_slug in rows
        ]
    }


@app.get("/api/me/certificates")
def list_certificates(
    user: User = Depends(require_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    rows = db.execute(
        select(Certificate, Course.slug, Course.title)
        .join(Course, Certificate.course_id == Course.id)
        .where(Certificate.user_id == user.id, Certificate.revoked_at.is_(None))
        .order_by(Certificate.issued_at.desc())
    ).all()
    return {
        "items": [
            {
                "public_id": certificate.public_id,
                "course_id": str(certificate.course_id),
                "course_slug": course_slug,
                "course_title": course_title,
                "issued_at": certificate.issued_at.isoformat(),
            }
            for certificate, course_slug, course_title in rows
        ]
    }


def _build_certificate_pdf(
    recipient_name: str, course_title: str, public_id: str, issued_at: datetime
) -> bytes:
    """Build a downloadable, one-page PDF credential using reportlab."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.pdfgen import canvas

    output = BytesIO()
    page_width, page_height = landscape(A4)
    pdf = canvas.Canvas(output, pagesize=(page_width, page_height), pageCompression=0)
    pdf.setTitle(f"CodeLeaf Certificate - {course_title}")
    pdf.setAuthor("CodeLeaf")
    pdf.setSubject(f"Verified learning credential {public_id}")

    dark = colors.HexColor("#183A32")
    green = colors.HexColor("#087D5C")
    muted = colors.HexColor("#507568")
    border = colors.HexColor("#A3CDBF")
    paper = colors.HexColor("#EDF8F3")
    pdf.setFillColor(paper)
    pdf.rect(0, 0, page_width, page_height, fill=1, stroke=0)
    pdf.setStrokeColor(border)
    pdf.setLineWidth(3)
    pdf.rect(18, 18, page_width - 36, page_height - 36, fill=0, stroke=1)
    pdf.setLineWidth(1)
    pdf.rect(27, 27, page_width - 54, page_height - 54, fill=0, stroke=1)

    def centered_lines(value: str, y: float, font: str, size: float, max_width: float, color) -> float:
        safe_text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
        words = safe_text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if current and stringWidth(candidate, font, size) > max_width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        pdf.setFillColor(color)
        pdf.setFont(font, size)
        for line in lines[:3]:
            pdf.drawCentredString(page_width / 2, y, line)
            y -= size * 1.35
        return y

    pdf.setFillColor(green)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString(page_width / 2, page_height - 63, "CODELEAF  |  VERIFIED LEARNING")
    pdf.setStrokeColor(border)
    pdf.line(82, page_height - 78, page_width - 82, page_height - 78)

    y = page_height - 132
    y = centered_lines("CERTIFICATE OF ACHIEVEMENT", y, "Helvetica-Bold", 10, page_width - 150, green) - 10
    y = centered_lines("Certificate of Completion", y, "Helvetica-Bold", 27, page_width - 150, dark) - 15
    y = centered_lines("This certificate is proudly presented to", y, "Helvetica", 12, page_width - 150, muted) - 8
    y = centered_lines(recipient_name or "CodeLeaf learner", y, "Helvetica-Bold", 24, page_width - 170, green) - 12
    pdf.setStrokeColor(border)
    pdf.line(page_width / 2 - 105, y, page_width / 2 + 105, y)
    y -= 26
    y = centered_lines("for completing the published learning requirements and passing the", y, "Helvetica", 11, page_width - 150, muted)
    y = centered_lines("required theoretical and practical certification assessments for", y - 2, "Helvetica", 11, page_width - 150, muted) - 7
    y = centered_lines(course_title, y, "Helvetica-Bold", 17, page_width - 170, dark) - 15
    y = centered_lines("Issued after verification by the CodeLeaf certification service", y, "Helvetica", 9, page_width - 150, green) - 24

    footer_y = 66
    pdf.setStrokeColor(border)
    pdf.line(58, footer_y + 28, page_width - 58, footer_y + 28)
    pdf.setFillColor(muted)
    pdf.setFont("Helvetica-Bold", 7)
    pdf.drawString(70, footer_y + 10, "DATE ISSUED")
    pdf.drawString(280, footer_y + 10, "CREDENTIAL ID")
    pdf.setFillColor(dark)
    pdf.setFont("Helvetica", 9)
    try:
        formatted_date = issued_at.strftime("%d %B %Y")
    except (AttributeError, ValueError):
        formatted_date = "Date unavailable"
    pdf.drawString(70, footer_y - 5, formatted_date)
    pdf.setFont("Courier", 8)
    pdf.drawString(280, footer_y - 5, str(public_id))
    pdf.setFillColor(green)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawRightString(page_width - 70, footer_y - 5, "VERIFIED CREDENTIAL")
    pdf.setFillColor(muted)
    pdf.setFont("Helvetica", 7)
    pdf.drawCentredString(page_width / 2, 37, "Keep the credential ID to verify this certificate on CodeLeaf.")
    pdf.showPage()
    pdf.save()
    return output.getvalue()


@app.get("/api/me/certificates/{public_id}/download")
def download_my_certificate(
    public_id: str,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> Response:
    """Download an active certificate as a PDF, scoped to its authenticated owner."""
    row = db.execute(
        select(Certificate, Course.slug, Course.title)
        .join(Course, Certificate.course_id == Course.id)
        .where(
            Certificate.public_id == public_id,
            Certificate.user_id == user.id,
            Certificate.revoked_at.is_(None),
        )
        .limit(1)
    ).first()
    # Use the same not-found response for unknown, revoked, and another user's ID.
    if row is None:
        raise HTTPException(
            status_code=404,
            detail="This certificate is not available for the signed-in account.",
        )
    certificate, course_slug, course_title = row
    pdf_bytes = _build_certificate_pdf(
        user.display_name or "CodeLeaf learner",
        course_title,
        certificate.public_id,
        certificate.issued_at,
    )
    safe_slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", str(course_slug)).strip("-") or "course"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="CodeLeaf-{safe_slug}-certificate.pdf"',
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.get("/api/me/certificates/{public_id}")
def get_my_certificate(
    public_id: str,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return printable certificate details only to the learner who owns it."""
    row = db.execute(
        select(Certificate, Course.slug, Course.title)
        .join(Course, Certificate.course_id == Course.id)
        .where(
            Certificate.public_id == public_id,
            Certificate.user_id == user.id,
            Certificate.revoked_at.is_(None),
        )
        .limit(1)
    ).first()
    # Use the same not-found response for unknown, revoked, and other users' IDs.
    if row is None:
        raise HTTPException(
            status_code=404,
            detail="This certificate is not available for the signed-in account.",
        )
    certificate, course_slug, course_title = row
    return {
        "valid": True,
        "public_id": certificate.public_id,
        "recipient_name": user.display_name,
        "course_id": str(certificate.course_id),
        "course_slug": course_slug,
        "course_title": course_title,
        "issued_at": certificate.issued_at.isoformat(),
    }


@app.get("/api/me/certificate-eligibility")
def list_my_certificate_eligibility(
    user: User = Depends(require_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Return learner progress even when that course's certification exam is not ready."""
    items: list[dict[str, Any]] = []
    tracks = {str(item.get("slug") or ""): item for item in PUBLIC_COURSES if item.get("slug")}
    for slug, track in tracks.items():
        entry: dict[str, Any] = {
            "course_slug": slug,
            "course_title": str(track.get("title") or slug.title()),
            "available": False,
            "start_exam_available": False,
            "status": "course_not_published",
            "total_lessons": None,
            "completed_lessons": None,
            "missing_lessons": None,
            "lessons_complete": False,
            "total_exercises": None,
            "completed_exercises": None,
            "missing_exercises": None,
            "exercises_complete": False,
            "message": "The course content has not been published to the learner catalog.",
        }

        # Progress and exam publication are separate concerns. Calculate completion
        # as soon as the course itself is available, so a missing/unpublished exam
        # blueprint cannot hide the learner's lesson and exercise actions.
        try:
            course = get_course_visible_to_reader(db, slug)
            progress = _course_progress_requirements(db, user, course)
            entry.update(progress)
            entry["course_available"] = True
        except HTTPException as exc:
            detail = exc.detail
            entry["message"] = (
                str(detail.get("message") or "The course progress is unavailable.")
                if isinstance(detail, dict)
                else str(detail or "The course progress is unavailable.")
            )
            if exc.status_code == 500:
                entry["status"] = "configuration_error"
            items.append(entry)
            continue

        try:
            _course, course_dir, blueprint = _load_exam_blueprint(slug, db)
            readiness = _exam_bank_readiness(course_dir, blueprint)
            practical_ready = False
            try:
                _load_practical_exam(course_dir)
                practical_ready = True
            except HTTPException:
                practical_ready = False
            latest_attempt = db.scalar(
                select(ExamAttempt)
                .where(
                    ExamAttempt.user_id == user.id,
                    ExamAttempt.course_id == course.id,
                    ExamAttempt.submitted_at.is_not(None),
                )
                .order_by(ExamAttempt.submitted_at.desc())
                .limit(1)
            )
            certificate = db.scalar(
                select(Certificate).where(
                    Certificate.user_id == user.id,
                    Certificate.course_id == course.id,
                    Certificate.revoked_at.is_(None),
                ).order_by(Certificate.issued_at.desc()).limit(1)
            )
            entry.update({
                "available": bool(readiness["ready"] and practical_ready),
                "mcq_ready": bool(readiness["ready"]),
                "valid_question_count": readiness["valid_question_count"],
                "distinct_question_count": readiness["distinct_prompt_count"],
                "required_question_count": 80,
                "practical_exam_available": practical_ready,
                "start_exam_available": bool(
                    progress["prerequisites_complete"] and readiness["ready"] and practical_ready
                ),
                "certificate_issued": certificate is not None,
                "status": "issued" if certificate else (
                    "prerequisites_incomplete" if not progress["prerequisites_complete"] else
                    "question_bank_incomplete" if not readiness["ready"] else
                    "practical_exam_unavailable" if not practical_ready else
                    "exam_required" if not latest_attempt else
                    "exam_passed" if latest_attempt.passed else "exam_not_passed"
                ),
                "message": (
                    "Certificate issued." if certificate else
                    "Complete all required lessons and exercises before starting the exam." if not progress["prerequisites_complete"] else
                    f"The MCQ bank needs 80 distinct valid questions; {readiness['distinct_prompt_count']} are available." if not readiness["ready"] else
                    "The practical certification stage has not been published." if not practical_ready else
                    "Start the certification exam." if latest_attempt is None else
                    "The latest MCQ attempt passed." if latest_attempt.passed else
                    "The latest MCQ attempt did not pass; review and retry."
                ),
            })
            if latest_attempt is not None:
                detailed = _certificate_eligibility_payload(
                    db, user, course, blueprint, latest_attempt, issue_if_eligible=False
                )
                entry["certificate_status"] = detailed["status"]
                entry["certificate_message"] = detailed["message"]
        except HTTPException as exc:
            detail = exc.detail
            message = (
                str(detail.get("message") or "The certification track is not ready.")
                if isinstance(detail, dict)
                else str(detail or "The certification track is not ready.")
            )
            entry["message"] = message
            if exc.status_code == 500:
                entry["status"] = "configuration_error"
            elif exc.status_code == 404:
                entry["status"] = "publication_required"
            entry["mcq_ready"] = False
            entry["practical_exam_available"] = False
            entry["start_exam_available"] = False
        items.append(entry)
    return {"items": items}


@app.get("/api/me/certificate-eligibility/{course_slug}")
def get_certificate_eligibility(
    course_slug: str, user: User = Depends(require_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    course = get_course_visible_to_reader(db, course_slug)
    _course, _course_dir, blueprint = _load_exam_blueprint(course_slug, db)
    attempt = db.scalar(
        select(ExamAttempt)
        .where(
            ExamAttempt.user_id == user.id,
            ExamAttempt.course_id == course.id,
            ExamAttempt.submitted_at.is_not(None),
        )
        .order_by(ExamAttempt.submitted_at.desc())
    )
    return _certificate_eligibility_payload(
        db, user, course, blueprint, attempt, issue_if_eligible=False
    )


@app.get("/api/certificates/verify/{public_id}")
def verify_certificate(public_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    certificate = db.scalar(
        select(Certificate).where(Certificate.public_id == public_id)
    )
    if not certificate or certificate.revoked_at:
        raise HTTPException(
            status_code=404, detail="Certificate not found or no longer valid."
        )
    return {
        "valid": True,
        "certificate_id": certificate.public_id,
        "issued_at": certificate.issued_at.isoformat(),
    }
