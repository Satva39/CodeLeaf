"""Phase 5 APIs: transparent learning recommendations, portfolios, editor staging,
privacy-minimized analytics, and an authenticated gateway to a separate runner.

The content studio keeps immutable staging revisions in PostgreSQL. It deliberately
does not write files from an HTTP request; releasing a revision into learner-facing
course manifests still requires the existing validated importer/release workflow.
"""
from __future__ import annotations

import io
import json
import re
import tempfile
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Literal
from urllib.parse import urlsplit
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, Response, UploadFile, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select, delete, update
from sqlalchemy.orm import Session

from .auth_security import require_user
from .config import settings
from .db import SessionLocal, get_db
from .models import (
    AuditLog, ContentRevision, Course, Exercise, ExerciseProgress, Lesson,
    LessonProgress, LearningPreference, Module, ProductAnalyticsEvent,
    Certificate, ProjectSubmission, ProjectSubmissionZipChunk, ReviewSchedule, RunnerJob, User,
)
from .phase5_service import apply_review_rating, get_or_create_preferences, utc_now
from .plan_entitlements import (
    effective_plan_id,
    ensure_storage_capacity,
    finalize_daily_usage,
    plan_limits,
    require_feature,
    reserve_daily_usage,
)
from .diagram_assets import validate_dynamic_diagram_model

