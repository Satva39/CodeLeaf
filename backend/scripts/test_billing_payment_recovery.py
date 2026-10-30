"""Regression tests for unpaid and verified Razorpay billing states.

Run from backend/: python scripts/test_billing_payment_recovery.py
All payment-provider calls are mocked; this script never contacts Razorpay.
"""
from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

_TEMP = tempfile.TemporaryDirectory(prefix="codeleaf-billing-recovery-")
os.environ["DATABASE_URL"] = f"sqlite:///{(Path(_TEMP.name) / 'billing.db').as_posix()}"
os.environ["APP_ENV"] = "development"
os.environ["JWT_SECRET"] = "billing-recovery-test-only-secret-not-for-production-2026"
os.environ["FRONTEND_ORIGINS"] = "http://localhost:5173"
os.environ["FRONTEND_BASE_URL"] = "http://localhost:5173"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import Response  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.auth_security import create_session  # noqa: E402
from app.config import settings  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.models import Entitlement, PaymentRecord, User  # noqa: E402
import app.main as main_module  # noqa: E402
import jwt  # noqa: E402


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS {message}")


def make_user(label: str) -> User:
    with SessionLocal() as db:
        user = User(
            email=f"{label}-{uuid4().hex[:8]}@example.invalid",
            username=f"{label}_{uuid4().hex[:10]}",
            display_name=f"{label} learner",
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
        claims = jwt.decode(
            token, settings.jwt_secret, algorithms=[main_module.TOKEN_ALGORITHM]
        )
    client.cookies.clear()
    client.cookies.set(main_module.SESSION_COOKIE, token)
    client.cookies.set("codeleaf_csrf", claims["csrf"])
    client.headers.update({
        "origin": "http://localhost:5173",
        "x-csrf-token": claims["csrf"],
    })


def main() -> None:
    Base.metadata.create_all(bind=engine)
    old_provider = main_module.razorpay_request
    settings.razorpay_key_id = "rzp_test_billing_recovery"
    settings.razorpay_key_secret = "billing-recovery-provider-test-secret"
    settings.razorpay_webhook_secret = "billing-recovery-webhook-test-secret"
    settings.razorpay_pro_plan_id = "plan_pro_test"
    settings.razorpay_max_plan_id = "plan_max_test"

    provider_calls: list[tuple[str, str, dict | None]] = []
    future = datetime.now(timezone.utc) + timedelta(days=20)
    current_start = int((datetime.now(timezone.utc) - timedelta(days=10)).timestamp())
    current_end = int(future.timestamp())
    expires_later = int((datetime.now(timezone.utc) + timedelta(days=1)).timestamp())

    async def fake_provider(method: str, path: str, payload=None):
        provider_calls.append((method, path, payload))
        if method == "GET" and path == "/orders/order-pending-full":
            return {
                "id": "order-pending-full",
                "status": "created",
                "amount": 4_999_900,
                "currency": "INR",
            }
        if method == "GET" and path == "/subscriptions/sub-pending-pro":
            return {
                "id": "sub-pending-pro",
                "status": "created",
                "plan_id": "plan_pro_test",
                "expire_by": expires_later,
            }
        if method == "GET" and path == "/subscriptions/sub-pending-pro-cancel":
            return {
                "id": "sub-pending-pro-cancel",
                "status": "created",
                "plan_id": "plan_pro_test",
            }
        if method == "POST" and path == "/subscriptions/sub-pending-pro-cancel/cancel":
            return {"id": "sub-pending-pro-cancel", "status": "cancelled"}
        if method == "GET" and path == "/subscriptions/sub-authenticated-pro":
            return {
                "id": "sub-authenticated-pro",
                "status": "authenticated",
                "plan_id": "plan_pro_test",
            }
        if method == "POST" and path == "/subscriptions/sub-authenticated-pro/cancel":
            return {"id": "sub-authenticated-pro", "status": "cancelled"}
        if method == "GET" and path == "/subscriptions/sub-active-pro":
            return {
                "id": "sub-active-pro",
                "status": "active",
                "plan_id": "plan_pro_test",
                "current_start": current_start,
                "current_end": current_end,
            }
        if method == "POST" and path == "/subscriptions/sub-active-pro/cancel":
            return {"id": "sub-active-pro", "status": "active"}
        raise AssertionError(f"Unexpected mocked Razorpay request: {method} {path} {payload}")

    main_module.razorpay_request = fake_provider
    client = TestClient(main_module.app)
    try:
        # A created order and subscription are pending checkouts, never memberships.
        unpaid_user = make_user("unpaid")
        with SessionLocal() as db:
            db.add_all([
                PaymentRecord(
                    user_id=unpaid_user.id,
                    plan_id="full_access",
                    amount_paise=4_999_900,
                    currency="INR",
                    kind="order",
                    status="created",
                    provider_order_id="order-pending-full",
                ),
                PaymentRecord(
                    user_id=unpaid_user.id,
                    plan_id="pro",
                    amount_paise=29_900,
                    currency="INR",
                    kind="subscription",
                    status="created",
                    provider_subscription_id="sub-pending-pro",
                    provider_payload={"provider_plan_id": "plan_pro_test"},
                ),
            ])
            db.commit()
        authenticate(client, unpaid_user.id)
        billing = client.get("/api/me/billing")
        payload = billing.json()
        check(billing.status_code == 200, "billing snapshot loads for an authenticated account")
        check(payload["entitlements"] == [] and payload["subscriptions"] == [], "unpaid created records are not shown as active memberships or renewals")
        pending = payload["pending_checkouts"]
        check({item["plan_id"] for item in pending} == {"pro", "full_access"}, "unfinished Pro and Full Access checkouts are listed separately")
        check(all(item["state"] == "awaiting_payment" for item in pending), "unpaid attempts are explicitly labelled as awaiting payment")

        # Retry the Full Access button: the existing open order is reused.
        full_resume = client.post("/api/payments/create", json={"plan_id": "full_access"})
        check(
            full_resume.status_code == 200
            and full_resume.json()["order_id"] == "order-pending-full"
            and full_resume.json()["resumed"] is True,
            "Full Access retry resumes the same valid unpaid Razorpay order",
        )
        check(
            not any(method == "POST" and path == "/orders" for method, path, _ in provider_calls),
            "resuming Full Access does not create a duplicate provider order",
        )

        # Retry a created monthly subscription: the same provider subscription is reused.
        pro_resume = client.post("/api/payments/create", json={"plan_id": "pro"})
        check(
            pro_resume.status_code == 200
            and pro_resume.json()["subscription_id"] == "sub-pending-pro"
            and pro_resume.json()["resumed"] is True,
            "Pro retry resumes the existing unpaid provider subscription",
        )
        check(
            not any(method == "POST" and path == "/subscriptions" for method, path, _ in provider_calls),
            "resuming a monthly checkout does not create a duplicate subscription",
        )

        # Unpaid subscription cancellation must be immediate, not end-of-cycle.
        pending_to_cancel = make_user("cancel_unpaid")
        with SessionLocal() as db:
            db.add(PaymentRecord(
                user_id=pending_to_cancel.id,
                plan_id="pro",
                amount_paise=29_900,
                currency="INR",
                kind="subscription",
                status="created",
                provider_subscription_id="sub-pending-pro-cancel",
                provider_payload={"provider_plan_id": "plan_pro_test"},
            ))
            db.commit()
        authenticate(client, pending_to_cancel.id)
        close_pending = client.post("/api/payments/sub-pending-pro-cancel/cancel")
        cancellation_call = next(
            call for call in provider_calls
            if call[0] == "POST" and call[1] == "/subscriptions/sub-pending-pro-cancel/cancel"
        )
        check(close_pending.status_code == 200 and close_pending.json()["cancelled_pending"] is True, "unpaid subscription checkout can be closed without removing a membership")
        check(cancellation_call[2] == {"cancel_at_cycle_end": False}, "unpaid subscription uses immediate cancellation instead of cycle-end cancellation")

        # Authenticated provider authorization is not the same as a fresh created checkout.
        # It must not reopen a duplicate checkout, but the learner can close it immediately.
        auth_user = make_user("authenticated")
        with SessionLocal() as db:
            db.add(PaymentRecord(
                user_id=auth_user.id,
                plan_id="pro",
                amount_paise=29_900,
                currency="INR",
                kind="subscription",
                status="authenticated",
                provider_subscription_id="sub-authenticated-pro",
                provider_payload={"provider_plan_id": "plan_pro_test"},
            ))
            db.commit()
        authenticate(client, auth_user.id)
        auth_billing = client.get("/api/me/billing").json()
        auth_pending = auth_billing["pending_checkouts"][0]
        check(
            auth_pending["state"] == "awaiting_verification" and auth_pending["cancelable"] is True,
            "authenticated but unpaid subscription is shown as pending verification, not active membership",
        )
        duplicate_auth_checkout = client.post("/api/payments/create", json={"plan_id": "pro"})
        check(
            duplicate_auth_checkout.status_code == 409
            and duplicate_auth_checkout.json()["detail"]["code"] == "SUBSCRIPTION_CONFIRMATION_PENDING",
            "authenticated subscription does not open another checkout",
        )
        auth_cancel = client.post("/api/payments/sub-authenticated-pro/cancel")
        auth_cancel_call = next(
            call for call in provider_calls
            if call[0] == "POST" and call[1] == "/subscriptions/sub-authenticated-pro/cancel"
        )
        check(
            auth_cancel.status_code == 200 and auth_cancel.json()["cancelled_pending"] is True,
            "authenticated unpaid authorization can be cancelled without changing plan access",
        )
        check(
            auth_cancel_call[2] == {"cancel_at_cycle_end": False},
            "authenticated unpaid authorization is cancelled immediately",
        )

        # A verified paid subscription must remain a membership and use cycle-end cancellation.
        paid_user = make_user("paid")
        with SessionLocal() as db:
            record = PaymentRecord(
                user_id=paid_user.id,
                plan_id="pro",
                amount_paise=29_900,
                currency="INR",
                kind="subscription",
                status="active",
                provider_subscription_id="sub-active-pro",
                provider_payload={"provider_plan_id": "plan_pro_test"},
            )
            db.add(record)
            db.flush()
            db.add(Entitlement(
                user_id=paid_user.id,
                plan_id="pro",
                status="active",
                provider_subscription_id="sub-active-pro",
                starts_at=datetime.now(timezone.utc) - timedelta(days=10),
                ends_at=future,
            ))
            db.commit()
        authenticate(client, paid_user.id)
        paid_billing = client.get("/api/me/billing").json()
        check(
            len(paid_billing["subscriptions"]) == 1
            and paid_billing["subscriptions"][0]["cancelable"] is True
            and paid_billing["pending_checkouts"] == [],
            "only a verified paid subscription appears in the membership section",
        )
        scheduled = client.post("/api/payments/sub-active-pro/cancel")
        active_cancel_call = next(
            call for call in provider_calls
            if call[0] == "POST" and call[1] == "/subscriptions/sub-active-pro/cancel"
        )
        check(scheduled.status_code == 200 and scheduled.json()["cancellation_scheduled"] is True, "paid subscription cancellation is scheduled for its current billing period end")
        check(active_cancel_call[2] == {"cancel_at_cycle_end": True}, "verified paid subscription uses cycle-end cancellation")

        print("Billing recovery tests passed; isolated SQLite database and mocked Razorpay only.")
    finally:
        client.close()
        main_module.razorpay_request = old_provider
        engine.dispose()
        _TEMP.cleanup()


if __name__ == "__main__":
    main()
