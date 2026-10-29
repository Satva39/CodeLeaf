"""Plan, billing snapshot, saved workspace and daily quota contracts.

Run from backend/: python scripts/test_plan_entitlements.py
Uses an isolated temporary SQLite database; no live payment or AI provider is called.
"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

_TEMP = tempfile.TemporaryDirectory(prefix="codeleaf-plan-entitlements-")
os.environ["DATABASE_URL"] = f"sqlite:///{(Path(_TEMP.name) / 'plans.db').as_posix()}"
os.environ["APP_ENV"] = "development"
os.environ["JWT_SECRET"] = "plan-test-only-secret-never-use-in-production-2026"
os.environ["FRONTEND_ORIGINS"] = "http://localhost:5173"
os.environ["FRONTEND_BASE_URL"] = "http://localhost:5173"
for key in ("AI_API_BASE_URL", "AI_API_KEY", "AI_MODEL"):
    os.environ.pop(key, None)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import Response, HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select, func  # noqa: E402

from app.config import settings  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.auth_security import create_session  # noqa: E402
from app.models import Entitlement, PlanUsage, User, UsageReservation, SavedWorkspace  # noqa: E402
from app.plan_entitlements import (  # noqa: E402
    PLAN_DEFINITIONS, effective_plan_id, plan_limits, reserve_daily_usage, finalize_daily_usage,
)
import app.main as main_module  # noqa: E402
import jwt  # noqa: E402


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS {message}")


def make_user(suffix: str) -> User:
    with SessionLocal() as db:
        user = User(
            email=f"{suffix}-{uuid4().hex[:8]}@example.invalid",
            username=f"{suffix}_{uuid4().hex[:10]}",
            display_name=f"{suffix} learner",
            password_hash="test-only-hash",
            is_email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


def authenticate(client: TestClient, user_id) -> None:
    with SessionLocal() as db:
        user = db.get(User, user_id)
        response = Response()
        token = create_session(user, response, db)
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[main_module.TOKEN_ALGORITHM])
        csrf = claims["csrf"]
    client.cookies.set(main_module.SESSION_COOKIE, token)
    client.cookies.set("codeleaf_csrf", csrf)
    client.headers.update({"origin": "http://localhost:5173", "x-csrf-token": csrf})


def grant(user_id, plan_id: str, ends_at=None, status="active") -> None:
    with SessionLocal() as db:
        db.add(Entitlement(user_id=user_id, plan_id=plan_id, status=status, starts_at=datetime.now(timezone.utc) - timedelta(days=1), ends_at=ends_at))
        db.commit()


def main() -> None:
    Base.metadata.create_all(bind=engine)
    client = TestClient(main_module.app)
    try:
        check(set(PLAN_DEFINITIONS) == {"free", "pro", "max", "full_access"}, "all four plans exist in authoritative definitions")
        check([PLAN_DEFINITIONS[p]["amount_paise"] for p in ("free", "pro", "max", "full_access")] == [0, 29900, 69900, 4999900], "server plan prices match ₹0, ₹299/month, ₹699/month and ₹49,999 lifetime")
        limits = {key: plan_limits(key) for key in PLAN_DEFINITIONS}
        check([limits[p]["workspaces"] for p in limits] == [3, 25, 100, 200], "workspace limits match all four plans")
        check([limits[p]["code_executions_per_day"] for p in limits] == [50, 300, 1000, 1500], "daily supported-execution limits match all four plans")
        check([limits[p]["ai_requests_per_day"] for p in limits] == [0, 0, 100, 150], "AI request limits match all four plans")
        check([limits[p]["project_storage_bytes"] for p in limits] == [1024**3, 10*1024**3, 50*1024**3, 100*1024**3], "project-storage allowances match all four tiers")
        check([limits[p]["max_single_zip_bytes"] for p in limits] == [500*1024**2]*4, "individual ZIP cap is 500 MiB on every tier")
        check([limits[p]["ads_enabled"] for p in limits] == [True, True, False, False], "ad entitlement is enabled only for Free and Pro")
        check([limits[p]["xp_multiplier"] for p in limits] == [1.0, 1.0, 1.5, 1.5], "XP multiplier is 1× for Free/Pro and 1.5× for Max/Lifetime")

        user = make_user("plan_free")
        authenticate(client, user.id)
        snapshot = client.get("/api/me/entitlements")
        check(snapshot.status_code == 200 and snapshot.json()["current_plan"]["id"] == "free", "new account resolves to Free by default")
        check(snapshot.json()["usage"]["project_storage_bytes"]["limit"] == 1024 ** 3, "entitlement endpoint exposes configured Free storage allowance")
        denied_ai = client.post("/api/me/ai/tutor", json={"prompt": "Explain variables"}, headers={"Idempotency-Key": "free-ai-denied-1"})
        check(denied_ai.status_code == 403 and denied_ai.json()["detail"]["code"] == "FEATURE_REQUIRES_UPGRADE", "Free user cannot call the AI tutor directly")
        denied_analytics = client.get("/api/me/analytics/advanced")
        check(denied_analytics.status_code == 403, "Free user cannot call advanced analytics directly")

        for idx in range(3):
            created = client.post("/api/me/workspaces", json={"name": f"Workspace {idx}", "language": "python", "files": [{"id": f"f-{idx}", "name": "main.py", "language": "python", "content": "print('hello')"}]})
            check(created.status_code == 201, f"Free account can save workspace {idx + 1}")
        over = client.post("/api/me/workspaces", json={"name": "Workspace over limit", "language": "python", "files": [{"id": "over", "name": "main.py", "language": "python", "content": "print(0)"}]})
        check(over.status_code == 409 and over.json()["detail"]["code"] == "WORKSPACE_LIMIT_REACHED", "saved-workspace count is enforced server-side")
        listing = client.get("/api/me/workspaces")
        check(listing.status_code == 200 and listing.json()["usage"] == {"used": 3, "limit": 3}, "saved-workspace usage reports actual persisted records")
        first_workspace = listing.json()["items"][0]["id"]
        replaced = client.put(f"/api/me/workspaces/{first_workspace}", json={"name": "Renamed workspace", "language": "python", "files": [{"id": "file", "name": "main.py", "language": "python", "content": "print('updated')"}]})
        check(replaced.status_code == 200 and replaced.json()["workspace"]["name"] == "Renamed workspace", "workspace updates are scoped to and persisted for the owner")
        foreign = make_user("plan_other")
        other_workspace = None
        with SessionLocal() as db:
            db.add(SavedWorkspace(user_id=foreign.id, name="Private", language="python", files=[{"id":"private","name":"main.py","language":"python","content":"secret"}], byte_size=20))
            db.commit()
            other_workspace = db.scalar(select(SavedWorkspace.id).where(SavedWorkspace.user_id == foreign.id))
        foreign_access = client.delete(f"/api/me/workspaces/{other_workspace}")
        check(foreign_access.status_code == 404, "a user cannot access or delete another user's workspace")

        pro_user = make_user("plan_pro")
        grant(pro_user.id, "pro")
        with SessionLocal() as db:
            check(effective_plan_id(db, pro_user.id) == "pro", "verified Pro entitlement is resolved by backend state")
        # User without configured provider receives a truthful unavailable response, not mocked output.
        max_user = make_user("plan_max")
        grant(max_user.id, "max")
        client.cookies.clear()
        authenticate(client, max_user.id)
        unavailable_ai = client.post("/api/me/ai/tutor", json={"prompt": "Explain loops"}, headers={"Idempotency-Key": "max-ai-no-provider-1"})
        check(unavailable_ai.status_code == 503 and unavailable_ai.json()["detail"]["code"] == "AI_PROVIDER_UNAVAILABLE", "Max AI stays disabled when a real provider is not configured")

        expired_user = make_user("plan_expired")
        grant(expired_user.id, "max", datetime.now(timezone.utc) - timedelta(days=1))
        with SessionLocal() as db:
            check(effective_plan_id(db, expired_user.id) == "free", "expired membership falls back to Free")
        halted_current_period = make_user("plan_halted_current_period")
        grant(halted_current_period.id, "pro", datetime.now(timezone.utc) + timedelta(days=3), status="past_due")
        with SessionLocal() as db:
            check(effective_plan_id(db, halted_current_period.id) == "pro", "halted subscription retains already-paid access through its recorded period end")
        halted_expired_period = make_user("plan_halted_expired_period")
        grant(halted_expired_period.id, "pro", datetime.now(timezone.utc) - timedelta(seconds=1), status="past_due")
        with SessionLocal() as db:
            check(effective_plan_id(db, halted_expired_period.id) == "free", "halted subscription cannot grant access beyond its recorded period end")
        halted_without_end = make_user("plan_halted_no_end")
        grant(halted_without_end.id, "pro", None, status="past_due")
        with SessionLocal() as db:
            check(effective_plan_id(db, halted_without_end.id) == "free", "past-due status without a period end never grants indefinite access")
        lifetime_user = make_user("plan_lifetime")
        grant(lifetime_user.id, "full_access", None)
        with SessionLocal() as db:
            check(effective_plan_id(db, lifetime_user.id) == "full_access", "lifetime entitlement remains effective with no monthly expiry")

        # Daily quota reservations are concurrency/idempotency accounting, tested with one slot.
        quota_user = make_user("plan_quota")
        with SessionLocal() as db:
            first, duplicate = reserve_daily_usage(db, quota_user, metric="test_operation", allowance=1, idempotency_key="quota-key-1")
            check(not duplicate and first.status == "reserved", "first quota operation reserves an allowance")
            try:
                reserve_daily_usage(db, quota_user, metric="test_operation", allowance=1, idempotency_key="quota-key-2")
                raise AssertionError("Expected daily usage quota to be enforced")
            except HTTPException as exc:
                check(exc.status_code == 429 and exc.detail["code"] == "DAILY_USAGE_LIMIT_REACHED", "concurrent reserved operations cannot overspend a daily quota")
                db.rollback()
            finalize_daily_usage(db, first.id, success=True, commit=True)
            used = db.scalar(select(PlanUsage.used_count).where(PlanUsage.user_id == quota_user.id, PlanUsage.metric == "test_operation"))
            check(used == 1, "successful operation increments daily usage exactly once")
            again, is_duplicate = reserve_daily_usage(db, quota_user, metric="test_operation", allowance=1, idempotency_key="quota-key-1")
            check(is_duplicate and again.status == "consumed", "retry with the same idempotency key does not reserve or consume twice")

        print("Plan entitlement tests passed; isolated SQLite database and no live payment/AI services were used.")
    finally:
        client.close()
        engine.dispose()
        _TEMP.cleanup()


if __name__ == "__main__":
    main()
