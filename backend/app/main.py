from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time
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
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from .config import settings
from .auth_security import require_user, user_payload, TOKEN_ALGORITHM
from .auth_routes import router as auth_router
from .phase5_routes import router as phase5_router
from .phase5_service import record_review_result
from .diagram_assets import validate_dynamic_diagram_model
from .db import engine, get_db
from .project_guide_service import build_project_guide, is_protected_project_path, project_guide_zip
from .models import (
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
logger = logging.getLogger("codeleaf.api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
)


@app.exception_handler(SQLAlchemyError)
async def handle_database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Return a bounded, non-sensitive response for database/query/pool failures."""
    logger.error(
        "Database request failed: %s %s (%s)",
        request.method,
        request.url.path,
        type(exc).__name__,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return JSONResponse(
        status_code=503,
        content={
            "detail": "The database request failed or timed out. Check backend logs and /api/ready, then retry."
        },
    )


@app.middleware("http")
async def enforce_allowed_origin(request: Request, call_next):
    # Origin validation plus a signed double-submit token protects cookie-authenticated writes.
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path != "/api/payments/webhook":
        origin = request.headers.get("origin")
        if origin and origin.rstrip("/") not in settings.allowed_origins:
            return JSONResponse(status_code=403, content={"detail": "Request origin is not allowed."})
        session_cookie = request.cookies.get("codeleaf_session")
        if session_cookie:
            csrf_cookie = request.cookies.get("codeleaf_csrf", "")
            csrf_header = request.headers.get("x-csrf-token", "")
            try:
                claims = jwt.decode(session_cookie, settings.jwt_secret, algorithms=[TOKEN_ALGORITHM])
                csrf_claim = claims.get("csrf", "")
            except jwt.InvalidTokenError:
                csrf_claim = ""
            if (not origin or origin.rstrip("/") not in settings.allowed_origins or not csrf_cookie
                    or not csrf_header or not csrf_claim
                    or not hmac.compare_digest(csrf_cookie, csrf_header)
                    or not hmac.compare_digest(csrf_cookie, csrf_claim)):
                return JSONResponse(status_code=403, content={"detail": "CSRF validation failed. Refresh the page and try again."})
    return await call_next(request)


@app.middleware("http")
async def log_slow_api_requests(request: Request, call_next):
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.exception(
            "Unhandled API failure: %s %s after %.0f ms",
            request.method,
            request.url.path,
            elapsed_ms,
        )
        raise
    elapsed_ms = (time.perf_counter() - started) * 1000
    if request.url.path.startswith("/api/") and elapsed_ms >= 1500:
        logger.warning(
            "Slow API response: %s %s -> %s in %.0f ms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
    return response


app.include_router(auth_router)
app.include_router(phase5_router)


SESSION_COOKIE = "codeleaf_session"
TOKEN_ALGORITHM = "HS256"
# Award rules are owned by the backend and exposed read-only through /api/public/config.
XP_REWARDS = {"lesson": 20, "exercise": 20, "max_multiplier": 1.5}


# Integer INR subunits (paise) are fixed by the server; the browser never supplies an amount.
PLAN_CONFIG: dict[str, dict[str, Any]] = {
    "pro": {
        "title": "Pro",
        "amount_paise": 29_900,
        "currency": "INR",
        "kind": "subscription",
    },
    "max": {
        "title": "Max",
        "amount_paise": 69_900,
        "currency": "INR",
        "kind": "subscription",
    },
    "full_access": {
        "title": "Full Access",
        "amount_paise": 4_999_900,
        "currency": "INR",
        "kind": "order",
    },
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


def ensure_payment_config() -> tuple[str, str]:
    key_id, key_secret = settings.razorpay_key_id, settings.razorpay_key_secret
    if not key_id or not key_secret:
        raise HTTPException(
            status_code=503,
            detail="Razorpay is not configured. Add test-mode credentials to backend/.env.",
        )
    return key_id, key_secret


def active_entitlements(db: Session, user_id: UUID) -> list[Entitlement]:
    now = utc_now()
    rows = db.scalars(
        select(Entitlement).where(
            Entitlement.user_id == user_id, Entitlement.status == "active"
        )
    ).all()

    # SQLite returns naive datetimes even for timezone=True columns; PostgreSQL preserves timezone.
    def is_current(row: Entitlement) -> bool:
        if row.ends_at is None:
            return True  # Lifetime Full Access has no expiry.
        end = (
            row.ends_at.replace(tzinfo=timezone.utc)
            if row.ends_at.tzinfo is None
            else row.ends_at.astimezone(timezone.utc)
        )
        return end > now

    return [row for row in rows if is_current(row)]


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
    else:
        ent.status = "active"
        ent.ends_at = ends_at
    return ent


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
                if course_dir not in candidate.parents or candidate.suffix.lower() != ".json":
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

    rows = index_doc.get("references") or index_doc.get("sources") or index_doc.get("items") or []
    loaded_rows: list[dict[str, Any]] = []
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict):
                loaded_rows.append(row)
            elif isinstance(row, str):
                try:
                    candidate = (course_dir / row).resolve()
                    if course_dir not in candidate.parents or candidate.suffix.lower() != ".json":
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
        title = str(row.get("title") or row.get("name") or row.get("label") or "").strip()
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
        if metadata.get("status") not in {None, "published"} and not draft_course_preview_enabled():
            return empty
        course_meta = metadata.get("course") if isinstance(metadata.get("course"), dict) else {}
        def normalise(value: Any) -> list[str]:
            if isinstance(value, str):
                return [value.strip()] if value.strip() else []
            if isinstance(value, list):
                return [str(item).strip() for item in value if isinstance(item, (str, int, float)) and str(item).strip()]
            return []
        return {
            "audience": normalise(course_meta.get("audience") or metadata.get("audience")),
            "prerequisites": normalise(course_meta.get("prerequisites") or metadata.get("prerequisites")),
            "learning_outcomes": normalise(course_meta.get("learning_outcomes") or course_meta.get("outcomes") or metadata.get("learning_outcomes")),
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
        select(Course.slug, func.count(Exercise.id))
        .join(Module, Module.course_id == Course.id)
        .join(Lesson, Lesson.module_id == Module.id)
        .join(Exercise, Exercise.lesson_id == Lesson.id)
        .group_by(Course.slug)
    )
    if preview_mode:
        practice_query = practice_query.where(
            or_(
                and_(Course.published.is_(True), Lesson.is_published.is_(True), Exercise.is_published.is_(True)),
                Lesson.content["_codeleaf_course_slug"].as_string() == Course.slug,
            )
        )
    else:
        practice_query = practice_query.where(
            Course.published.is_(True), Lesson.is_published.is_(True), Exercise.is_published.is_(True)
        )
    practice_counts = {slug: int(count or 0) for slug, count in db.execute(practice_query).all()}
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
def list_course_references(course_slug: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return the learner-safe reference index for one visible course."""
    course = get_course_visible_to_reader(db, course_slug)
    course_dir = (COURSE_CONTENT_ROOT / course_slug).resolve()
    try:
        metadata_path = (course_dir / "course.json").resolve()
        if course_dir not in metadata_path.parents or not metadata_path.is_file():
            raise FileNotFoundError("Course manifest was not found.")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=404, detail="Course reference index was not found.") from exc

    reference_rel = metadata.get("reference_index") or "references/reference-index.json"
    index_path = (course_dir / str(reference_rel)).resolve()
    if course_dir not in index_path.parents or not index_path.is_file() or index_path.suffix.lower() != ".json":
        raise HTTPException(status_code=404, detail="Course reference index was not found.")
    try:
        index_doc = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Course reference index is invalid.") from exc
    if index_doc.get("status") not in {None, "published"} and not draft_course_preview_enabled():
        raise HTTPException(status_code=404, detail="This course reference index has not been published.")

    raw_items = index_doc.get("references") or index_doc.get("sources") or index_doc.get("items") or []
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
        if row.get("status") not in {None, "published"} and not draft_course_preview_enabled():
            continue
        title = str(row.get("title") or row.get("name") or row.get("label") or "").strip()
        url = str(row.get("url") or row.get("href") or "").strip()
        parsed = urlsplit(url)
        if not title or parsed.scheme not in {"http", "https"} or not parsed.netloc:
            continue
        supports = row.get("supports") or row.get("concepts") or row.get("topics") or row.get("description") or ""
        if isinstance(supports, list):
            supports = ", ".join(str(value) for value in supports if value)
        elif not isinstance(supports, str):
            supports = str(supports) if supports else ""
        generated_slug = re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-") or f"reference-{len(items) + 1}"
        reference_slug = str(row.get("slug") or generated_slug).strip()
        related_lessons = row.get("related_lesson_slugs") or row.get("related_lessons") or []
        if isinstance(related_lessons, str):
            related_lessons = [related_lessons]
        if not isinstance(related_lessons, list):
            related_lessons = []
        items.append({
            "slug": reference_slug,
            "title": title,
            "url": url,
            "publisher": str(row.get("publisher") or row.get("organization") or row.get("source") or "").strip(),
            "checked_on": str(row.get("checked_on") or index_doc.get("checked_on") or index_doc.get("version_checked_on") or index_doc.get("last_checked") or "").strip(),
            "source_type": str(row.get("source_type") or row.get("type") or "reference").strip(),
            "supports": supports,
            "explanation": str(row.get("explanation") or row.get("description") or supports).strip(),
            "example": str(row.get("example") or "").strip(),
            "related_lesson_slugs": [str(slug).strip() for slug in related_lessons if isinstance(slug, str) and slug.strip()],
        })
    return {
        "course_slug": course.slug,
        "course_title": course.title,
        "description": course.description,
        "checked_on": index_doc.get("checked_on") or index_doc.get("version_checked_on") or index_doc.get("last_checked") or "",
        "items": items,
    }


