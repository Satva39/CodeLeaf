"""Authoritative CodeLeaf plan definitions, effective entitlements and quota accounting.

Usage windows are UTC calendar days. All paid access is derived from verified database
entitlements; caller-supplied plan names are never trusted.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import (
    Entitlement,
    PlanUsage,
    ProjectSubmission,
    SavedWorkspace,
    SavedSnippet,
    UsageReservation,
    User,
)

MIB = 1024 * 1024
GIB = 1024 * MIB
MAX_SINGLE_ZIP_BYTES = 500 * MIB

FEATURES_FREE = {
    "published_learning": True,
    "standard_exercises": True,
    "learning_progress": True,
    "course_exams": True,
    "earned_certificates": True,
    "public_projects": True,
    "portfolio": True,
    "saved_workspaces": True,
    "browser_playground": True,
    "standard_analytics": True,
    "advanced_analytics": False,
    "personalized_recommendations": False,
    "premium_practice": False,
    "project_planning": False,
    "premium_projects": False,
    "ai_tutor": False,
    "ai_code_review": False,
    "ad_free": False,
    "priority_support": False,
    "leaderboards": False,
}
FEATURES_PRO = {
    **FEATURES_FREE,
    "advanced_analytics": True,
    "personalized_recommendations": True,
    "premium_practice": True,
    "project_planning": True,
    "leaderboards": True,
}
FEATURES_MAX = {
    **FEATURES_PRO,
    "premium_projects": True,
    "ai_tutor": True,
    "ai_code_review": True,
    "ad_free": True,
    "priority_support": True,
}

PLAN_DEFINITIONS: dict[str, dict[str, Any]] = {
    "free": {
        "title": "Free",
        "amount_paise": 0,
        "billing": "free",
        "description": "A complete foundation for learning and practicing.",
        "limits": {
            "max_single_zip_bytes": MAX_SINGLE_ZIP_BYTES,
            "project_storage_bytes": 1 * GIB,
            "workspaces": 3,
            "saved_snippets": 10,
            "code_executions_per_day": 50,
            "ai_requests_per_day": 0,
            "xp_multiplier": 1.0,
            "ads_enabled": True,
        },
        "features": FEATURES_FREE,
    },
    "pro": {
        "title": "Pro",
        "amount_paise": 29_900,
        "billing": "monthly",
        "description": "More structure, analytics and room for projects.",
        "limits": {
            "max_single_zip_bytes": MAX_SINGLE_ZIP_BYTES,
            "project_storage_bytes": 10 * GIB,
            "workspaces": 25,
            "saved_snippets": 100,
            "code_executions_per_day": 300,
            "ai_requests_per_day": 0,
            "xp_multiplier": 1.0,
            "ads_enabled": True,
        },
        "features": FEATURES_PRO,
    },
    "max": {
        "title": "Max",
        "amount_paise": 69_900,
        "billing": "monthly",
        "description": "Ad-free learning with advanced projects and AI tools when configured.",
        "limits": {
            "max_single_zip_bytes": MAX_SINGLE_ZIP_BYTES,
            "project_storage_bytes": 50 * GIB,
            "workspaces": 100,
            "saved_snippets": 500,
            "code_executions_per_day": 1_000,
            "ai_requests_per_day": 100,
            "xp_multiplier": 1.5,
            "ads_enabled": False,
        },
        "features": FEATURES_MAX,
    },
    "full_access": {
        "title": "Full Access",
        "amount_paise": 4_999_900,
        "billing": "lifetime",
        "description": "One-time lifetime access to all standard individual Pro and Max features.",
        "limits": {
            "max_single_zip_bytes": MAX_SINGLE_ZIP_BYTES,
            "project_storage_bytes": 100 * GIB,
            "workspaces": 200,
            "saved_snippets": 1_000,
            "code_executions_per_day": 1_500,
            "ai_requests_per_day": 150,
            "xp_multiplier": 1.5,
            "ads_enabled": False,
        },
        "features": FEATURES_MAX,
    },
}

PLAN_PRIORITY = {"free": 0, "pro": 1, "max": 2, "full_access": 3}
FEATURE_REQUIRED_PLAN = {
    "advanced_analytics": "pro",
    "personalized_recommendations": "pro",
    "premium_practice": "pro",
    "project_planning": "pro",
    "premium_projects": "max",
    "ai_tutor": "max",
    "ai_code_review": "max",
    "ad_free": "max",
    "priority_support": "max",
    "leaderboards": "pro",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def active_entitlements(db: Session, user_id: UUID) -> list[Entitlement]:
    """Return valid paid records; a missing/expired record never grants paid access."""
    now = utc_now()
    rows = db.scalars(
        select(Entitlement).where(
            Entitlement.user_id == user_id,
            Entitlement.status.in_(["active", "past_due"]),
        )
    ).all()
    valid = []
    for row in rows:
        end = normalize_datetime(row.ends_at) if row.ends_at is not None else None
        # A failed renewal does not create a new paid period, but it should not
        # revoke time the customer has already paid for. Halted memberships are
        # honored only through their recorded period end; without an end date,
        # past_due is never an indefinite grant.
        if row.status == "active" and (end is None or end > now):
            valid.append(row)
        elif row.status == "past_due" and end is not None and end > now:
            valid.append(row)
    return valid


def effective_plan_id(db: Session, user_id: UUID) -> str:
    active = active_entitlements(db, user_id)
    if not active:
        return "free"
    return max(
        (row.plan_id for row in active if row.plan_id in PLAN_PRIORITY),
        key=lambda item: PLAN_PRIORITY[item],
        default="free",
    )


def plan_features(plan_id: str) -> dict[str, bool]:
    return dict(PLAN_DEFINITIONS.get(plan_id, PLAN_DEFINITIONS["free"])["features"])


def plan_limits(plan_id: str) -> dict[str, Any]:
    return dict(PLAN_DEFINITIONS.get(plan_id, PLAN_DEFINITIONS["free"])["limits"])


def require_feature(db: Session, user: User, feature: str) -> str:
    plan_id = effective_plan_id(db, user.id)
    enabled = plan_features(plan_id).get(feature, False)
    if not enabled:
        required = FEATURE_REQUIRED_PLAN.get(feature, "max")
        raise HTTPException(
            status_code=403,
            detail={
                "code": "FEATURE_REQUIRES_UPGRADE",
                "feature": feature,
                "current_plan": plan_id,
                "required_plan": required,
                "upgrade_url": "/plans",
                "message": f"This feature requires the {PLAN_DEFINITIONS[required]['title']} plan or higher.",
            },
        )
    return plan_id


def lock_user_for_quota(db: Session, user_id: UUID) -> None:
    """Serialize quota-changing operations for the same user on PostgreSQL."""
    db.scalar(select(User.id).where(User.id == user_id).with_for_update())


def total_storage_used(db: Session, user_id: UUID) -> int:
    archive_bytes = db.scalar(
        select(func.coalesce(func.sum(ProjectSubmission.stored_bytes), 0)).where(
            ProjectSubmission.user_id == user_id
        )
    ) or 0
    workspace_bytes = db.scalar(
        select(func.coalesce(func.sum(SavedWorkspace.byte_size), 0)).where(
            SavedWorkspace.user_id == user_id
        )
    ) or 0
    snippet_bytes = db.scalar(
        select(func.coalesce(func.sum(SavedSnippet.byte_size), 0)).where(
            SavedSnippet.user_id == user_id
        )
    ) or 0
    return int(archive_bytes) + int(workspace_bytes) + int(snippet_bytes)


def ensure_storage_capacity(
    db: Session,
    user: User,
    *,
    incoming_bytes: int,
    replacing_workspace_id: UUID | None = None,
    replacing_snippet_id: UUID | None = None,
) -> dict[str, int]:
    if incoming_bytes < 0:
        raise ValueError("incoming_bytes must not be negative")
    lock_user_for_quota(db, user.id)
    plan_id = effective_plan_id(db, user.id)
    limit = int(plan_limits(plan_id)["project_storage_bytes"])
    current = total_storage_used(db, user.id)
    if replacing_workspace_id is not None:
        old_size = db.scalar(
            select(SavedWorkspace.byte_size).where(
                SavedWorkspace.id == replacing_workspace_id,
                SavedWorkspace.user_id == user.id,
            )
        ) or 0
        current = max(0, current - int(old_size))
    if replacing_snippet_id is not None:
        old_size = db.scalar(
            select(SavedSnippet.byte_size).where(
                SavedSnippet.id == replacing_snippet_id,
                SavedSnippet.user_id == user.id,
            )
        ) or 0
        current = max(0, current - int(old_size))
    projected = current + incoming_bytes
    if projected > limit:
        raise HTTPException(
            status_code=413,
            detail={
                "code": "PROJECT_STORAGE_LIMIT_REACHED",
                "current_plan": plan_id,
                "allowance_bytes": limit,
                "used_bytes": current,
                "requested_bytes": incoming_bytes,
                "upgrade_url": "/plans",
                "message": "This save would exceed your plan's project-storage allowance. Existing work is preserved; free space or upgrade your plan.",
            },
        )
    return {"plan_id": plan_id, "allowance_bytes": limit, "used_bytes": current}


def get_plan_usage_row(
    db: Session, user_id: UUID, metric: str, window_start: date
) -> PlanUsage | None:
    return db.scalar(
        select(PlanUsage).where(
            PlanUsage.user_id == user_id,
            PlanUsage.metric == metric,
            PlanUsage.window_start == window_start,
        )
    )


def reserve_daily_usage(
    db: Session,
    user: User,
    *,
    metric: str,
    allowance: int,
    idempotency_key: str,
    now: datetime | None = None,
) -> tuple[UsageReservation, bool]:
    """Reserve one actual provider operation. Returns (reservation, duplicate).

    Call before an external request, then finalize with success=True only after the
    provider accepts/completes it. Expired reservations are automatically released.
    """
    now = normalize_datetime(now or utc_now())
    window = now.date()
    lock_user_for_quota(db, user.id)

    existing = db.scalar(
        select(UsageReservation).where(
            UsageReservation.user_id == user.id,
            UsageReservation.metric == metric,
            UsageReservation.idempotency_key == idempotency_key,
        ).with_for_update()
    )
    if existing is not None and existing.status == "consumed":
        return existing, True
    if (
        existing is not None
        and existing.status == "reserved"
        and normalize_datetime(existing.expires_at) > now
    ):
        return existing, True

    db.query(UsageReservation).filter(
        UsageReservation.user_id == user.id,
        UsageReservation.metric == metric,
        UsageReservation.status == "reserved",
        UsageReservation.expires_at <= now,
    ).update({UsageReservation.status: "released", UsageReservation.updated_at: now}, synchronize_session=False)

    usage = db.scalar(
        select(PlanUsage).where(
            PlanUsage.user_id == user.id,
            PlanUsage.metric == metric,
            PlanUsage.window_start == window,
        ).with_for_update()
    )
    if usage is None:
        usage = PlanUsage(
            user_id=user.id, metric=metric, window_start=window, used_count=0,
            updated_at=now,
        )
        db.add(usage)
        db.flush()

    reserved_count = db.scalar(
        select(func.count(UsageReservation.id)).where(
            UsageReservation.user_id == user.id,
            UsageReservation.metric == metric,
            UsageReservation.window_start == window,
            UsageReservation.status == "reserved",
            UsageReservation.expires_at > now,
            *([UsageReservation.id != existing.id] if existing is not None else []),
        )
    ) or 0
    if allowance <= 0 or int(usage.used_count) + int(reserved_count) >= allowance:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "DAILY_USAGE_LIMIT_REACHED",
                "metric": metric,
                "current_plan": effective_plan_id(db, user.id),
                "allowance": allowance,
                "used": int(usage.used_count),
                "reserved": int(reserved_count),
                "resets_at": (datetime.combine(window + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)).isoformat(),
                "upgrade_url": "/plans",
                "message": "The daily allowance for this feature has been reached. Usage resets at 00:00 UTC.",
            },
        )

    if existing is None:
        existing = UsageReservation(
            user_id=user.id,
            metric=metric,
            window_start=window,
            idempotency_key=idempotency_key,
            status="reserved",
            expires_at=now + timedelta(minutes=15),
            created_at=now,
            updated_at=now,
        )
        db.add(existing)
    else:
        existing.window_start = window
        existing.status = "reserved"
        existing.expires_at = now + timedelta(minutes=15)
        existing.updated_at = now
    db.commit()
    db.refresh(existing)
    return existing, False


def finalize_daily_usage(
    db: Session,
    reservation_id: UUID,
    *,
    success: bool,
    commit: bool = True,
) -> None:
    reservation = db.scalar(
        select(UsageReservation).where(
            UsageReservation.id == reservation_id
        ).with_for_update()
    )
    if reservation is None or reservation.status != "reserved":
        return
    if success:
        usage = db.scalar(
            select(PlanUsage).where(
                PlanUsage.user_id == reservation.user_id,
                PlanUsage.metric == reservation.metric,
                PlanUsage.window_start == reservation.window_start,
            ).with_for_update()
        )
        if usage is None:
            usage = PlanUsage(
                user_id=reservation.user_id,
                metric=reservation.metric,
                window_start=reservation.window_start,
                used_count=0,
            )
            db.add(usage)
        usage.used_count += 1
        usage.updated_at = utc_now()
        reservation.status = "consumed"
    else:
        reservation.status = "released"
    reservation.updated_at = utc_now()
    if commit:
        db.commit()


def build_plan_snapshot(db: Session, user: User) -> dict[str, Any]:
    now = utc_now()
    plan_id = effective_plan_id(db, user.id)
    definition = PLAN_DEFINITIONS[plan_id]
    limits = plan_limits(plan_id)
    features = plan_features(plan_id)
    usage_date = now.date()

    def used(metric: str) -> int:
        row = get_plan_usage_row(db, user.id, metric, usage_date)
        return int(row.used_count) if row else 0

    workspace_count = db.scalar(
        select(func.count(SavedWorkspace.id)).where(SavedWorkspace.user_id == user.id)
    ) or 0
    snippet_count = db.scalar(
        select(func.count(SavedSnippet.id)).where(SavedSnippet.user_id == user.id)
    ) or 0
    storage_used = total_storage_used(db, user.id)
    entitlements = active_entitlements(db, user.id)
    billing_period_end = max(
        (normalize_datetime(e.ends_at) for e in entitlements if e.ends_at is not None),
        default=None,
    )
    return {
        "current_plan": {
            "id": plan_id,
            "title": definition["title"],
            "billing": definition["billing"],
            "amount_paise": definition["amount_paise"],
            "period_ends_at": billing_period_end.isoformat() if billing_period_end else None,
            "lifetime": plan_id == "full_access",
        },
        "features": features,
        "limits": limits,
        "usage": {
            "date": usage_date.isoformat(),
            "timezone": "UTC",
            "workspaces": {"used": int(workspace_count), "limit": limits["workspaces"]},
            "saved_snippets": {"used": int(snippet_count), "limit": limits["saved_snippets"]},
            "project_storage_bytes": {"used": storage_used, "limit": limits["project_storage_bytes"]},
            "code_executions_per_day": {"used": used("code_execution"), "limit": limits["code_executions_per_day"]},
            "ai_requests_per_day": {"used": used("ai_request"), "limit": limits["ai_requests_per_day"]},
        },
        "available_plans": {
            key: {
                "title": value["title"],
                "amount_paise": value["amount_paise"],
                "currency": "INR",
                "billing": value["billing"],
                "limits": dict(value["limits"]),
                "features": dict(value["features"]),
                "description": value["description"],
            }
            for key, value in PLAN_DEFINITIONS.items()
        },
    }
