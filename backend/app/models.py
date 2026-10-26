"""Starter PostgreSQL schema. Create a proper Alembic migration before production."""

from datetime import date, datetime, timezone
from uuid import uuid4
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid
from .db import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    email: Mapped[str] = mapped_column(
        String(320), unique=True, index=True, nullable=False
    )
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    username: Mapped[str] = mapped_column(
        String(40), unique=True, index=True, nullable=False
    )
    avatar: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    theme: Mapped[str] = mapped_column(String(20), default="dark", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Existing accounts are backfilled as verified by migration; new registrations opt out.
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Privileges are assigned through trusted operations, never through profile payloads.
    role: Mapped[str] = mapped_column(String(20), default="learner", nullable=False)


class Course(Base):
    __tablename__ = "courses"
    id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    category: Mapped[str] = mapped_column(
        String(100), default="Programming", nullable=False
    )
    level: Mapped[str] = mapped_column(String(30), default="Beginner", nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Module(Base):
    __tablename__ = "course_modules"
    id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    course_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), index=True
    )
    slug: Mapped[str] = mapped_column(String(140), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    level: Mapped[str] = mapped_column(String(30), default="Core", nullable=False)
    __table_args__ = (
        UniqueConstraint("course_id", "slug", name="uq_module_course_slug"),
    )


class Lesson(Base):
    __tablename__ = "lessons"
    id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    module_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("course_modules.id", ondelete="CASCADE"),
        index=True,
    )
    slug: Mapped[str] = mapped_column(String(160), nullable=False)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    content: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    __table_args__ = (
        UniqueConstraint("module_id", "slug", name="uq_lesson_module_slug"),
    )


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    lesson_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), index=True
    )
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_progress_user_lesson"),
    )


class Exercise(Base):
    """An individually managed, imported exercise attached to one lesson."""

    __tablename__ = "exercises"
    id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    lesson_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), index=True
    )
    slug: Mapped[str] = mapped_column(String(160), nullable=False)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    exercise_type: Mapped[str] = mapped_column(
        String(40), default="short_answer", nullable=False
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    starter: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    public_tests: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    acceptance_criteria: Mapped[list] = mapped_column(
        JSON, default=list, nullable=False
    )
    hints: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    solution: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    grading_config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(30), default="easy", nullable=False)
    xp_points: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    __table_args__ = (
        UniqueConstraint("lesson_id", "slug", name="uq_exercise_lesson_slug"),
    )


class ExerciseProgress(Base):
    __tablename__ = "exercise_progress"
    id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    exercise_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("exercises.id", ondelete="CASCADE"), index=True
    )
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    __table_args__ = (
        UniqueConstraint(
            "user_id", "exercise_id", name="uq_exercise_progress_user_exercise"
        ),
    )


class UserActivityDay(Base):
    """One row per active learner-local calendar day, used to compute streaks."""

    __tablename__ = "user_activity_days"
    id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    activity_date: Mapped[date] = mapped_column(Date, nullable=False)
    timezone_name: Mapped[str] = mapped_column(
        String(80), default="UTC", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False
    )
    __table_args__ = (
        UniqueConstraint("user_id", "activity_date", name="uq_activity_user_date"),
    )


class Bookmark(Base):
    __tablename__ = "bookmarks"
    id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    lesson_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False
    )
    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_bookmark_user_lesson"),
    )


class XPTransaction(Base):
    __tablename__ = "xp_transactions"
    id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_id: Mapped[str] = mapped_column(String(160), nullable=False)
    base_points: Mapped[int] = mapped_column(Integer, nullable=False)
    awarded_points: Mapped[int] = mapped_column(Integer, nullable=False)
    boost_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False
    )
    __table_args__ = (
        UniqueConstraint(
            "user_id", "source_type", "source_id", name="uq_xp_event_once"
        ),
    )


class ExamAttempt(Base):
    __tablename__ = "exam_attempts"
    id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    course_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), index=True
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    answers_summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class PracticalExamAttempt(Base):
    """Server-owned practical assessment attempt linked to a passed MCQ attempt."""

    __tablename__ = "practical_exam_attempts"
    id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    course_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), index=True
    )
    mcq_attempt_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("exam_attempts.id", ondelete="CASCADE"), index=True
    )
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    answers_summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Certificate(Base):
    __tablename__ = "certificates"
    id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    public_id: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    user_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    course_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), index=True
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    exam_attempt_id: Mapped[object | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("exam_attempts.id"), nullable=True
    )