@app.get("/api/courses/{course_slug}/exercises")
def list_course_exercises(
    course_slug: str,
    limit: int = 100,
    offset: int = 0,
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
            Lesson.title,
            Module.title,
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
    rows = db.execute(query.order_by(Module.sort_order.asc(), Lesson.sort_order.asc(), Exercise.sequence.asc()).limit(10_000)).all()
    items: list[dict[str, Any]] = []
    for (
        exercise,
        lesson_slug,
        lesson_title,
        module_title,
        course_title,
        course_is_published,
        lesson_is_published,
        lesson_content,
    ) in rows:
        published_item = bool(course_is_published and lesson_is_published and exercise.is_published)
        imported_draft = (
            preview_mode
            and isinstance(lesson_content, dict)
            and lesson_content.get("_codeleaf_course_slug") == course_slug
        )
        if not (published_item or imported_draft):
            continue
        items.append({
            "slug": exercise.slug,
            "title": exercise.title,
            "type": exercise.exercise_type,
            "prompt": exercise.prompt,
            "difficulty": exercise.difficulty,
            "course_slug": course_slug,
            "course_title": course_title,
            "module_title": module_title,
            "lesson_slug": lesson_slug,
            "lesson_title": lesson_title,
            "status": "published" if published_item else "draft",
            "sequence": exercise.sequence,
            "starter": exercise.starter or {},
            "hints": exercise.hints or [],
            "acceptance_criteria": exercise.acceptance_criteria or [],
            "xp_points": XP_REWARDS["exercise"],
        })
    total = len(items)
    return {"items": items[offset:offset + limit], "total": total, "offset": offset, "limit": limit, "preview_mode": preview_mode}


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
    if not isinstance(relative_path, str) or not relative_path.strip() or "\\" in relative_path or "\x00" in relative_path:
        raise HTTPException(status_code=404, detail=f"{label} was not found.")
    candidate = (course_dir / relative_path).resolve()
    if (
        course_dir.resolve() not in candidate.parents
        or candidate.suffix.lower() != ".json"
        or not candidate.is_file()
    ):
        raise HTTPException(status_code=404, detail=f"{label} was not found.")
    return candidate


def _load_exam_blueprint(course_slug: str, db: Session) -> tuple[Course, Path, dict[str, Any]]:
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
        raise HTTPException(status_code=500, detail="Course manifest is invalid.") from exc

    candidates = [
        item for item in course_manifest.get("assessment_files", [])
        if isinstance(item, str) and Path(item).name.lower() in {"exam-blueprint.json", "exam-blueprint"}
    ]
    if not candidates:
        candidates = ["exams/exam-blueprint.json"]
    blueprint_path = None
    for relative in candidates:
        try:
            blueprint_path = _safe_course_json_path(course_dir, relative, "Exam blueprint")
            break
        except HTTPException:
            continue
    if blueprint_path is None:
        raise HTTPException(status_code=404, detail="This course does not have a final exam blueprint.")
    try:
        blueprint = json.loads(blueprint_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Exam blueprint is invalid.") from exc
    if not isinstance(blueprint, dict):
        raise HTTPException(status_code=500, detail="Exam blueprint is invalid.")
    if course_manifest.get("status") == "draft" and not draft_course_preview_enabled():
        raise HTTPException(status_code=404, detail="This course has not been published.")
    if blueprint.get("status") != "published" and not draft_course_preview_enabled():
        raise HTTPException(status_code=404, detail="This final exam has not been published.")
    return course, course_dir, blueprint


def _load_exam_question_pool(course_dir: Path, blueprint: dict[str, Any]) -> list[dict[str, Any]]:
    """Load valid published question records. Private answer keys remain server-only."""
    question_files = blueprint.get("question_files", [])
    if not isinstance(question_files, list):
        raise HTTPException(status_code=500, detail="Exam question index is invalid.")
    preview = draft_course_preview_enabled()
    pool: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    topic_ranges: list[tuple[str, int, int]] = []
    for topic in blueprint.get("topic_distribution", []):
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
            topic_ranges.append((str(topic.get("topic") or "General skills"), start, end))

    for relative in question_files:
        if not isinstance(relative, str) or "\\" in relative:
            continue
        try:
            question_path = _safe_course_json_path(course_dir, str(Path("exams") / relative), "Exam question set")
        except HTTPException:
            continue
        try:
            question_set = json.loads(question_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=500, detail="An exam question set is invalid.") from exc
        if not isinstance(question_set, dict):
            raise HTTPException(status_code=500, detail="An exam question set is invalid.")
        if question_set.get("status") != "published" and not preview:
            continue
        lesson_id = question_set.get("lesson_id")
        lesson_slug = question_set.get("lesson_slug")
        import re
        match = re.search(r"(\d+)$", str(lesson_id or question_path.stem))
        lesson_number = int(match.group(1)) if match else 0
        topic_name = next(
            (name for name, start, end in topic_ranges if start <= lesson_number <= end),
            "General skills",
        )
        questions = question_set.get("questions")
        if not isinstance(questions, list):
            raise HTTPException(status_code=500, detail="An exam question set is malformed.")
        for question in questions:
            if not isinstance(question, dict):
                raise HTTPException(status_code=500, detail="An exam question is malformed.")
            question_id = question.get("id")
            prompt = question.get("prompt")
            options = question.get("options")
            answer_key = question.get("answer_key")
            if (
                not isinstance(question_id, str) or not question_id.strip()
                or question_id in seen_ids
                or not isinstance(prompt, str) or not prompt.strip()
                or not isinstance(options, list) or len(options) < 2
                or not all(isinstance(option, str) for option in options)
                or not isinstance(answer_key, str) or answer_key not in options
            ):
                raise HTTPException(status_code=500, detail="An exam question is malformed or has a duplicate ID.")
            seen_ids.add(question_id)
            pool.append({
                "id": question_id,
                "lesson_id": str(lesson_id or ""),
                "lesson_slug": str(lesson_slug or ""),
                "lesson_number": lesson_number,
                "topic": topic_name,
                "prompt": prompt,
                "options": options,
                "answer_key": answer_key,
                "explanation": str(question.get("explanation") or "Review the relevant lesson and try again."),
            })
    return pool


def _choose_exam_questions(pool: list[dict[str, Any]], blueprint: dict[str, Any], count: int = 20) -> list[dict[str, Any]]:
    """Sample unique lesson concepts according to the blueprint's topic weights."""
    if not pool:
        return []
    rng = secrets.SystemRandom()
    by_lesson: dict[int, list[dict[str, Any]]] = {}
    for question in pool:
        by_lesson.setdefault(int(question.get("lesson_number") or 0), []).append(question)
    lesson_numbers = [number for number in by_lesson if number > 0]
    rng.shuffle(lesson_numbers)
    target_count = min(max(1, int(count)), len(lesson_numbers))
    topics = []
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
    weighted_total = sum(row[3] for row in topics)
    selected: list[dict[str, Any]] = []
    selected_lessons: set[int] = set()
    if topics and weighted_total > 0:
        raw_quotas = [target_count * item[3] / weighted_total for item in topics]
        quotas = [int(value) for value in raw_quotas]
        remaining = target_count - sum(quotas)
        ranked = sorted(range(len(topics)), key=lambda i: raw_quotas[i] - quotas[i], reverse=True)
        for index in ranked[:remaining]:
            quotas[index] += 1
        for topic_row, quota in zip(topics, quotas):
            name, start, end, _weight = topic_row
            eligible = [number for number in lesson_numbers if number not in selected_lessons and start <= number <= end]
            rng.shuffle(eligible)
            for number in eligible[:quota]:
                choices = by_lesson[number]
                candidate = dict(rng.choice(choices))
                candidate["topic"] = name
                selected.append(candidate)
                selected_lessons.add(number)
    if len(selected) < target_count:
        remaining_lessons = [number for number in lesson_numbers if number not in selected_lessons]
        rng.shuffle(remaining_lessons)
        for number in remaining_lessons[: target_count - len(selected)]:
            selected.append(dict(rng.choice(by_lesson[number])))
    rng.shuffle(selected)
    return selected


def _course_requires_human_capstone_review(blueprint: dict[str, Any]) -> bool:
    description = str(blueprint.get("project_submission") or "").casefold()
    if re.search(r"\b(no|not|never|without)\b.{0,55}\b(capstone|human[- ]review(?:ed)?)\b", description):
        return False
    return "capstone" in description and bool(re.search(r"human[- ]review(?:ed)?", description))


def _certificate_eligibility_payload(
    db: Session, user: User, course: Course, blueprint: dict[str, Any],
    attempt: ExamAttempt | None, issue_if_eligible: bool = False,
) -> dict[str, Any]:
    lesson_rows = db.execute(
        select(Lesson.id, LessonProgress.completed)
        .join(Module, Lesson.module_id == Module.id)
        .outerjoin(
            LessonProgress,
            (LessonProgress.lesson_id == Lesson.id) & (LessonProgress.user_id == user.id),
        )
        .where(Module.course_id == course.id)
    ).all()
    total_lessons = len(lesson_rows)
    completed_lessons = sum(1 for _lesson_id, complete in lesson_rows if complete)
    certificate = db.scalar(
        select(Certificate).where(
            Certificate.user_id == user.id,
            Certificate.course_id == course.id,
            Certificate.revoked_at.is_(None),
        ).order_by(Certificate.issued_at.desc())
    )
    attempt_passed = bool(attempt and attempt.submitted_at and attempt.passed)
    capstone_required = _course_requires_human_capstone_review(blueprint)
    status_text = "exam_required"
    reason = "Pass the server-graded final exam first."
    if certificate:
        status_text, reason = "issued", "A verified certificate has been issued for this course."
    elif not attempt_passed:
        if attempt and attempt.submitted_at:
            status_text, reason = "exam_not_passed", "Review the result and pass the final exam to continue."
    elif total_lessons and completed_lessons < total_lessons:
        status_text, reason = "pending_course_completion", "Pass the exam and finish every required lesson to continue."
    elif capstone_required:
        status_text, reason = "pending_capstone_review", "The course blueprint requires human review of the capstone. The submission/review workflow is not implemented, so no completion certificate has been issued."
    else:
        status_text, reason = "eligible", "The backend verified the passing result and course completion."
        if issue_if_eligible:
            certificate = Certificate(
                public_id=secrets.token_hex(8).upper(),
                user_id=user.id,
                course_id=course.id,
                exam_attempt_id=attempt.id if attempt else None,
            )
            db.add(certificate)
            db.flush()
            status_text, reason = "issued", "A certificate was issued after backend-verified exam pass and course completion."
    return {
        "course_slug": course.slug,
        "course_title": course.title,
        "status": status_text,
        "eligible": status_text in {"eligible", "issued"},
        "exam_passed": attempt_passed,
        "score_percent": (attempt.answers_summary or {}).get("score_percent") if attempt else None,
        "completed_lessons": completed_lessons,
        "total_lessons": total_lessons,
        "capstone_review_required": capstone_required,
        "capstone_review_status": "pending_not_implemented" if capstone_required else "not_required",
        "certificate": ({"public_id": certificate.public_id, "issued_at": certificate.issued_at.isoformat()} if certificate else None),
        "message": reason,
    }


@app.get("/api/courses/{course_slug}/exam")
def get_course_exam_info(course_slug: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return safe exam metadata; no answer keys or explanations are included."""
    _course, course_dir, blueprint = _load_exam_blueprint(course_slug, db)
    pool = _load_exam_question_pool(course_dir, blueprint)
    available_lessons = len({item["lesson_number"] for item in pool if item["lesson_number"] > 0})
    if len(pool) < 1 or available_lessons < 1:
        raise HTTPException(status_code=409, detail="The exam has no published question bank yet.")
    settings_doc = blueprint.get("recommended_settings") or {}
    return {
        "course_slug": course_slug,
        "title": str(blueprint.get("title") or f"{course_slug.title()} Skills Assessment"),
        "duration_minutes": int(settings_doc.get("duration_minutes") or 60),
        "pass_percent": int(settings_doc.get("suggested_pass_percent") or 70),
        "question_count": min(20, available_lessons),
        "question_bank_count": len(pool),
        "status": "preview" if draft_course_preview_enabled() and blueprint.get("status") != "published" else "published",
    }


@app.post("/api/courses/{course_slug}/exam/start", status_code=status.HTTP_201_CREATED)
def start_course_exam(
    course_slug: str, user: User = Depends(require_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Create a private exam attempt and return only prompts/options."""
    course, course_dir, blueprint = _load_exam_blueprint(course_slug, db)
    pool = _load_exam_question_pool(course_dir, blueprint)
    picked = _choose_exam_questions(pool, blueprint, count=20)
    if not picked:
        raise HTTPException(status_code=409, detail="The exam has no published question bank yet.")
    recommended = blueprint.get("recommended_settings") or {}
    stored_questions = [
        {key: item[key] for key in ("id", "lesson_id", "lesson_slug", "lesson_number", "topic", "prompt", "options", "answer_key", "explanation")}
        for item in picked
    ]
    attempt = ExamAttempt(
        user_id=user.id,
        course_id=course.id,
        score=0,
        passed=False,
        answers_summary={
            "status": "in_progress",
            "course_slug": course_slug,
            "exam_title": str(blueprint.get("title") or f"{course_slug.title()} Skills Assessment"),
            "pass_percent": int(recommended.get("suggested_pass_percent") or 70),
            "duration_minutes": int(recommended.get("duration_minutes") or 60),
            "question_count": len(stored_questions),
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
        "question_count": len(stored_questions),
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
        select(ExamAttempt).where(ExamAttempt.id == parsed_id, ExamAttempt.user_id == user.id)
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
    if attempt.submitted_at:
        return {
            "attempt_id": str(attempt.id),
            "status": "submitted",
            "score": attempt.score,
            "passed": attempt.passed,
            **{key: value for key, value in summary.items() if key not in {"questions", "answer_key"}},
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
    attempt_id: str, payload: dict[str, Any],
    user: User = Depends(require_user), db: Session = Depends(get_db),
) -> dict[str, Any]:
    attempt = _find_owned_exam_attempt(attempt_id, user, db)
    if attempt.submitted_at:
        raise HTTPException(status_code=409, detail="This exam attempt has already been submitted.")
    summary = attempt.answers_summary or {}
    questions = summary.get("questions")
    answers = payload.get("answers") if isinstance(payload, dict) else None
    if not isinstance(questions, list) or not questions:
        raise HTTPException(status_code=409, detail="This exam attempt has no question set.")
    if not isinstance(answers, dict) or not answers:
        raise HTTPException(status_code=422, detail="Submit an answers object with one selected option per question.")
    question_by_id = {str(q.get("id")): q for q in questions if isinstance(q, dict)}
    if set(answers) != set(question_by_id):
        raise HTTPException(status_code=422, detail="Answer every exam question exactly once.")
    results: list[dict[str, Any]] = []
    correct_count = 0
    for question_id, question in question_by_id.items():
        selected = answers.get(question_id)
        if not isinstance(selected, str) or selected not in question.get("options", []):
            raise HTTPException(status_code=422, detail="Each exam answer must match one of the offered options.")
        correct = selected == question.get("answer_key")
        correct_count += int(correct)
        results.append({
            "question_id": question_id,
            "prompt": question.get("prompt", ""),
            "topic": question.get("topic", "General skills"),
            "lesson_slug": question.get("lesson_slug", ""),
            "selected_answer": selected,
            "is_correct": correct,
            "correct_answer": question.get("answer_key"),
            "explanation": question.get("explanation", "Review the relevant lesson and try again."),
        })
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
    course = db.get(Course, attempt.course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course was not found.")
    _same_course, _course_dir, blueprint = _load_exam_blueprint(course.slug, db)
    eligibility = _certificate_eligibility_payload(db, user, course, blueprint, attempt, issue_if_eligible=passed)
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
    if any(part in {".", ".."} for part in requested_parts) or Path(asset_path).is_absolute():
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
            validate_dynamic_diagram_model(target, f"public diagram {course_slug}/{asset_path}")
        except ValueError as exc:
            # Invalid files in the diagram directory are not public assets. Do not
            # return the file or its contents, and keep private JSON unavailable.
            raise HTTPException(status_code=404, detail="Course asset was not found.") from exc
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
        media_type="application/json" if is_dynamic_diagram else media_types[target.suffix.lower()],
        headers={"Cache-Control": "public, max-age=3600"},
    )


@app.get("/api/courses/{course_slug}/projects")
def list_published_course_projects(
    course_slug: str, db: Session = Depends(get_db)
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
                row for row in safe_item["starter_files"]
                if not is_protected_project_path(
                    row if isinstance(row, str) else (
                        row.get("path") or row.get("name") if isinstance(row, dict) else None
                    )
                )
            ]
        if is_protected_project_path(safe_item.get("starter_readme")):
            safe_item.pop("starter_readme", None)
        items.append(safe_item)
    items.sort(key=lambda item: item.get("sequence", 0))
    return {"items": items}




def _load_project_manifest_for_guide(
    course_slug: str, project_slug: str, db: Session
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    """Load one visible project manifest without opening protected solution files."""
    get_course_visible_to_reader(db, course_slug)
    content_root = COURSE_CONTENT_ROOT.resolve()
    course_dir = (content_root / course_slug).resolve()
    metadata_path = (course_dir / "course.json").resolve()
    # Keep the course slug inside the configured content root even if a crafted path
    # reaches this route; only real course directories may be inspected.
    if content_root not in course_dir.parents or course_dir not in metadata_path.parents or not metadata_path.is_file():
        raise HTTPException(status_code=404, detail="Course content was not found.")
    try:
        course_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Course project index is invalid.") from exc

    selected: dict[str, Any] | None = None
    project_files = course_metadata.get("project_files", [])
    if not isinstance(project_files, list):
        raise HTTPException(status_code=500, detail="Course project index is invalid.")
    for relative in project_files:
        if not isinstance(relative, str) or "\\" in relative:
            continue
        parts = Path(relative).parts
        # Never expose a solution file even if the course index is accidentally misconfigured.
        if any(part.lower() in {"solution", "solutions", "answer-keys", "answer_keys"} for part in parts):
            continue
        project_path = (course_dir / relative).resolve()
        if course_dir not in project_path.parents or project_path.suffix.lower() != ".json" or not project_path.is_file():
            continue
        try:
            project_doc = json.loads(project_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if project_doc.get("slug") == project_slug or project_doc.get("id") == project_slug:
            selected = project_doc
            break

    if selected is None:
        raise HTTPException(status_code=404, detail="Project guide was not found.")
    if selected.get("status") != "published" and not (
        draft_course_preview_enabled() and selected.get("status") == "draft"
    ):
        raise HTTPException(status_code=404, detail="Project guide is not published yet.")
    return course_dir, course_metadata, selected


@app.get("/api/courses/{course_slug}/projects/{project_slug}")
def get_published_course_project_guide(
    course_slug: str, project_slug: str, db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Return a complete learner-facing build guide and explicitly declared starter code."""
    course_dir, course_metadata, project_doc = _load_project_manifest_for_guide(course_slug, project_slug, db)
    return build_project_guide(course_slug, course_metadata, project_doc, course_dir)


@app.get("/api/courses/{course_slug}/projects/{project_slug}/starter-kit.zip")
def download_published_course_project_starter_kit(
    course_slug: str, project_slug: str, db: Session = Depends(get_db)
) -> Response:
    """Download learner-safe starter files; protected reference solutions are never included."""
    course_dir, course_metadata, project_doc = _load_project_manifest_for_guide(course_slug, project_slug, db)
    guide = build_project_guide(course_slug, course_metadata, project_doc, course_dir)
    archive_bytes = project_guide_zip(guide)
    raw_name = str(project_doc.get("slug") or project_doc.get("title") or "project")
    safe_name = "".join(char for char in raw_name if char.isalnum() or char in "-_")[:80] or "project"
    return Response(
        content=archive_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}-starter-kit.zip"'},
    )

@app.get("/api/courses/{course_slug}/projects/{project_slug}/starter-files/{file_id}")
def get_published_course_project_starter_file(
    course_slug: str,
    project_slug: str,
    file_id: str,
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

    if not isinstance(relative_file, str) or not relative_file or is_protected_project_path(relative_file):
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
    return {
        "items": [
            {
                "id": "free",
                "title": "Free",
                "amount_paise": 0,
                "currency": "INR",
                "billing": "free",
            },
            {
                "id": "pro",
                "title": "Pro",
                "amount_paise": 29_900,
                "currency": "INR",
                "billing": "monthly",
            },
            {
                "id": "max",
                "title": "Max",
                "amount_paise": 69_900,
                "currency": "INR",
                "billing": "monthly",
            },
            {
                "id": "full_access",
                "title": "Full Access",
                "amount_paise": 4_999_900,
                "currency": "INR",
                "billing": "lifetime",
            },
        ]
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
    return {
        "user": user_payload(user),
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
    key_id, _ = ensure_payment_config()
    plan = PLAN_CONFIG[body.plan_id]
    current_entitlements = active_entitlements(db, user.id)
    if current_entitlements:
        current_names = sorted(
            {e.plan_id.replace("_", " ").title() for e in current_entitlements}
        )
        raise HTTPException(
            status_code=409,
            detail=f"This account already has active access ({', '.join(current_names)}). Manage or wait for that membership to end before starting another paid plan.",
        )
    if body.plan_id == "full_access":
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
        return {
            "kind": "order",
            "key_id": key_id,
            "order_id": provider["id"],
            "amount": plan["amount_paise"],
            "currency": "INR",
            "name": "CodeLeaf",
            "description": "Full Access — lifetime platform access",
            "prefill": {"email": user.email, "name": user.display_name},
        }

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
    return {
        "kind": "subscription",
        "key_id": key_id,
        "subscription_id": provider["id"],
        "plan_id": body.plan_id,
        "name": "CodeLeaf",
        "description": f"{plan['title']} monthly membership",
        "prefill": {"email": user.email, "name": user.display_name},
        "status": provider.get("status", "created"),
        "billing_cycles": total_count,
    }


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
    records = db.scalars(
        select(PaymentRecord)
        .where(PaymentRecord.user_id == user.id, PaymentRecord.kind == "subscription")
        .order_by(PaymentRecord.created_at.desc())
    ).all()
    entitlement_by_subscription = {
        e.provider_subscription_id: e
        for e in entitlements
        if e.provider_subscription_id
    }
    terminal = {"cancelled", "completed", "expired"}
    return {
        "entitlements": [
            {
                "plan_id": e.plan_id,
                "status": e.status,
                "ends_at": e.ends_at.isoformat() if e.ends_at else None,
            }
            for e in entitlements
        ],
        "subscriptions": [
            {
                "subscription_id": r.provider_subscription_id,
                "plan_id": r.plan_id,
                "status": r.status,
                "amount_paise": r.amount_paise,
                "ends_at": (
                    entitlement_by_subscription.get(
                        r.provider_subscription_id
                    ).ends_at.isoformat()
                    if entitlement_by_subscription.get(r.provider_subscription_id)
                    and entitlement_by_subscription[r.provider_subscription_id].ends_at
                    else None
                ),
                "cancelable": bool(
                    r.provider_subscription_id and r.status.lower() not in terminal
                ),
            }
            for r in records
            if r.provider_subscription_id
        ],
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
    if record.status.lower() in {"cancelled", "completed", "expired"}:
        raise HTTPException(
            status_code=409,
            detail="This subscription is already cancelled or completed.",
        )
    provider = await razorpay_request(
        "POST", f"/subscriptions/{subscription_id}/cancel", {"cancel_at_cycle_end": 1}
    )
    record.status = provider.get("status", "cancelled")
    db.commit()
    return {
        "ok": True,
        "status": record.status,
        "message": "Cancellation was requested at the end of the current billing cycle.",
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

    event_name = payload.get("event")
    entities = payload.get("payload") or {}
    order_entity = (entities.get("order") or {}).get("entity") or {}
    payment_entity = (entities.get("payment") or {}).get("entity") or {}
    subscription_entity = (entities.get("subscription") or {}).get("entity") or {}

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
            and int(amount or 0) == record.amount_paise
            and currency == "INR"
        ):
            record.status = "paid"
            if payment_entity.get("id"):
                record.provider_payment_id = payment_entity["id"]
            grant_entitlement(
                db, user_id=record.user_id, plan_id="full_access", payment_record=record
            )
    elif event_name in {
        "subscription.activated",
        "subscription.charged",
        "subscription.updated",
        "subscription.cancelled",
        "subscription.halted",
        "subscription.paused",
        "subscription.resumed",
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
            provider_status = str(
                subscription_entity.get("status", event_name.split(".")[-1])
            )
            record.status = provider_status
            existing = db.scalar(
                select(Entitlement).where(
                    Entitlement.provider_subscription_id == sub_id,
                    Entitlement.user_id == record.user_id,
                )
            )
            period_end = parse_epoch(subscription_entity.get("current_end"))
            if (
                (
                    event_name
                    in {
                        "subscription.activated",
                        "subscription.charged",
                        "subscription.resumed",
                    }
                    or provider_status == "active"
                )
                and provider_status == "active"
                and period_end is not None
            ):
                grant_entitlement(
                    db,
                    user_id=record.user_id,
                    plan_id=record.plan_id,
                    payment_record=record,
                    subscription_id=sub_id,
                    ends_at=period_end,
                )
            elif existing:
                existing.ends_at = (
                    parse_epoch(subscription_entity.get("current_end"))
                    or existing.ends_at
                )
                existing.cancelled_at = (
                    utc_now()
                    if event_name == "subscription.cancelled"
                    else existing.cancelled_at
                )
                if event_name in {"subscription.halted", "subscription.paused"}:
                    existing.status = (
                        "past_due" if event_name == "subscription.halted" else "paused"
                    )
                elif event_name == "subscription.cancelled" and (
                    not existing.ends_at or existing.ends_at <= utc_now()
                ):
                    existing.status = "cancelled"
    elif event_name == "payment.failed" and payment_entity.get("order_id"):
        record = db.scalar(
            select(PaymentRecord).where(
                PaymentRecord.provider_order_id == payment_entity.get("order_id")
            )
        )
        if record and record.status != "paid":
            record.status = "failed"

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
    period: str = "week", limit: int = 20, db: Session = Depends(get_db)
) -> dict[str, Any]:
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
    published_lesson_count = db.scalar(select(func.count(Lesson.id)).join(
        Module, Module.id == Lesson.module_id
    ).where(Module.course_id == course_id, Lesson.is_published.is_(True))) or 0
    completed_lesson_count = db.scalar(select(func.count(LessonProgress.id)).join(
        Lesson, LessonProgress.lesson_id == Lesson.id
    ).join(Module, Module.id == Lesson.module_id).where(
        LessonProgress.user_id == user.id, LessonProgress.completed.is_(True),
        Module.course_id == course_id, Lesson.is_published.is_(True)
    )) or 0
    course_completed_now = bool(newly_completed and published_lesson_count > 0 and completed_lesson_count >= published_lesson_count)
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


@app.get("/api/exercises/featured")
def list_featured_exercises(
    limit: int = 12, db: Session = Depends(get_db)
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
        # Never expose the grader, solution or answer key in this learner-facing list.
        visible_items.append(
            {
                "slug": exercise.slug,
                "title": exercise.title,
                "type": exercise.exercise_type,
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
    course_slug: str, lesson_slug: str, db: Session = Depends(get_db)
) -> dict[str, Any]:
    lesson = find_published_lesson(db, course_slug, lesson_slug)
    exercise_query = select(Exercise).where(Exercise.lesson_id == lesson.id)
    if not draft_course_preview_enabled():
        exercise_query = exercise_query.where(Exercise.is_published.is_(True))
    rows = db.scalars(exercise_query.order_by(Exercise.sequence.asc())).all()
    return {
        "items": [
            {
                "slug": item.slug,
                "title": item.title,
                "type": item.exercise_type,
                "prompt": item.prompt,
                "starter": item.starter,
                "public_tests": item.public_tests,
                "acceptance_criteria": item.acceptance_criteria,
                "hints": item.hints,
                "sequence": item.sequence,
                "difficulty": item.difficulty,
                "xp_points": XP_REWARDS["exercise"],
            }
            for item in rows
        ]
    }


@app.get("/api/courses/{course_slug}/lessons/{lesson_slug}/exercises/{exercise_slug}/solution")
def reveal_exercise_solution(
    course_slug: str,
    lesson_slug: str,
    exercise_slug: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Reveal an authored solution only on explicit request for a visible exercise.

    Normal exercise listings never contain solutions or grading configuration.
    The response is whitelisted so protected grading keys can never leak here.
    """
    exercise = find_published_exercise(db, course_slug, lesson_slug, exercise_slug)
    solution_doc: dict[str, Any] = {}
    embedded = exercise.solution if isinstance(exercise.solution, dict) else {}
    if embedded:
        solution_doc = embedded

    course_root = (COURSE_CONTENT_ROOT / course_slug).resolve()
    try:
        if COURSE_CONTENT_ROOT.resolve() not in course_root.parents:
            raise HTTPException(status_code=404, detail="Exercise solution was not found.")
        # Resolve the authored source manifest by slug; do not accept a user-supplied path.
        source_manifest: dict[str, Any] | None = None
        source_path: Path | None = None
        for candidate in course_root.rglob("exercises/*.json"):
            if candidate.parent.name != "exercises" or "solutions" in candidate.parts:
                continue
            try:
                item = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(item, dict) or item.get("slug") != exercise_slug:
                continue
            if item.get("lesson_slug") and item.get("lesson_slug") != lesson_slug:
                continue
            # Access is already gated by find_published_exercise above. Content manifests
            # may remain draft while a reviewed database record is published, so the
            # explicit reveal action follows the visible database record's permissions.
            source_manifest, source_path = item, candidate
            break

        if source_manifest and source_path:
            solution_relative = source_manifest.get("solution_file")
            if isinstance(solution_relative, str) and solution_relative.strip() and "\\" not in solution_relative and "\x00" not in solution_relative:
                exercises_root = source_path.parent.resolve()
                module_root = exercises_root.parent.resolve()
                solution_path = (exercises_root / solution_relative).resolve()
                allowed_roots = (
                    (module_root / "solutions").resolve(),
                    (exercises_root / "solutions").resolve(),
                )
                allowed_solution = any(
                    solution_path == root or root in solution_path.parents
                    for root in allowed_roots
                )
                if allowed_solution and module_root in solution_path.parents and solution_path.suffix.lower() == ".json" and solution_path.is_file():
                    loaded = json.loads(solution_path.read_text(encoding="utf-8"))
                    if isinstance(loaded, dict):
                        solution_doc = loaded
            if not solution_doc:
                direct = source_manifest.get("solution")
                if isinstance(direct, dict):
                    solution_doc = direct
    except (OSError, json.JSONDecodeError, ValueError):
        # A broken/missing authored solution should not break the exercise itself.
        solution_doc = {}

    answer = solution_doc.get("answer") or solution_doc.get("code") or solution_doc.get("solution")
    explanation = solution_doc.get("explanation") or solution_doc.get("notes") or solution_doc.get("description") or ""
    expected_result = solution_doc.get("expected_result") or solution_doc.get("expected_output") or ""
    steps = solution_doc.get("steps") if isinstance(solution_doc.get("steps"), list) else []
    steps = steps or (solution_doc.get("manual_validation_checklist") if isinstance(solution_doc.get("manual_validation_checklist"), list) else [])
    test_cases = solution_doc.get("test_cases") if isinstance(solution_doc.get("test_cases"), list) else []
    if not any((answer, explanation, expected_result, steps, test_cases)):
        raise HTTPException(status_code=404, detail="A worked solution has not been authored for this exercise yet.")
    return {
        "slug": exercise.slug,
        "title": exercise.title,
        "answer": answer if isinstance(answer, (str, int, float, list, dict)) else "",
        "explanation": str(explanation) if explanation else "",
        "expected_result": str(expected_result) if expected_result else "",
        "steps": [str(step) for step in steps if isinstance(step, (str, int, float))],
        "test_cases": [
            {key: str(case.get(key, "")) for key in ("input", "expected") if key in case}
            for case in test_cases if isinstance(case, dict)
        ],
    }


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


@app.get("/api/me/certificate-eligibility/{course_slug}")
def get_certificate_eligibility(
    course_slug: str, user: User = Depends(require_user), db: Session = Depends(get_db)
) -> dict[str, Any]:
    course = get_course_visible_to_reader(db, course_slug)
    _course, _course_dir, blueprint = _load_exam_blueprint(course_slug, db)
    attempt = db.scalar(
        select(ExamAttempt)
        .where(ExamAttempt.user_id == user.id, ExamAttempt.course_id == course.id, ExamAttempt.submitted_at.is_not(None))
        .order_by(ExamAttempt.submitted_at.desc())
    )
    return _certificate_eligibility_payload(db, user, course, blueprint, attempt, issue_if_eligible=False)


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