router = APIRouter()
COURSE_CONTENT_ROOT = Path(__file__).resolve().parents[1] / "content" / "courses"
ROADMAP_FILE = Path(__file__).resolve().parents[1] / "content" / "career-roadmaps.json"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,179}$")
COURSE_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,99}$")
MAX_PROJECT_ZIP_BYTES = 500 * 1024 * 1024
MAX_PROJECT_ZIP_FILES = 10_000
MAX_PROJECT_ZIP_FILE_BYTES = 500 * 1024 * 1024
MAX_PROJECT_ZIP_UNCOMPRESSED_BYTES = 1024 * 1024 * 1024
PROJECT_ZIP_CHUNK_BYTES = 1024 * 1024
# Keep individual browser-to-Vercel-function payloads comfortably below Vercel's
# 4.5 MB function request-body ceiling. The browser sends raw binary chunks.
PROJECT_ZIP_UPLOAD_CHUNK_BYTES = 4 * 1024 * 1024
PROJECT_ZIP_UPLOAD_SESSION_TTL = timedelta(hours=24)
PROJECT_ZIP_DB_BATCH_BYTES = 8 * 1024 * 1024
PROJECT_ZIP_DOWNLOAD_BATCH_CHUNKS = 4
EDITOR_ROLES = {"editor", "admin"}
ALLOWED_CONTENT_TYPES = {"course", "module", "lesson", "project", "reference", "diagram"}
ALLOWED_ANALYTICS_EVENTS = {
    "course_start", "course_completion", "exercise_attempt", "exercise_incorrect",
    "lesson_dropoff", "broken_asset", "project_completion", "lesson_completion",
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LearningPreferenceInput(StrictModel):
    timezone_name: str = Field(default="UTC", min_length=1, max_length=80)
    review_frequency_days: int = Field(default=1, ge=1, le=30)
    daily_review_limit: int = Field(default=10, ge=1, le=50)
    analytics_enabled: bool = False

    @field_validator("timezone_name")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("timezone_name must be a recognized IANA timezone") from exc
        return value


class SnoozeInput(StrictModel):
    days: int = Field(default=1, ge=1, le=30)


class ReviewRatingInput(StrictModel):
    """Learner self-assessment after opening the scheduled review item."""
    rating: Literal["again", "hard", "good", "easy"]
    course_slug: str = Field(min_length=1, max_length=100)
    lesson_slug: str = Field(min_length=1, max_length=180)
    item_type: Literal["lesson", "exercise"]
    item_slug: str = Field(min_length=1, max_length=180)


class PortfolioSubmissionInput(StrictModel):
    course_slug: str = Field(min_length=1, max_length=100)
    project_slug: str = Field(min_length=1, max_length=180)
    title: str | None = Field(default=None, max_length=200)
    code_bundle: dict[str, str] = Field(default_factory=dict)

    @field_validator("course_slug")
    @classmethod
    def valid_course_slug(cls, value: str) -> str:
        value = value.strip().lower()
        if not COURSE_SLUG_RE.fullmatch(value):
            raise ValueError("Invalid course slug")
        return value

    @field_validator("project_slug")
    @classmethod
    def valid_project_slug(cls, value: str) -> str:
        value = value.strip().lower()
        if not SLUG_RE.fullmatch(value):
            raise ValueError("Invalid project slug")
        return value

    @field_validator("code_bundle")
    @classmethod
    def bounded_code_bundle(cls, value: dict[str, str]) -> dict[str, str]:
        if len(value) > 40:
            raise ValueError("A submission may contain at most 40 files")
        total = 0
        cleaned = {}
        for path, content in value.items():
            if not isinstance(path, str) or not isinstance(content, str):
                raise ValueError("Submission files must map file paths to text")
            parts = Path(path.replace("\\", "/")).parts
            if (not path or path.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", path) or ".." in parts
                    or len(path) > 180 or "\x00" in path or ":" in path):
                raise ValueError("A submission contains an unsafe file path")
            total += len(path.encode("utf-8")) + len(content.encode("utf-8"))
            cleaned[path] = content
        if total > 100_000:
            raise ValueError("A submission may be at most 100 KB of text")
        return cleaned


class PortfolioUploadSessionInput(StrictModel):
    course_slug: str = Field(default="", max_length=100)
    project_slug: str = Field(default="", max_length=180)
    title: str | None = Field(default=None, max_length=200)
    filename: str = Field(min_length=1, max_length=512)
    total_bytes: int = Field(gt=0, le=500 * 1024 * 1024)


class PortfolioEditInput(StrictModel):
    visibility: Literal["private", "public"] | None = None
    title: str | None = Field(default=None, max_length=200)
    summary: str | None = Field(default=None, max_length=1000)
    skills: list[str] | None = Field(default=None, max_length=20)
    technologies: list[str] | None = Field(default=None, max_length=20)
    screenshot_urls: list[str] | None = Field(default=None, max_length=5)

    @field_validator("skills", "technologies")
    @classmethod
    def clean_terms(cls, value):
        if value is None:
            return value
        result = []
        for term in value:
            if not isinstance(term, str) or not term.strip() or len(term.strip()) > 50:
                raise ValueError("Skills and technologies must be non-empty strings up to 50 characters")
            result.append(term.strip())
        return list(dict.fromkeys(result))

    @field_validator("screenshot_urls")
    @classmethod
    def safe_screenshot_urls(cls, value):
        if value is None:
            return value
        cleaned = []
        for entry in value:
            if not isinstance(entry, str) or len(entry) > 1000:
                raise ValueError("Screenshot URLs must be valid HTTPS URLs")
            parsed = urlsplit(entry.strip())
            if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError("Screenshot URLs must use HTTPS and may not contain credentials")
            cleaned.append(entry.strip())
        return cleaned


class ContentRevisionInput(StrictModel):
    course_slug: str = Field(min_length=1, max_length=100)
    content_type: str = Field(min_length=1, max_length=30)
    content_slug: str = Field(min_length=1, max_length=180)
    content_json: dict[str, Any]

    @field_validator("course_slug")
    @classmethod
    def valid_course_slug(cls, value: str) -> str:
        value = value.strip().lower()
        if not COURSE_SLUG_RE.fullmatch(value):
            raise ValueError("Invalid course slug")
        return value

    @field_validator("content_slug")
    @classmethod
    def valid_content_slug(cls, value: str) -> str:
        value = value.strip().lower()
        if not SLUG_RE.fullmatch(value):
            raise ValueError("Invalid content slug")
        return value


class ReviewFeedbackInput(StrictModel):
    approved: bool
    feedback: str = Field(default="", max_length=3000)


class AnalyticsEventInput(StrictModel):
    event_type: str = Field(min_length=1, max_length=40)
    course_slug: str | None = Field(default=None, max_length=100)
    lesson_slug: str | None = Field(default=None, max_length=180)
    item_key: str | None = Field(default=None, max_length=180)
    outcome: str | None = Field(default=None, max_length=30)

    @field_validator("event_type")
    @classmethod
    def known_event(cls, value: str) -> str:
        if value not in ALLOWED_ANALYTICS_EVENTS:
            raise ValueError("Unsupported analytics event type")
        return value


class RunnerCreateInput(StrictModel):
    language: Literal["python", "javascript"]
    source: str = Field(min_length=1, max_length=16000)
    stdin: str = Field(default="", max_length=8000)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=100)

    @field_validator("idempotency_key")
    @classmethod
    def safe_idempotency_key(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(r"[A-Za-z0-9._:-]{8,100}", value):
            raise ValueError("idempotency_key contains unsupported characters")
        return value


class RunnerResultInput(StrictModel):
    pass


def _require_editor(user: User = Depends(require_user)) -> User:
    if getattr(user, "role", "learner") not in EDITOR_ROLES:
        raise HTTPException(status_code=403, detail="Content editor permission is required.")
    return user


def _slug_ok(value: str | None, pattern=SLUG_RE) -> bool:
    return bool(value and pattern.fullmatch(value))


def _audit(db: Session, actor: User, action: str, resource_type: str, resource_id: str, details: dict[str, Any] | None = None) -> None:
    db.add(AuditLog(actor_user_id=actor.id, action=action, resource_type=resource_type,
                    resource_id=resource_id[:180], details=details or {}, created_at=utc_now()))


def _preference_payload(preferences: LearningPreference) -> dict[str, Any]:
    return {
        "timezone_name": preferences.timezone_name,
        "review_frequency_days": preferences.review_frequency_days,
        "daily_review_limit": preferences.daily_review_limit,
        "analytics_enabled": preferences.analytics_enabled,
        "updated_at": preferences.updated_at.isoformat() if preferences.updated_at else None,
    }


def _aware_utc(value: datetime) -> datetime:
    """Normalize database datetimes for portable comparison and JSON serialization."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _review_metadata_index(db: Session, items: list[ReviewSchedule]) -> dict[tuple[str, str, str], dict[str, str]]:
    """Load published review targets in two queries, avoiding per-card query storms."""
    if not items:
        return {}
    course_slugs = {item.course_slug for item in items}
    lesson_slugs = {item.item_slug for item in items if item.item_type == "lesson"}
    exercise_slugs = {item.item_slug for item in items if item.item_type == "exercise"}
    metadata: dict[tuple[str, str, str], dict[str, str]] = {}
    if lesson_slugs:
        rows = db.execute(select(Course.slug, Lesson.slug, Lesson.title).join(
            Module, Module.course_id == Course.id
        ).join(Lesson, Lesson.module_id == Module.id).where(
            Course.slug.in_(course_slugs), Course.published.is_(True),
            Lesson.slug.in_(lesson_slugs), Lesson.is_published.is_(True),
        )).all()
        for course_slug, lesson_slug, title in rows:
            metadata[("lesson", course_slug, lesson_slug)] = {"title": title, "lesson_slug": lesson_slug}
    if exercise_slugs:
        rows = db.execute(select(Course.slug, Exercise.slug, Exercise.title, Lesson.slug).join(
            Module, Module.course_id == Course.id
        ).join(Lesson, Lesson.module_id == Module.id).join(
            Exercise, Exercise.lesson_id == Lesson.id
        ).where(
            Course.slug.in_(course_slugs), Course.published.is_(True),
            Lesson.is_published.is_(True), Exercise.slug.in_(exercise_slugs),
            Exercise.is_published.is_(True),
        )).all()
        for course_slug, exercise_slug, title, lesson_slug in rows:
            metadata[("exercise", course_slug, exercise_slug)] = {"title": title, "lesson_slug": lesson_slug}
    return metadata


def _review_item_lesson_slug(db: Session, item: ReviewSchedule) -> str | None:
    metadata = _review_metadata_index(db, [item])
    return metadata.get((item.item_type, item.course_slug, item.item_slug), {}).get("lesson_slug")


def _review_item_is_public(db: Session, item: ReviewSchedule) -> bool:
    return _review_item_lesson_slug(db, item) is not None


def _review_payload(db: Session, item: ReviewSchedule, metadata: dict[tuple[str, str, str], dict[str, str]] | None = None) -> dict[str, Any]:
    entry = (metadata or {}).get((item.item_type, item.course_slug, item.item_slug), {})
    title = entry.get("title") or item.item_slug.replace("-", " ").title()
    lesson_slug = entry.get("lesson_slug")
    if metadata is None and item.item_type == "lesson":
        title_query = select(Lesson.title).join(Module, Lesson.module_id == Module.id).join(Course, Module.course_id == Course.id).where(
            Course.slug == item.course_slug, Lesson.slug == item.item_slug
        )
        title = db.scalar(title_query) or title
        lesson_slug = _review_item_lesson_slug(db, item)
    elif metadata is None and item.item_type == "exercise":
        title_query = select(Exercise.title).join(Lesson, Exercise.lesson_id == Lesson.id).join(Module, Lesson.module_id == Module.id).join(Course, Module.course_id == Course.id).where(
            Course.slug == item.course_slug, Exercise.slug == item.item_slug
        )
        title = db.scalar(title_query) or title
        lesson_slug = _review_item_lesson_slug(db, item)
    return {
        "id": str(item.id), "course_slug": item.course_slug, "item_type": item.item_type,
        "item_slug": item.item_slug, "lesson_slug": lesson_slug, "title": title,
        "due_at": _aware_utc(item.due_at).isoformat(), "interval_days": item.interval_days,
        "repetitions": item.repetitions, "last_result": item.last_result,
        "dismissed_until": item.dismissed_until.isoformat() if item.dismissed_until else None,
    }


def _load_roadmaps() -> list[dict[str, Any]]:
    try:
        data = json.loads(ROADMAP_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    tracks = data.get("tracks", []) if isinstance(data, dict) else []
    return tracks if isinstance(tracks, list) else []


@router.get("/api/me/learning-preferences")
def get_learning_preferences(user: User = Depends(require_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    preferences = get_or_create_preferences(db, user.id)
    db.commit()
    return {"preferences": _preference_payload(preferences)}


@router.patch("/api/me/learning-preferences")
def update_learning_preferences(body: LearningPreferenceInput, user: User = Depends(require_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    preferences = get_or_create_preferences(db, user.id)
    preferences.timezone_name = body.timezone_name
    preferences.review_frequency_days = body.review_frequency_days
    preferences.daily_review_limit = body.daily_review_limit
    preferences.analytics_enabled = body.analytics_enabled
    preferences.updated_at = utc_now()
    db.commit()
    db.refresh(preferences)
    return {"preferences": _preference_payload(preferences)}


@router.get("/api/me/reviews")
def list_review_queue(user: User = Depends(require_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    preferences = get_or_create_preferences(db, user.id)
    now = utc_now()
    rows = db.scalars(select(ReviewSchedule).where(
        ReviewSchedule.user_id == user.id,
        (ReviewSchedule.dismissed_until.is_(None) | (ReviewSchedule.dismissed_until <= now)),
    ).order_by(ReviewSchedule.due_at.asc()).limit(200)).all()
    # Content can be unpublished after a schedule was created. Never surface dead
    # or draft lesson/exercise targets in the learner's review queue.
    metadata = _review_metadata_index(db, rows)
    rows = [row for row in rows if (row.item_type, row.course_slug, row.item_slug) in metadata]
    due = [row for row in rows if _aware_utc(row.due_at) <= now][:preferences.daily_review_limit]
    upcoming = [row for row in rows if _aware_utc(row.due_at) > now][:20]
    db.commit()
    return {"due": [_review_payload(db, item, metadata) for item in due], "upcoming": [_review_payload(db, item, metadata) for item in upcoming],
            "daily_limit": preferences.daily_review_limit, "timezone_name": preferences.timezone_name,
            "preferences": _preference_payload(preferences)}


@router.post("/api/me/reviews/{review_id}/snooze")
def snooze_review(review_id: UUID, body: SnoozeInput, user: User = Depends(require_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    item = db.scalar(select(ReviewSchedule).where(ReviewSchedule.id == review_id, ReviewSchedule.user_id == user.id))
    if item is None:
        raise HTTPException(status_code=404, detail="Review item was not found.")
    item.dismissed_until = utc_now() + timedelta(days=body.days)
    db.commit()
    return {"ok": True, "review": _review_payload(db, item)}


@router.post("/api/me/reviews/{review_id}/rate")
def rate_review(
    review_id: UUID,
    body: ReviewRatingInput,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Reschedule a review from the learner's self-reported recall; this never grants XP."""
    item = db.scalar(select(ReviewSchedule).where(
        ReviewSchedule.id == review_id, ReviewSchedule.user_id == user.id
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="Review item was not found.")
    if (item.course_slug != body.course_slug or item.item_type != body.item_type
            or item.item_slug != body.item_slug):
        raise HTTPException(status_code=400, detail="This review rating does not match the scheduled item.")
    metadata = _review_metadata_index(db, [item])
    target = metadata.get((item.item_type, item.course_slug, item.item_slug))
    if target is None:
        raise HTTPException(status_code=404, detail="The published review target is no longer available.")
    if target.get("lesson_slug") != body.lesson_slug:
        raise HTTPException(status_code=400, detail="This review rating does not match the lesson being reviewed.")

    preferences = get_or_create_preferences(db, user.id)
    apply_review_rating(item, preferences, body.rating, now=utc_now())
    db.commit()
    db.refresh(item)
    return {
        "ok": True,
        "review": _review_payload(db, item, metadata),
        "rating": body.rating,
        "xp_awarded": 0,
        "mastery_inferred": False,
        "message": "Your self-assessment was saved. It updates the review schedule only; it does not mark the lesson complete or award XP.",
    }


@router.get("/api/me/recommendations")
def get_recommendations(user: User = Depends(require_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    """Explain rule-based recommendations using published, account-owned records only."""
    require_feature(db, user, "personalized_recommendations")
    now = utc_now()
    recommendations: list[dict[str, Any]] = []
    # Due reviews rank first; review queue entries are created only by server-side outcomes.
    due_items = db.scalars(select(ReviewSchedule).where(
        ReviewSchedule.user_id == user.id, ReviewSchedule.due_at <= now,
        (ReviewSchedule.dismissed_until.is_(None) | (ReviewSchedule.dismissed_until <= now)),
    ).order_by(ReviewSchedule.due_at.asc()).limit(50)).all()
    review_metadata = _review_metadata_index(db, due_items)
    due_items = [item for item in due_items if (item.item_type, item.course_slug, item.item_slug) in review_metadata][:5]
    for item in due_items:
        title = _review_payload(db, item, review_metadata)["title"]
        recommendations.append({"kind": "review", "course_slug": item.course_slug,
            "item_slug": item.item_slug, "item_type": item.item_type, "title": f"Review: {title}",
            "reason": f"This {item.item_type} is due for retrieval practice based on your recorded learning history.",
            "due_at": item.due_at.isoformat(), "href": f"/learn/{item.course_slug}/{item.item_slug}" if item.item_type == "lesson" else f"/practice/{item.course_slug}"})
    # Recommend an attempted but not yet correctly completed exercise, never infer skill mastery.
    attempts = db.execute(select(Exercise, Course.slug, Lesson.slug, Course.title).join(
        Lesson, Exercise.lesson_id == Lesson.id).join(Module, Lesson.module_id == Module.id).join(
        Course, Module.course_id == Course.id).join(ExerciseProgress, ExerciseProgress.exercise_id == Exercise.id).where(
        ExerciseProgress.user_id == user.id, ExerciseProgress.attempts > 0,
        ExerciseProgress.completed.is_(False), Exercise.is_published.is_(True),
        Lesson.is_published.is_(True), Course.published.is_(True)
    ).order_by(ExerciseProgress.last_attempt_at.desc().nullslast()).limit(5)).all()
    seen = {(r.get("course_slug"), r.get("item_slug")) for r in recommendations}
    for exercise, course_slug, lesson_slug, course_title in attempts:
        if (course_slug, exercise.slug) in seen:
            continue
        recommendations.append({"kind": "practice", "course_slug": course_slug, "item_slug": exercise.slug,
            "item_type": "exercise", "lesson_slug": lesson_slug, "title": f"Practice: {exercise.title}",
            "reason": "You have attempted this exercise, but a correct completion has not been recorded yet.",
            "href": f"/learn/{course_slug}/{lesson_slug}"})
    # Continue with the first incomplete lesson in each course, ordered by actual curriculum order.
    next_lessons = db.execute(select(Lesson, Module.slug, Course.slug).join(
        Module, Lesson.module_id == Module.id).join(Course, Module.course_id == Course.id).outerjoin(
        LessonProgress, (LessonProgress.lesson_id == Lesson.id) & (LessonProgress.user_id == user.id)).where(
        Course.published.is_(True), Lesson.is_published.is_(True),
        (LessonProgress.id.is_(None) | LessonProgress.completed.is_(False))
    ).order_by(Course.sort_order, Module.sort_order, Lesson.sort_order).limit(50)).all()
    courses_added: set[str] = set()
    seen_urls = {r.get("href") for r in recommendations}
    for lesson, module_slug, course_slug in next_lessons:
        href = f"/learn/{course_slug}/{lesson.slug}"
        if course_slug in courses_added or href in seen_urls:
            continue
        courses_added.add(course_slug)
        recommendations.append({"kind": "next_lesson", "course_slug": course_slug,
            "item_slug": lesson.slug, "item_type": "lesson", "title": f"Continue: {lesson.title}",
            "reason": "This is the next unfinished published lesson in the course sequence.", "href": href})
        if len(recommendations) >= 10:
            break
    return {"items": recommendations[:10], "method": "transparent_rules", "mastery_inferred": False,
            "generated_at": now.isoformat()}


@router.get("/api/me/roadmaps")
def get_learning_roadmaps(user: User = Depends(require_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    """Resolve explicit roadmap course/module/project metadata against real published data."""
    completed_course_ids: set[str] = set()
    course_rows = db.execute(select(Course.slug, Course.id).where(Course.published.is_(True))).all()
    published_course_slugs = [row.slug for row in course_rows]
    for slug, course_id in course_rows:
        lesson_count = db.scalar(select(func.count(Lesson.id)).join(Module, Lesson.module_id == Module.id).where(Module.course_id == course_id, Lesson.is_published.is_(True))) or 0
        done_count = db.scalar(select(func.count(LessonProgress.id)).join(Lesson, LessonProgress.lesson_id == Lesson.id).join(Module, Lesson.module_id == Module.id).where(
            LessonProgress.user_id == user.id, LessonProgress.completed.is_(True), Module.course_id == course_id, Lesson.is_published.is_(True))) or 0
        if lesson_count and done_count >= lesson_count:
            completed_course_ids.add(slug)

    submissions = db.scalars(select(ProjectSubmission).where(ProjectSubmission.user_id == user.id)).all()
    submitted_project_keys = {
        ((row.portfolio_metadata or {}).get("course_slug", ""), row.project_slug)
        for row in submissions
    }
    tracks = []
    for track in _load_roadmaps():
        stages = []
        for stage in track.get("stages", []):
            course_requirements = list(stage.get("course_slugs", []))
            observed_courses = [slug for slug in course_requirements if slug in published_course_slugs]
            missing_courses = [slug for slug in course_requirements if slug not in observed_courses]
            module_progress = []
            all_modules_complete = True
            for target in stage.get("module_targets", []):
                target_course = target.get("course_slug", "")
                target_modules = target.get("module_slugs", [])
                course_row = db.scalar(select(Course).where(Course.slug == target_course, Course.published.is_(True)))
                for module_slug in target_modules:
                    if course_row is None:
                        module_progress.append({"course_slug": target_course, "module_slug": module_slug, "status": "unavailable", "progress_percent": 0})
                        all_modules_complete = False
                        continue
                    module = db.scalar(select(Module).where(Module.course_id == course_row.id, Module.slug == module_slug))
                    if module is None:
                        module_progress.append({"course_slug": target_course, "module_slug": module_slug, "status": "unavailable", "progress_percent": 0})
                        all_modules_complete = False
                        continue
                    module_total = db.scalar(select(func.count(Lesson.id)).where(Lesson.module_id == module.id, Lesson.is_published.is_(True))) or 0
                    module_done = db.scalar(select(func.count(LessonProgress.id)).join(Lesson, LessonProgress.lesson_id == Lesson.id).where(
                        LessonProgress.user_id == user.id, LessonProgress.completed.is_(True), Lesson.module_id == module.id, Lesson.is_published.is_(True))) or 0
                    state = "completed" if module_total > 0 and module_done >= module_total else ("in_progress" if module_done else ("not_started" if module_total else "unavailable"))
                    if state != "completed": all_modules_complete = False
                    module_progress.append({"course_slug": target_course, "module_slug": module_slug, "title": module.title, "status": state,
                        "completed_lessons": int(module_done), "total_lessons": int(module_total),
                        "progress_percent": round(module_done * 100 / module_total) if module_total else 0})

            project_requirements = list(stage.get("project_slugs", []))
            course_candidates = observed_courses or published_course_slugs
            available_projects: dict[str, str] = {}
            for project_slug in project_requirements:
                for candidate_course in course_candidates:
                    if _find_project_manifest(candidate_course, project_slug) is not None:
                        available_projects[project_slug] = candidate_course
                        break
            missing_projects = [slug for slug in project_requirements if slug not in available_projects]
            submitted_projects = [slug for slug, course_slug in available_projects.items() if (course_slug, slug) in submitted_project_keys]
            pending_projects = [slug for slug in available_projects if slug not in submitted_projects]

            all_courses_complete = all(slug in completed_course_ids for slug in course_requirements) and not missing_courses
            modules_complete = all_modules_complete if stage.get("module_targets") else True
            projects_complete = not missing_projects and not pending_projects
            has_requirements = bool(course_requirements or stage.get("module_targets") or project_requirements)
            if has_requirements and all_courses_complete and modules_complete and projects_complete:
                state = "completed"
            else:
                course_progress = any(db.scalar(select(func.count(LessonProgress.id)).join(Lesson, LessonProgress.lesson_id == Lesson.id).join(Module, Lesson.module_id == Module.id).join(Course, Module.course_id == Course.id).where(
                    LessonProgress.user_id == user.id, LessonProgress.completed.is_(True), Course.slug == slug)) or 0 for slug in observed_courses)
                module_activity = any(item["status"] in {"in_progress", "completed"} for item in module_progress)
                project_activity = bool(submitted_projects)
                available_any = bool(observed_courses or module_progress and any(item["status"] != "unavailable" for item in module_progress) or available_projects)
                state = "in_progress" if course_progress or module_activity or project_activity else ("not_started" if available_any else "unavailable")
            stages.append({**stage, "status": state, "available_course_slugs": observed_courses,
                "missing_course_slugs": missing_courses, "module_progress": module_progress,
                "available_project_slugs": sorted(available_projects), "missing_project_slugs": missing_projects,
                "submitted_project_slugs": submitted_projects, "projects_awaiting_submission": pending_projects})
        required = [item for item in stages if item.get("kind") == "required"]
        done = sum(1 for item in required if item["status"] == "completed")
        tracks.append({**track, "stages": stages, "required_stages_completed": done,
            "required_stages_total": len(required), "progress_percent": round(done * 100 / len(required)) if required else 0})
    return {"tracks": tracks, "progress_basis": "server-recorded completion of published lessons and explicit published project submissions; unavailable curriculum does not count as progress"}


def _find_project_manifest(course_slug: str, project_slug: str) -> dict[str, Any] | None:
    course_dir = (COURSE_CONTENT_ROOT / course_slug).resolve()
    root = COURSE_CONTENT_ROOT.resolve()
    if root not in course_dir.parents or not course_dir.is_dir():
        return None
    try:
        course_manifest = json.loads((course_dir / "course.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    for rel_path in course_manifest.get("project_files", []):
        path = (course_dir / str(rel_path)).resolve()
        if course_dir not in path.parents or not path.is_file():
            continue
        try:
            project = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        parts = Path(str(rel_path)).parts
        if any(part.lower() in {"solution", "solutions", "answer-keys", "answer_keys"} for part in parts):
            continue
        if project.get("status") == "published" and (project.get("slug") == project_slug or project.get("id") == project_slug):
            return project
    return None


def validate_project_zip_size(size: int) -> None:
    """Reject oversized archives without allocating a second copy in memory."""
    if size <= 0:
        raise HTTPException(status_code=400, detail="Choose a non-empty ZIP archive to upload.")
    if size > MAX_PROJECT_ZIP_BYTES:
        raise HTTPException(status_code=413, detail="Project ZIP files must be 500 MB or smaller.")


def validate_project_zip_file(file_obj) -> list[str]:
    """Validate ZIP structure without loading the entire archive into RAM."""
    try:
        file_obj.seek(0)
        archive = zipfile.ZipFile(file_obj)
    except (zipfile.BadZipFile, OSError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="The uploaded file is not a valid ZIP archive.") from exc

    with archive:
        files = []
        total_size = 0
        for info in archive.infolist():
            if info.is_dir():
                continue
            raw_path = info.filename
            normalized = raw_path.replace("\\", "/")
            path = PurePosixPath(normalized)
            raw_parts = normalized.split("/")
            mode = (info.external_attr >> 16) & 0xFFFF
            if (not raw_path or "\x00" in raw_path or normalized.startswith("/")
                    or re.match(r"^[A-Za-z]:", normalized)
                    or any(part in {"", ".", ".."} for part in raw_parts)
                    or ":" in normalized or (mode and (mode & 0o170000) == 0o120000)):
                raise HTTPException(status_code=400, detail="ZIP contains an unsafe file path or symbolic link.")
            if len(normalized) > 180:
                raise HTTPException(status_code=400, detail="A ZIP file path exceeds the 180-character limit.")
            if info.file_size > MAX_PROJECT_ZIP_FILE_BYTES:
                raise HTTPException(status_code=413, detail="Each file inside the ZIP must be 500 MB or smaller.")
            total_size += info.file_size
            if total_size > MAX_PROJECT_ZIP_UNCOMPRESSED_BYTES:
                raise HTTPException(status_code=413, detail="The uncompressed contents of a ZIP must total 1 GB or less.")
            files.append(normalized)
            if len(files) > MAX_PROJECT_ZIP_FILES:
                raise HTTPException(status_code=413, detail="A project ZIP may contain at most 10,000 files.")
        if not files:
            raise HTTPException(status_code=400, detail="The ZIP archive must contain at least one file.")
        try:
            bad_member = archive.testzip()
        except (zipfile.BadZipFile, RuntimeError, OSError, EOFError) as exc:
            raise HTTPException(status_code=400, detail="The ZIP archive could not be verified.") from exc
        if bad_member:
            raise HTTPException(status_code=400, detail="A file inside the ZIP archive is corrupted.")
    file_obj.seek(0)
    return files


def validate_project_zip(payload: bytes) -> list[str]:
    """Compatibility wrapper used by the regression tests and any legacy callers."""
    validate_project_zip_size(len(payload))
    return validate_project_zip_file(io.BytesIO(payload))


def _normalize_portfolio_slug(value: str, *, fallback: str, max_length: int = 180) -> str:
    """Convert a user-entered project name or technology into a safe URL-style slug."""
    candidate = (value or fallback or "my-project").strip().lower()
    candidate = re.sub(r"[^a-z0-9]+", "-", candidate).strip("-")
    candidate = candidate[:max_length].strip("-")
    if not candidate:
        candidate = "my-project"
    if not SLUG_RE.fullmatch(candidate):
        raise HTTPException(status_code=422, detail="Enter a project name using letters, numbers, spaces, or hyphens.")
    return candidate


def _store_project_zip_chunks(db: Session, submission_id, file_obj) -> int:
    """Store an archive in small database rows so 500 MB uploads do not need 500 MB of RAM."""
    file_obj.seek(0)
    sequence = 0
    batch: list[ProjectSubmissionZipChunk] = []
    batch_size = 0
    while True:
        payload = file_obj.read(PROJECT_ZIP_CHUNK_BYTES)
        if not payload:
            break
        batch.append(ProjectSubmissionZipChunk(submission_id=submission_id, sequence=sequence, payload=payload))
        batch_size += len(payload)
        sequence += 1
        if batch_size >= PROJECT_ZIP_DB_BATCH_BYTES:
            db.add_all(batch)
            db.flush()
            batch = []
            batch_size = 0
    if batch:
        db.add_all(batch)
        db.flush()
    if sequence == 0:
        raise HTTPException(status_code=400, detail="Choose a non-empty ZIP archive to upload.")
    return sequence


def _portfolio_certificate_items(db: Session, owner: User) -> list[dict[str, Any]]:
    rows = db.execute(
        select(Certificate, Course.slug, Course.title)
        .join(Course, Certificate.course_id == Course.id)
        .where(Certificate.user_id == owner.id, Certificate.revoked_at.is_(None))
        .order_by(Certificate.issued_at.desc())
    ).all()
    return [
        {
            "public_id": certificate.public_id,
            "course_slug": course_slug,
            "course_title": course_title,
            "issued_at": certificate.issued_at.isoformat(),
            "verification_url": f"/api/certificates/verify/{certificate.public_id}",
        }
        for certificate, course_slug, course_title in rows
    ]


def _portfolio_upload_is_complete(submission: ProjectSubmission) -> bool:
    """Return False only for a pending chunked upload, not ordinary legacy submissions."""
    raw_metadata = getattr(submission, "portfolio_metadata", None)
    metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
    return not (metadata.get("upload_state") == "uploading" and not metadata.get("archive_upload_complete"))


def _download_project_zip(submission: ProjectSubmission, is_public: bool, db: Session | None = None) -> Response:
    """Stream chunk-stored ZIPs; keep compatibility with old inline and JSON-bundle submissions."""
    if not _portfolio_upload_is_complete(submission):
        raise HTTPException(status_code=409, detail="This project ZIP upload is not complete yet.")
    filename = submission.zip_filename or f"{submission.project_slug}.zip"
    safe_filename = re.sub(r"[^A-Za-z0-9._-]+", "-", filename).strip(".-") or "project.zip"
    if submission.zip_bundle:
        payload = bytes(submission.zip_bundle)
        return Response(content=payload, media_type="application/zip", headers={
            "Content-Disposition": f'attachment; filename="{safe_filename}"',
            "Content-Length": str(len(payload)),
            "Cache-Control": "public, max-age=300" if is_public else "private, no-store",
            "X-Content-Type-Options": "nosniff",
        })

    if db is not None:
        first_chunk = db.scalar(select(ProjectSubmissionZipChunk.sequence).where(
            ProjectSubmissionZipChunk.submission_id == submission.id
        ).order_by(ProjectSubmissionZipChunk.sequence).limit(1))
        if first_chunk is not None:
            submission_id = submission.id

            def archive_chunks():
                # Separate short-lived sessions keep each database query bounded and avoid
                # holding a 500 MB result set (or a long transaction) in application memory.
                if SessionLocal is None:
                    return
                next_sequence = 0
                while True:
                    with SessionLocal() as download_db:
                        rows = download_db.execute(
                            select(ProjectSubmissionZipChunk.sequence, ProjectSubmissionZipChunk.payload)
                            .where(
                                ProjectSubmissionZipChunk.submission_id == submission_id,
                                ProjectSubmissionZipChunk.sequence >= next_sequence,
                            )
                            .order_by(ProjectSubmissionZipChunk.sequence)
                            .limit(PROJECT_ZIP_DOWNLOAD_BATCH_CHUNKS)
                        ).all()
                    if not rows:
                        break
                    for _, chunk in rows:
                        yield bytes(chunk)
                    next_sequence = int(rows[-1][0]) + 1

            from starlette.responses import StreamingResponse
            return StreamingResponse(archive_chunks(), media_type="application/zip", headers={
                "Content-Disposition": f'attachment; filename="{safe_filename}"',
                "Cache-Control": "public, max-age=300" if is_public else "private, no-store",
                "X-Content-Type-Options": "nosniff",
            })

    bundle = submission.code_bundle or {}
    if not isinstance(bundle, dict) or not bundle:
        raise HTTPException(status_code=404, detail="This submission has no downloadable project archive.")
    stream = io.BytesIO()
    try:
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file_path, content in bundle.items():
                if not isinstance(file_path, str) or not isinstance(content, str):
                    continue
                normalized = file_path.replace("\\", "/")
                safe_path = PurePosixPath(normalized)
                if normalized.startswith("/") or any(part in {"", ".", ".."} for part in safe_path.parts):
                    continue
                archive.writestr(normalized, content)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        raise HTTPException(status_code=500, detail="The project archive could not be prepared.") from exc
    payload = stream.getvalue()
    filename = f"{submission.project_slug}.zip"
    safe_filename = re.sub(r"[^A-Za-z0-9._-]+", "-", filename).strip(".-") or "project.zip"
    return Response(content=payload, media_type="application/zip", headers={
        "Content-Disposition": f'attachment; filename="{safe_filename}"',
        "Content-Length": str(len(payload)),
        "Cache-Control": "public, max-age=300" if is_public else "private, no-store",
        "X-Content-Type-Options": "nosniff",
    })


def _portfolio_item(submission: ProjectSubmission, owner: User | None = None) -> dict[str, Any]:
    metadata = submission.portfolio_metadata or {}
    return {
        "id": str(submission.id), "project_slug": submission.project_slug,
        "course_slug": metadata.get("course_slug", ""),
        "title": metadata.get("title") or submission.title,
        "summary": metadata.get("summary", ""), "skills": metadata.get("skills", []),
        "technologies": metadata.get("technologies", []),
        "screenshot_urls": metadata.get("screenshot_urls", []),
        "has_downloadable_zip": bool(
            metadata.get("archive_upload_complete")
            or (submission.zip_filename and not metadata.get("custom_project"))
            or submission.code_bundle
        ),
        "zip_filename": submission.zip_filename or f"{submission.project_slug}.zip",
        "visibility": submission.visibility, "submitted_at": submission.submitted_at.isoformat(),
        "username": owner.username if owner else None,
        "display_name": owner.display_name if owner else None,
    }


@router.post("/api/me/portfolio/submissions", status_code=status.HTTP_201_CREATED)
def create_portfolio_submission(body: PortfolioSubmissionInput, user: User = Depends(require_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    """Accept legacy text-bundle submissions for any learner-created project."""
    encoded_bundle_size = len(json.dumps(body.code_bundle, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    ensure_storage_capacity(db, user, incoming_bytes=encoded_bundle_size)
    submission = ProjectSubmission(user_id=user.id, project_slug=body.project_slug,
        title=(body.title or body.project_slug.replace("-", " ").title()).strip(),
        code_bundle=body.code_bundle, stored_bytes=encoded_bundle_size, visibility="private",
        portfolio_metadata={"course_slug": body.course_slug, "custom_project": True, "summary": "", "skills": [], "technologies": [], "screenshot_urls": []})
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return {"submission": _portfolio_item(submission, user), "message": "Submission saved privately. Choose its visible fields before sharing."}


def _cleanup_expired_portfolio_uploads(db: Session, user_id) -> int:
    """Release abandoned upload reservations after 24 hours; never delete completed work."""
    cutoff = utc_now() - PROJECT_ZIP_UPLOAD_SESSION_TTL
    stale_rows = db.scalars(
        select(ProjectSubmission).where(
            ProjectSubmission.user_id == user_id,
            ProjectSubmission.submitted_at < cutoff,
        )
    ).all()
    removed = 0
    for row in stale_rows:
        metadata = row.portfolio_metadata if isinstance(row.portfolio_metadata, dict) else {}
        if metadata.get("upload_state") == "uploading" and not metadata.get("archive_upload_complete"):
            db.delete(row)
            removed += 1
    if removed:
        db.flush()
    return removed


def _owned_upload_submission(db: Session, submission_id: UUID, user: User, *, lock: bool = False) -> ProjectSubmission:
    query = select(ProjectSubmission).where(
        ProjectSubmission.id == submission_id,
        ProjectSubmission.user_id == user.id,
    )
    if lock:
        query = query.with_for_update()
    row = db.scalar(query)
    if row is None:
        # Do not reveal whether another learner has an upload with this ID.
        raise HTTPException(status_code=404, detail="Upload session was not found.")
    return row


@router.post("/api/me/portfolio/submissions/upload-session", status_code=status.HTTP_201_CREATED)
def create_portfolio_upload_session(
    body: PortfolioUploadSessionInput,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Reserve storage and create a chunk-upload session without sending a large body through Vercel."""
    filename = Path(body.filename).name.strip()
    if not filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Upload a .zip archive of your project files.")
    validate_project_zip_size(body.total_bytes)
    _cleanup_expired_portfolio_uploads(db, user.id)

    course_slug = _normalize_portfolio_slug(body.course_slug, fallback="", max_length=100) if body.course_slug.strip() else ""
    title_value = (body.title or "").strip()
    project_base = body.project_slug.strip() or title_value or Path(filename).stem or "my-project"
    normalized_project_slug = _normalize_portfolio_slug(project_base, fallback="my-project", max_length=180)
    safe_filename = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(filename).name).strip(".-") or f"{normalized_project_slug}.zip"
    if not safe_filename.lower().endswith(".zip"):
        safe_filename += ".zip"
    safe_filename = safe_filename[:180]

    ensure_storage_capacity(db, user, incoming_bytes=body.total_bytes)
    chunk_count = (body.total_bytes + PROJECT_ZIP_UPLOAD_CHUNK_BYTES - 1) // PROJECT_ZIP_UPLOAD_CHUNK_BYTES
    submission = ProjectSubmission(
        user_id=user.id,
        project_slug=normalized_project_slug,
        title=(title_value or normalized_project_slug.replace("-", " ").title()).strip()[:200],
        code_bundle={},
        zip_bundle=None,
        zip_filename=safe_filename,
        stored_bytes=body.total_bytes,
        visibility="private",
        portfolio_metadata={
            "course_slug": course_slug,
            "custom_project": True,
            "archive_upload_complete": False,
            "upload_state": "uploading",
            "upload_expected_bytes": body.total_bytes,
            "upload_chunk_size": PROJECT_ZIP_UPLOAD_CHUNK_BYTES,
            "upload_chunk_count": chunk_count,
            "upload_protocol": "chunked-v1",
            "summary": "",
            "skills": [],
            "technologies": [],
            "screenshot_urls": [],
        },
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return {
        "upload_id": str(submission.id),
        "chunk_size": PROJECT_ZIP_UPLOAD_CHUNK_BYTES,
        "chunk_count": chunk_count,
        "expires_after_hours": int(PROJECT_ZIP_UPLOAD_SESSION_TTL.total_seconds() // 3600),
        "message": "Upload session created. Send each binary chunk, then finalize the archive.",
    }


@router.put("/api/me/portfolio/submissions/upload-session/{submission_id}/chunks/{sequence}")
async def upload_portfolio_submission_chunk(
    submission_id: UUID,
    sequence: int,
    request: Request,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Accept one bounded raw-binary chunk; identical retries are idempotent."""
    submission = _owned_upload_submission(db, submission_id, user, lock=True)
    metadata = dict(submission.portfolio_metadata or {})
    if metadata.get("upload_state") != "uploading" or metadata.get("archive_upload_complete"):
        raise HTTPException(status_code=409, detail="This upload session is no longer accepting chunks.")
    total_bytes = int(metadata.get("upload_expected_bytes") or 0)
    chunk_size = int(metadata.get("upload_chunk_size") or 0)
    chunk_count = int(metadata.get("upload_chunk_count") or 0)
    if chunk_size != PROJECT_ZIP_UPLOAD_CHUNK_BYTES or sequence < 0 or sequence >= chunk_count:
        raise HTTPException(status_code=400, detail="Invalid upload chunk number.")
    expected_size = min(chunk_size, total_bytes - sequence * chunk_size)
    if expected_size <= 0:
        raise HTTPException(status_code=400, detail="Invalid upload chunk size.")

    # Stream into a small bounded buffer instead of trusting Content-Length or
    # materializing an arbitrarily large request body in memory.
    parts: list[bytes] = []
    received = 0
    async for part in request.stream():
        if not part:
            continue
        received += len(part)
        if received > expected_size:
            raise HTTPException(status_code=413, detail="Upload chunk exceeds its expected size.")
        parts.append(part)
    payload = b"".join(parts)
    if len(payload) != expected_size:
        raise HTTPException(status_code=400, detail="Upload chunk size does not match the expected size.")

    existing = db.scalar(select(ProjectSubmissionZipChunk).where(
        ProjectSubmissionZipChunk.submission_id == submission.id,
        ProjectSubmissionZipChunk.sequence == sequence,
    ))
    if existing is not None:
        if bytes(existing.payload) == payload:
            db.rollback()
            return {"stored": True, "duplicate": True, "sequence": sequence, "received_bytes": len(payload)}
        raise HTTPException(status_code=409, detail="A different chunk is already stored at this sequence number.")

    db.add(ProjectSubmissionZipChunk(submission_id=submission.id, sequence=sequence, payload=payload))
    db.commit()
    return {"stored": True, "duplicate": False, "sequence": sequence, "received_bytes": len(payload)}


@router.post("/api/me/portfolio/submissions/upload-session/{submission_id}/finalize", status_code=status.HTTP_201_CREATED)
def finalize_portfolio_upload_session(
    submission_id: UUID,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Verify all chunks and validate the reconstructed ZIP before publishing it as a saved submission."""
    submission = _owned_upload_submission(db, submission_id, user, lock=True)
    metadata = dict(submission.portfolio_metadata or {})
    if metadata.get("archive_upload_complete") and metadata.get("upload_state") == "completed":
        return {"submission": _portfolio_item(submission, user), "message": "This upload was already finalized."}
    if metadata.get("upload_state") != "uploading":
        raise HTTPException(status_code=409, detail="This upload session cannot be finalized.")

    expected_bytes = int(metadata.get("upload_expected_bytes") or 0)
    expected_chunks = int(metadata.get("upload_chunk_count") or 0)
    actual_count = db.scalar(select(func.count()).select_from(ProjectSubmissionZipChunk).where(
        ProjectSubmissionZipChunk.submission_id == submission.id,
    )) or 0
    if expected_bytes <= 0 or expected_chunks <= 0 or int(actual_count) != expected_chunks:
        raise HTTPException(status_code=409, detail={
            "code": "UPLOAD_INCOMPLETE",
            "message": "Some ZIP chunks are still missing. Retry failed chunks, then finalize again.",
            "expected_chunks": expected_chunks,
            "received_chunks": int(actual_count),
        })

    total_written = 0
    next_sequence = 0
    with tempfile.TemporaryFile(mode="w+b") as archive_file:
        while next_sequence < expected_chunks:
            batch = db.execute(
                select(ProjectSubmissionZipChunk.sequence, ProjectSubmissionZipChunk.payload)
                .where(
                    ProjectSubmissionZipChunk.submission_id == submission.id,
                    ProjectSubmissionZipChunk.sequence >= next_sequence,
                )
                .order_by(ProjectSubmissionZipChunk.sequence)
                .limit(4)
            ).all()
            if not batch:
                raise HTTPException(status_code=409, detail="Some ZIP chunks are missing. Retry the upload and finalize again.")
            for stored_sequence, payload in batch:
                if int(stored_sequence) != next_sequence:
                    raise HTTPException(status_code=409, detail="ZIP chunks are not in a complete sequence.")
                archive_file.write(bytes(payload))
                total_written += len(payload)
                next_sequence += 1
        if total_written != expected_bytes:
            raise HTTPException(status_code=409, detail="Uploaded byte count does not match the declared ZIP size.")
        try:
            validate_project_zip_file(archive_file)
        except HTTPException:
            # Invalid/unsafe archives do not occupy storage indefinitely.
            db.delete(submission)
            db.commit()
            raise

    metadata["archive_upload_complete"] = True
    metadata["upload_state"] = "completed"
    metadata["upload_completed_at"] = utc_now().isoformat()
    submission.portfolio_metadata = metadata
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return {"submission": _portfolio_item(submission, user), "message": "Your project ZIP was validated and saved privately."}


@router.delete("/api/me/portfolio/submissions/upload-session/{submission_id}")
def cancel_portfolio_upload_session(
    submission_id: UUID,
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Cancel an incomplete upload and atomically release its reserved storage quota."""
    submission = db.scalar(select(ProjectSubmission).where(
        ProjectSubmission.id == submission_id,
        ProjectSubmission.user_id == user.id,
    ).with_for_update())
    if submission is None:
        return {"deleted": False}
    metadata = dict(submission.portfolio_metadata or {})
    if metadata.get("upload_state") != "uploading" or metadata.get("archive_upload_complete"):
        raise HTTPException(status_code=409, detail="A completed project submission cannot be canceled as an upload session.")
    db.delete(submission)
    db.commit()
    return {"deleted": True}


@router.post("/api/me/portfolio/submissions/upload", status_code=status.HTTP_201_CREATED)
def upload_portfolio_submission(
    course_slug: str = Form(default="", max_length=100),
    project_slug: str = Form(default="", max_length=180),
    title: str | None = Form(default=None, max_length=200),
    archive_file: UploadFile = File(...),
    user: User = Depends(require_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Accept any learner-created ZIP; no reviewed-course project manifest is required."""
    filename = (archive_file.filename or "").strip()
    if not filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Upload a .zip archive of your project files.")
    try:
        archive_file.file.seek(0, 2)
        payload_size = archive_file.file.tell()
        validate_project_zip_size(payload_size)
        archive_file.file.seek(0)
        validate_project_zip_file(archive_file.file)
        archive_file.file.seek(0)

        course_slug = _normalize_portfolio_slug(course_slug, fallback="", max_length=100) if course_slug.strip() else ""
        title_value = (title or "").strip()
        project_base = project_slug.strip() or title_value or Path(filename).stem or "my-project"
        normalized_project_slug = _normalize_portfolio_slug(
            project_base, fallback="my-project", max_length=180
        )
        safe_filename = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(filename).name).strip(".-") or f"{normalized_project_slug}.zip"
        if not safe_filename.lower().endswith(".zip"):
            safe_filename += ".zip"

        ensure_storage_capacity(db, user, incoming_bytes=payload_size)
        submission = ProjectSubmission(
            user_id=user.id,
            project_slug=normalized_project_slug,
            title=(title_value or normalized_project_slug.replace("-", " ").title()).strip()[:200],
            code_bundle={}, zip_bundle=None, zip_filename=safe_filename, stored_bytes=payload_size, visibility="private",
            portfolio_metadata={
                "course_slug": course_slug,
                "custom_project": True,
                "archive_upload_complete": False,
                "summary": "", "skills": [], "technologies": [], "screenshot_urls": [],
            },
        )
        db.add(submission)
        db.flush()
        try:
            _store_project_zip_chunks(db, submission.id, archive_file.file)
            metadata = dict(submission.portfolio_metadata or {})
            metadata["archive_upload_complete"] = True
            submission.portfolio_metadata = metadata
            db.add(submission)
            db.commit()
        except Exception as exc:
            # The submission row, quota check and chunks share one transaction. Rollback
            # removes the partial upload and releases the user's quota lock atomically.
            db.rollback()
            if isinstance(exc, HTTPException):
                raise
            raise HTTPException(status_code=503, detail="The project ZIP could not be stored completely. Please retry the upload.") from exc
        db.refresh(submission)
        return {"submission": _portfolio_item(submission, user), "message": "Your project ZIP was saved privately. Add a summary, then enable public sharing when you are ready."}
    finally:
        try:
            archive_file.file.close()
        except Exception:
            pass


@router.get("/api/me/portfolio")
def get_my_portfolio(user: User = Depends(require_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    rows = db.scalars(select(ProjectSubmission).where(ProjectSubmission.user_id == user.id).order_by(ProjectSubmission.submitted_at.desc())).all()
    visible_rows = [row for row in rows if _portfolio_upload_is_complete(row)]
    return {"username": user.username, "items": [_portfolio_item(row, user) for row in visible_rows], "certificates": _portfolio_certificate_items(db, user), "default_visibility": "private"}


@router.patch("/api/me/portfolio/{submission_id}")
def update_portfolio_item(submission_id: UUID, body: PortfolioEditInput, user: User = Depends(require_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    item = db.scalar(select(ProjectSubmission).where(ProjectSubmission.id == submission_id, ProjectSubmission.user_id == user.id))
    if item is None:
        raise HTTPException(status_code=404, detail="Portfolio submission was not found.")
    if not _portfolio_upload_is_complete(item):
        raise HTTPException(status_code=409, detail="Finish or cancel the ZIP upload before editing or sharing this project.")
    metadata = dict(item.portfolio_metadata or {})
    changes = body.model_dump(exclude_unset=True)
    if "visibility" in changes and changes["visibility"] is not None:
        item.visibility = changes.pop("visibility")
    if "title" in changes and changes["title"] is not None:
        metadata["title"] = changes.pop("title").strip()
    for key, value in changes.items():
        if value is not None:
            metadata[key] = value
    if len(json.dumps(metadata, ensure_ascii=False).encode("utf-8")) > 12_000:
        raise HTTPException(status_code=413, detail="Portfolio metadata is too large.")
    item.portfolio_metadata = metadata
    db.commit()
    db.refresh(item)
    return {"item": _portfolio_item(item, user), "message": "Visibility and selected portfolio fields were saved."}


@router.get("/api/me/portfolio/{submission_id}/download")
def download_my_project_submission(
    submission_id: UUID, user: User = Depends(require_user), db: Session = Depends(get_db)
) -> Response:
    item = db.scalar(select(ProjectSubmission).where(ProjectSubmission.id == submission_id, ProjectSubmission.user_id == user.id))
    if item is None:
        raise HTTPException(status_code=404, detail="Project submission was not found.")
    return _download_project_zip(item, is_public=False, db=db)


@router.get("/api/portfolio/{username}/projects/{submission_id}/download")
def download_public_project_submission(
    username: str, submission_id: UUID, db: Session = Depends(get_db)
) -> Response:
    owner = db.scalar(select(User).where(User.username == username.lower(), User.is_active.is_(True)))
    if owner is None:
        raise HTTPException(status_code=404, detail="Public portfolio was not found.")
    item = db.scalar(select(ProjectSubmission).where(
        ProjectSubmission.id == submission_id,
        ProjectSubmission.user_id == owner.id,
        ProjectSubmission.visibility == "public",
    ))
    if item is None:
        raise HTTPException(status_code=404, detail="This project is not shared publicly.")
    return _download_project_zip(item, is_public=True, db=db)


@router.get("/api/portfolio/{username}")
def get_public_portfolio(username: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    owner = db.scalar(select(User).where(User.username == username.lower(), User.is_active.is_(True)))
    if owner is None:
        raise HTTPException(status_code=404, detail="Public portfolio was not found.")
    rows = db.scalars(select(ProjectSubmission).where(ProjectSubmission.user_id == owner.id,
        ProjectSubmission.visibility == "public").order_by(ProjectSubmission.submitted_at.desc())).all()
    visible_rows = [row for row in rows if _portfolio_upload_is_complete(row)]
    return {"username": owner.username, "display_name": owner.display_name,
            "items": [_portfolio_item(row, owner) for row in visible_rows],
            "certificates": _portfolio_certificate_items(db, owner)}


def _validate_content(revision: ContentRevision) -> dict[str, Any]:
    data = revision.content_json
    errors: list[str] = []
    if not isinstance(data, dict) or not data:
        errors.append("Content must be a non-empty JSON object.")
    else:
        try:
            serialized = json.dumps(data, ensure_ascii=False, allow_nan=False)
            if len(serialized.encode("utf-8")) > 250_000:
                errors.append("A single revision may not exceed 250 KB.")
        except (TypeError, ValueError):
            serialized = ""
            errors.append("Content must contain only standard JSON values.")
        if not any(isinstance(data.get(key), str) and data.get(key).strip() for key in ("title", "name", "slug", "course")):
            errors.append("Content needs a title, name, slug, or course identity field.")
        if data.get("slug") and data.get("slug") != revision.content_slug:
            errors.append("Top-level slug must match this revision's content slug.")
    if revision.content_type == "diagram" and isinstance(data, dict):
        # Reuse the same strict schema/text-mapping validator as live lesson assets.
        try:
            with tempfile.TemporaryDirectory(prefix="codeleaf-content-preview-") as directory:
                diagram_path = Path(directory) / "revision.diagram.json"
                diagram_path.write_text(json.dumps(data, ensure_ascii=False, allow_nan=False), encoding="utf-8")
                validate_dynamic_diagram_model(diagram_path, f"staged diagram {revision.content_slug}")
        except (OSError, TypeError, ValueError) as exc:
            errors.append(f"Native diagram validation failed: {str(exc)[:500]}")
    return {"valid": not errors, "errors": errors,
            "checked_at": utc_now().isoformat(), "validation_scope": "staging-structure-only",
            "live_import_preflight_required": True}


def _revision_payload(row: ContentRevision) -> dict[str, Any]:
    return {"id": str(row.id), "course_slug": row.course_slug, "content_type": row.content_type,
            "content_slug": row.content_slug, "version": row.version, "status": row.status,
            "content_json": row.content_json, "validation_report": row.validation_report,
            "review_feedback": row.review_feedback, "created_by": str(row.created_by),
            "reviewed_by": str(row.reviewed_by) if row.reviewed_by else None,
            "published_by": str(row.published_by) if row.published_by else None,
            "created_at": row.created_at.isoformat(), "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None,
            "published_at": row.published_at.isoformat() if row.published_at else None}


@router.get("/api/editor/content-revisions")
def list_content_revisions(user: User = Depends(_require_editor), db: Session = Depends(get_db)) -> dict[str, Any]:
    rows = db.scalars(select(ContentRevision).order_by(ContentRevision.created_at.desc()).limit(200)).all()
    return {"items": [_revision_payload(row) for row in rows]}


@router.post("/api/editor/content-revisions", status_code=status.HTTP_201_CREATED)
def create_content_revision(body: ContentRevisionInput, user: User = Depends(_require_editor), db: Session = Depends(get_db)) -> dict[str, Any]:
    if body.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=422, detail="Unsupported content_type.")
    course_dir = (COURSE_CONTENT_ROOT / body.course_slug).resolve()
    if COURSE_CONTENT_ROOT.resolve() not in course_dir.parents or not course_dir.is_dir():
        raise HTTPException(status_code=404, detail="Course content directory was not found.")
    try:
        encoded = json.dumps(body.content_json, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="content_json must be standard JSON data.")
    if len(encoded) > 250_000:
        raise HTTPException(status_code=413, detail="A revision may not exceed 250 KB.")
    latest = db.scalar(select(func.max(ContentRevision.version)).where(
        ContentRevision.course_slug == body.course_slug, ContentRevision.content_type == body.content_type,
        ContentRevision.content_slug == body.content_slug)) or 0
    row = ContentRevision(course_slug=body.course_slug, content_type=body.content_type,
        content_slug=body.content_slug, version=latest + 1, status="draft",
        content_json=body.content_json, validation_report={}, review_feedback="",
        created_by=user.id, created_at=utc_now())
    db.add(row)
    db.flush()
    _audit(db, user, "content_revision_created", "content_revision", str(row.id), {"course_slug": row.course_slug, "content_type": row.content_type, "version": row.version})
    db.commit()
    db.refresh(row)
    return {"revision": _revision_payload(row)}


@router.get("/api/editor/content-revisions/{revision_id}")
def get_content_revision(revision_id: UUID, user: User = Depends(_require_editor), db: Session = Depends(get_db)) -> dict[str, Any]:
    row = db.get(ContentRevision, revision_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Content revision was not found.")
    return {"revision": _revision_payload(row), "preview_isolated": True}


@router.post("/api/editor/content-revisions/{revision_id}/validate")
def validate_content_revision(revision_id: UUID, user: User = Depends(_require_editor), db: Session = Depends(get_db)) -> dict[str, Any]:
    row = db.get(ContentRevision, revision_id)
    if row is None: raise HTTPException(status_code=404, detail="Content revision was not found.")
    if row.status not in {"draft", "review", "reviewed"}:
        raise HTTPException(status_code=409, detail="Only a draft revision can be validated.")
    report = _validate_content(row)
    row.validation_report = report
    if report["valid"]: row.status = "review"
    _audit(db, user, "content_revision_validated", "content_revision", str(row.id), {"valid": report["valid"], "error_count": len(report["errors"])})
    db.commit()
    db.refresh(row)
    return {"revision": _revision_payload(row)}


@router.post("/api/editor/content-revisions/{revision_id}/review")
def review_content_revision(revision_id: UUID, body: ReviewFeedbackInput, user: User = Depends(_require_editor), db: Session = Depends(get_db)) -> dict[str, Any]:
    row = db.get(ContentRevision, revision_id)
    if row is None: raise HTTPException(status_code=404, detail="Content revision was not found.")
    if row.status != "review": raise HTTPException(status_code=409, detail="Validate the draft before reviewing it.")
    row.review_feedback = body.feedback.strip()
    row.reviewed_by = user.id
    row.reviewed_at = utc_now()
    row.status = "reviewed" if body.approved and row.validation_report.get("valid") else "draft"
    _audit(db, user, "content_revision_reviewed", "content_revision", str(row.id), {"approved": row.status == "reviewed"})
    db.commit()
    db.refresh(row)
    return {"revision": _revision_payload(row)}


@router.post("/api/editor/content-revisions/{revision_id}/publish")
def publish_content_revision(revision_id: UUID, user: User = Depends(_require_editor), db: Session = Depends(get_db)) -> dict[str, Any]:
    row = db.get(ContentRevision, revision_id)
    if row is None: raise HTTPException(status_code=404, detail="Content revision was not found.")
    if row.status != "reviewed" or not row.validation_report.get("valid"):
        raise HTTPException(status_code=409, detail="A successfully validated and approved revision is required before publication.")
    row.status = "published"
    row.published_by = user.id
    row.published_at = utc_now()
    _audit(db, user, "content_revision_published_to_studio", "content_revision", str(row.id), {"version": row.version, "course_slug": row.course_slug})
    db.commit()
    db.refresh(row)
    return {"revision": _revision_payload(row), "live_catalog_updated": False,
            "message": "Published to the content-studio revision history. Run the existing importer and release preflight before this file becomes learner-facing."}


@router.post("/api/editor/content-revisions/{revision_id}/archive")
def archive_content_revision(revision_id: UUID, user: User = Depends(_require_editor), db: Session = Depends(get_db)) -> dict[str, Any]:
    row = db.get(ContentRevision, revision_id)
    if row is None: raise HTTPException(status_code=404, detail="Content revision was not found.")
    row.status = "archived"
    _audit(db, user, "content_revision_archived", "content_revision", str(row.id), {"version": row.version})
    db.commit()
    db.refresh(row)
    return {"revision": _revision_payload(row)}


@router.post("/api/editor/content-revisions/{revision_id}/rollback", status_code=status.HTTP_201_CREATED)
def rollback_content_revision(revision_id: UUID, user: User = Depends(_require_editor), db: Session = Depends(get_db)) -> dict[str, Any]:
    source = db.get(ContentRevision, revision_id)
    if source is None: raise HTTPException(status_code=404, detail="Source revision was not found.")
    latest = db.scalar(select(func.max(ContentRevision.version)).where(
        ContentRevision.course_slug == source.course_slug, ContentRevision.content_type == source.content_type,
        ContentRevision.content_slug == source.content_slug)) or source.version
    row = ContentRevision(course_slug=source.course_slug, content_type=source.content_type,
        content_slug=source.content_slug, version=latest + 1, status="draft",
        content_json=source.content_json, validation_report={}, review_feedback=f"Rollback draft copied from version {source.version}; validate and review before publishing.",
        created_by=user.id, created_at=utc_now())
    db.add(row)
    db.flush()
    _audit(db, user, "content_revision_rollback_draft_created", "content_revision", str(row.id), {"source_revision_id": str(source.id), "source_version": source.version, "new_version": row.version})
    db.commit()
    db.refresh(row)
    return {"revision": _revision_payload(row), "requires_validation_and_review": True}


@router.post("/api/me/analytics/events", status_code=status.HTTP_202_ACCEPTED)
def record_analytics_event(body: AnalyticsEventInput, user: User = Depends(require_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    preferences = db.scalar(select(LearningPreference).where(LearningPreference.user_id == user.id))
    if preferences is None or not preferences.analytics_enabled:
        return {"accepted": False, "reason": "analytics_opt_out"}
    # Keep a coarse 90-day event window. Rows contain no user ID, IP, answer or free-form text.
    now = utc_now()
    db.execute(delete(ProductAnalyticsEvent).where(ProductAnalyticsEvent.occurred_at < now - timedelta(days=90)))
    course_slug = body.course_slug.strip().lower() if body.course_slug else None
    if course_slug and not COURSE_SLUG_RE.fullmatch(course_slug):
        raise HTTPException(status_code=422, detail="Invalid course_slug.")
    lesson_slug = body.lesson_slug.strip().lower() if body.lesson_slug else None
    if lesson_slug and not SLUG_RE.fullmatch(lesson_slug):
        raise HTTPException(status_code=422, detail="Invalid lesson_slug.")
    item_key = body.item_key.strip().lower() if body.item_key else None
    if item_key and (not SLUG_RE.fullmatch(item_key)):
        raise HTTPException(status_code=422, detail="Invalid item_key.")
    outcome = body.outcome if body.outcome in {"success", "failure", "unknown", "loaded", "missing", "navigated_away"} else None
    db.add(ProductAnalyticsEvent(event_type=body.event_type, course_slug=course_slug,
        lesson_slug=lesson_slug, item_key=item_key, outcome=outcome, occurred_at=now))
    db.commit()
    return {"accepted": True}


@router.get("/api/editor/analytics/summary")
def analytics_summary(days: int = Query(default=30, ge=1, le=90), user: User = Depends(_require_editor), db: Session = Depends(get_db)) -> dict[str, Any]:
    cutoff = utc_now() - timedelta(days=days)
    rows = db.execute(select(ProductAnalyticsEvent.event_type, ProductAnalyticsEvent.course_slug,
        ProductAnalyticsEvent.item_key, ProductAnalyticsEvent.outcome,
        func.count(ProductAnalyticsEvent.id).label("count")).where(
        ProductAnalyticsEvent.occurred_at >= cutoff).group_by(ProductAnalyticsEvent.event_type,
        ProductAnalyticsEvent.course_slug, ProductAnalyticsEvent.item_key,
        ProductAnalyticsEvent.outcome).order_by(func.count(ProductAnalyticsEvent.id).desc())).all()
    daily_rows = db.execute(select(func.date(ProductAnalyticsEvent.occurred_at).label("day"),
        ProductAnalyticsEvent.event_type, func.count(ProductAnalyticsEvent.id).label("count")).where(
        ProductAnalyticsEvent.occurred_at >= cutoff).group_by(func.date(ProductAnalyticsEvent.occurred_at), ProductAnalyticsEvent.event_type).having(
        func.count(ProductAnalyticsEvent.id) >= 5).order_by(func.date(ProductAnalyticsEvent.occurred_at))).all()
    return {"window_days": days, "retention_days": 90,
        "events_by_dimension": [{"event_type": row.event_type, "course_slug": row.course_slug,
                                  "item_key": row.item_key, "outcome": row.outcome, "count": int(row.count)} for row in rows],
        "daily_counts": [{"day": str(row.day), "event_type": row.event_type, "count": int(row.count)} for row in daily_rows],
        "privacy": "Aggregates contain no user ID, raw IP, submitted code, answers or email. Groups with fewer than five events are omitted; this is an event-count threshold, not a unique-learner threshold. Retention cleanup is opportunistic on ingestion and summary requests."}


@router.get("/api/runner/status")
def runner_status() -> dict[str, Any]:
    """Expose only whether the isolated runner is configured, never its URL or secret."""
    configured = bool(
        (settings.runner_service_url or "").strip()
        and (settings.runner_service_token or "").strip()
    )
    return {
        "configured": configured,
        "supported_languages": ["python", "javascript"] if configured else [],
        "message": (
            "The isolated runner is configured. Sign in to submit a program."
            if configured
            else "The isolated runner is not configured yet. Browser HTML/CSS/JavaScript preview remains available."
        ),
    }


@router.post("/api/runner/jobs", status_code=status.HTTP_202_ACCEPTED)
async def create_runner_job(body: RunnerCreateInput, user: User = Depends(require_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    base_url = (settings.runner_service_url or "").strip().rstrip("/")
    token = settings.runner_service_token or ""
    if not base_url or not token:
        raise HTTPException(status_code=503, detail="The isolated runner service is not configured. Browser HTML/CSS/JavaScript preview remains available.")

    request_key = body.idempotency_key or uuid4().hex
    if body.idempotency_key:
        previous = db.scalar(
            select(RunnerJob).where(
                RunnerJob.user_id == user.id,
                RunnerJob.request_key == request_key,
            )
        )
        if previous is not None:
            return {"job": {"id": str(previous.id), "language": previous.language, "status": previous.status, "created_at": previous.created_at.isoformat()}}

    now = utc_now()
    db.execute(update(RunnerJob).where(
        RunnerJob.user_id == user.id,
        RunnerJob.status.in_(["queued", "running"]),
        RunnerJob.created_at < now - timedelta(minutes=15),
    ).values(status="expired", updated_at=now))
    db.execute(delete(RunnerJob).where(RunnerJob.user_id == user.id, RunnerJob.created_at < now - timedelta(days=7)))
    recent = db.scalar(select(func.count(RunnerJob.id)).where(RunnerJob.user_id == user.id, RunnerJob.created_at >= now - timedelta(minutes=1))) or 0
    active = db.scalar(select(func.count(RunnerJob.id)).where(RunnerJob.user_id == user.id, RunnerJob.status.in_(["queued", "running"]))) or 0
    if recent >= 8 or active >= 2:
        raise HTTPException(status_code=429, detail="Runner rate limit reached. Finish or wait for an existing job before starting another.")

    plan_id = effective_plan_id(db, user.id)
    allowance = int(plan_limits(plan_id)["code_executions_per_day"])
    reservation, duplicate = reserve_daily_usage(
        db, user, metric="code_execution", allowance=allowance,
        idempotency_key=request_key,
    )
    if duplicate:
        previous = db.scalar(
            select(RunnerJob).where(
                RunnerJob.user_id == user.id,
                RunnerJob.request_key == request_key,
            )
        )
        if previous is not None:
            return {"job": {"id": str(previous.id), "language": previous.language, "status": previous.status, "created_at": previous.created_at.isoformat()}}
        raise HTTPException(status_code=409, detail="This code execution request is already being processed. Check your runner status before retrying.")

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(
                f"{base_url}/v1/jobs",
                headers={"X-Runner-Key": token},
                json={
                    "owner_id": str(user.id),
                    "language": body.language,
                    "source": body.source,
                    "stdin": body.stdin,
                },
            )
    except httpx.HTTPError as exc:
        finalize_daily_usage(db, reservation.id, success=False)
        raise HTTPException(status_code=503, detail="The isolated runner service could not be reached. Your daily execution allowance was not consumed.") from exc
    if response.status_code >= 400:
        finalize_daily_usage(db, reservation.id, success=False)
        raise HTTPException(status_code=503, detail="The isolated runner service rejected this request. Your daily execution allowance was not consumed.")
    try:
        result = response.json()
    except ValueError as exc:
        finalize_daily_usage(db, reservation.id, success=False)
        raise HTTPException(status_code=502, detail="The runner service returned an invalid response. Your daily execution allowance was not consumed.") from exc
    external_id = result.get("job_id") if isinstance(result, dict) else None
    if not isinstance(external_id, str) or not external_id:
        finalize_daily_usage(db, reservation.id, success=False)
        raise HTTPException(status_code=502, detail="The runner service returned an invalid job reference. Your daily execution allowance was not consumed.")
    row = RunnerJob(
        user_id=user.id,
        external_job_id=external_id,
        request_key=request_key,
        language=body.language,
        status=str(result.get("status", "queued"))[:20],
        result_json={},
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    # Count the execution once, in the same DB transaction that records the accepted job.
    finalize_daily_usage(db, reservation.id, success=True, commit=False)
    db.commit()
    db.refresh(row)
    return {"job": {"id": str(row.id), "language": row.language, "status": row.status, "created_at": row.created_at.isoformat()}}


@router.get("/api/runner/jobs/{job_id}")
async def get_runner_job(job_id: UUID, user: User = Depends(require_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    row = db.scalar(select(RunnerJob).where(RunnerJob.id == job_id, RunnerJob.user_id == user.id))
    if row is None:
        raise HTTPException(status_code=404, detail="Runner job was not found.")
    base_url = (settings.runner_service_url or "").strip().rstrip("/")
    token = settings.runner_service_token or ""
    if not base_url or not token:
        raise HTTPException(status_code=503, detail="The isolated runner service is not configured.")
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(f"{base_url}/v1/jobs/{row.external_job_id}", headers={"X-Runner-Key": token, "X-CodeLeaf-User": str(user.id)})
        except httpx.HTTPError:
            raise HTTPException(status_code=503, detail="The isolated runner service could not be reached.")
    if response.status_code == 404:
        row.status = "expired"
        db.commit()
        return {"job": {"id": str(row.id), "language": row.language, "status": row.status, "result": {}}}
    if response.status_code >= 400:
        raise HTTPException(status_code=503, detail="The isolated runner service failed to return job status.")
    data = response.json()
    row.status = str(data.get("status", row.status))[:20]
    result = data.get("result") if isinstance(data.get("result"), dict) else {}
    row.result_json = result
    row.updated_at = utc_now()
    db.commit()
    return {"job": {"id": str(row.id), "language": row.language, "status": row.status, "result": result}}


@router.delete("/api/runner/jobs/{job_id}")
async def cancel_runner_job(job_id: UUID, user: User = Depends(require_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    row = db.scalar(select(RunnerJob).where(RunnerJob.id == job_id, RunnerJob.user_id == user.id))
    if row is None:
        raise HTTPException(status_code=404, detail="Runner job was not found.")
    base_url = (settings.runner_service_url or "").strip().rstrip("/")
    token = settings.runner_service_token or ""
    if not base_url or not token:
        raise HTTPException(status_code=503, detail="The isolated runner service is not configured.")
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.delete(f"{base_url}/v1/jobs/{row.external_job_id}", headers={"X-Runner-Key": token, "X-CodeLeaf-User": str(user.id)})
        except httpx.HTTPError:
            raise HTTPException(status_code=503, detail="The isolated runner service could not be reached.")
    if response.status_code >= 400 and response.status_code != 404:
        raise HTTPException(status_code=503, detail="The isolated runner service could not cancel this job.")
    row.status = "cancelled"
    row.updated_at = utc_now()
    db.commit()
    return {"ok": True, "status": row.status}