class PaymentRecord(Base):
    __tablename__ = "payment_records"
    id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    plan_id: Mapped[str] = mapped_column(String(40), nullable=False)
    amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    kind: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # order or subscription
    status: Mapped[str] = mapped_column(String(40), default="created", nullable=False)
    provider_order_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True
    )
    provider_subscription_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True
    )
    provider_payment_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True
    )
    provider_payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )


class Entitlement(Base):
    __tablename__ = "entitlements"
    id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    plan_id: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    source_payment_id: Mapped[object | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("payment_records.id"), nullable=True
    )
    provider_subscription_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False
    )
    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False
    )


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    provider_event_id: Mapped[str] = mapped_column(
        String(150), unique=True, index=True, nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class ProjectSubmission(Base):
    __tablename__ = "project_submissions"
    id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    project_slug: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    code_bundle: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    visibility: Mapped[str] = mapped_column(
        String(20), default="private", nullable=False
    )
    portfolio_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, nullable=False
    )


Index("ix_payment_plan_status", PaymentRecord.plan_id, PaymentRecord.status)


class AuthSession(Base):
    """Revocable cookie/JWT session; only a digest of the complete token is persisted."""
    __tablename__ = "auth_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AccountActionToken(Base):
    """Single-use, expiring email-verification/password-reset token metadata."""
    __tablename__ = "account_action_tokens"
    id: Mapped[object] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    purpose: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    target_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuthRateLimitEvent(Base):
    """Short-lived rate-limit keys; raw email addresses and IPs are not stored."""
    __tablename__ = "auth_rate_limit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

Index("ix_auth_sessions_user_revoked", AuthSession.user_id, AuthSession.revoked_at)
Index("ix_auth_tokens_user_purpose", AccountActionToken.user_id, AccountActionToken.purpose)
Index("ix_auth_rate_events_key_time", AuthRateLimitEvent.key_hash, AuthRateLimitEvent.occurred_at)


class LearningPreference(Base):
    """Private learner controls for review cadence, timezone and analytics opt-in."""
    __tablename__ = "learning_preferences"
    id: Mapped[object] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[object] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)
    timezone_name: Mapped[str] = mapped_column(String(80), default="UTC", nullable=False)
    review_frequency_days: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    daily_review_limit: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    analytics_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)


class ReviewSchedule(Base):
    """Spaced-retrieval state grounded in server-recorded lesson/exercise outcomes."""
    __tablename__ = "review_schedules"
    id: Mapped[object] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[object] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    course_slug: Mapped[str] = mapped_column(String(100), nullable=False)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)
    item_slug: Mapped[str] = mapped_column(String(180), nullable=False)
    interval_days: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    ease_factor: Mapped[float] = mapped_column(default=2.3, nullable=False)
    repetitions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_result: Mapped[str] = mapped_column(String(20), default="unknown", nullable=False)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True, nullable=False)
    dismissed_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (UniqueConstraint("user_id", "course_slug", "item_type", "item_slug", name="uq_review_item_per_user"),)


class ContentRevision(Base):
    """Versioned editor staging record; live course files still use the guarded importer."""
    __tablename__ = "content_revisions"
    id: Mapped[object] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    course_slug: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    content_type: Mapped[str] = mapped_column(String(30), nullable=False)
    content_slug: Mapped[str] = mapped_column(String(180), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True, nullable=False)
    content_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    validation_report: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    review_feedback: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_by: Mapped[object] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    reviewed_by: Mapped[object | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    published_by: Mapped[object | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (UniqueConstraint("course_slug", "content_type", "content_slug", "version", name="uq_content_revision_version"),)


class AuditLog(Base):
    """Minimal, append-only administrative audit record."""
    __tablename__ = "audit_logs"
    id: Mapped[object] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    actor_user_id: Mapped[object | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(40), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(180), nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True, nullable=False)


class ProductAnalyticsEvent(Base):
    """Privacy-minimized product event: no user identifier, IP address or free-form payload."""
    __tablename__ = "product_analytics_events"
    id: Mapped[object] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    course_slug: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    lesson_slug: Mapped[str | None] = mapped_column(String(180), nullable=True)
    item_key: Mapped[str | None] = mapped_column(String(180), nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(30), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True, nullable=False)


class RunnerJob(Base):
    """Owned reference to an isolated external runner job; source code is not persisted."""
    __tablename__ = "runner_jobs"
    id: Mapped[object] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[object] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    external_job_id: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="queued", nullable=False)
    result_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)
