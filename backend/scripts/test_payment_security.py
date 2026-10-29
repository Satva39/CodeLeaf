"""Payment security contract tests against an isolated temporary SQLite database.

Run from backend/: python scripts/test_payment_security.py
No live Razorpay requests are made; provider requests are mocked.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

_TEMP = tempfile.TemporaryDirectory(prefix="codeleaf-payment-security-")
os.environ["DATABASE_URL"] = f"sqlite:///{(Path(_TEMP.name) / 'payments.db').as_posix()}"
os.environ["APP_ENV"] = "development"
os.environ["JWT_SECRET"] = "payment-test-only-secret-never-use-in-production-2026"
os.environ["FRONTEND_ORIGINS"] = "http://localhost:5173"
os.environ["FRONTEND_BASE_URL"] = "http://localhost:5173"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import Response  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select, func  # noqa: E402

from app.config import settings  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.auth_security import create_session  # noqa: E402
from app.models import Entitlement, PaymentRecord, User, WebhookEvent  # noqa: E402
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


def main() -> None:
    Base.metadata.create_all(bind=engine)
    old_request = main_module.razorpay_request
    settings.razorpay_key_id = "rzp_test_codeleaf"
    settings.razorpay_key_secret = "unit-test-provider-key-secret"
    settings.razorpay_webhook_secret = "unit-test-webhook-secret"

    provider_calls: list[tuple[str, str]] = []

    async def fake_provider(method: str, path: str, payload=None):
        provider_calls.append((method, path))
        if method == "POST" and path == "/orders":
            return {"id": "order_full_access_test"}
        if method == "GET" and path == "/payments/pay_full_access_test":
            return {
                "id": "pay_full_access_test",
                "order_id": "order_full_access_test",
                "amount": 4_999_900,
                "currency": "INR",
                "status": "captured",
            }
        raise AssertionError(f"Unexpected mocked provider request: {method} {path}")

    main_module.razorpay_request = fake_provider
    client = TestClient(main_module.app)
    try:
        buyer = make_user("payment_buyer")
        authenticate(client, buyer.id)

        created = client.post("/api/payments/create", json={"plan_id": "full_access", "amount": 1})
        check(created.status_code == 200, "Full Access order is created through the mocked provider")
        payload = created.json()
        check(payload["amount"] == 4_999_900 and payload["currency"] == "INR", "server-controlled lifetime price is returned in integer paise")
        check(payload["order_id"] == "order_full_access_test", "provider order ID is returned")

        signature = hmac.new(
            settings.razorpay_key_secret.encode(),
            b"order_full_access_test|pay_full_access_test",
            hashlib.sha256,
        ).hexdigest()
        invalid = client.post("/api/payments/verify", json={
            "plan_id": "full_access",
            "razorpay_order_id": "order_full_access_test",
            "razorpay_payment_id": "pay_full_access_test",
            "razorpay_signature": "0" * 64,
        })
        check(invalid.status_code == 400, "invalid payment signature cannot grant access")

        verified = client.post("/api/payments/verify", json={
            "plan_id": "full_access",
            "razorpay_order_id": "order_full_access_test",
            "razorpay_payment_id": "pay_full_access_test",
            "razorpay_signature": signature,
        })
        check(verified.status_code == 200 and verified.json().get("ok") is True, "captured payment with a valid signature is accepted")
        with SessionLocal() as db:
            entitlement = db.scalar(select(Entitlement).where(Entitlement.user_id == buyer.id, Entitlement.plan_id == "full_access"))
            check(entitlement is not None and entitlement.status == "active" and entitlement.ends_at is None, "lifetime entitlement has no expiry and is persisted")

        refunded_buyer = make_user("payment_refunded_buyer")
        with SessionLocal() as db:
            refunded_record = PaymentRecord(
                user_id=refunded_buyer.id, plan_id="full_access", amount_paise=4_999_900,
                currency="INR", kind="order", status="refunded",
                provider_order_id="order_full_access_refunded", provider_payment_id="pay_full_access_refunded",
            )
            db.add(refunded_record)
            db.commit()
        authenticate(client, refunded_buyer.id)
        refunded_signature = hmac.new(
            settings.razorpay_key_secret.encode(),
            b"order_full_access_refunded|pay_full_access_refunded", hashlib.sha256,
        ).hexdigest()
        refunded_retry = client.post("/api/payments/verify", json={
            "plan_id": "full_access", "razorpay_order_id": "order_full_access_refunded",
            "razorpay_payment_id": "pay_full_access_refunded", "razorpay_signature": refunded_signature,
        })
        check(refunded_retry.status_code == 409, "a refunded Full Access order cannot be reactivated by retrying the checkout callback")

        # Verify webhook signature validation and event-id deduplication in isolation.
        webhook_buyer = make_user("webhook_buyer")
        with SessionLocal() as db:
            record = PaymentRecord(
                user_id=webhook_buyer.id,
                plan_id="full_access",
                amount_paise=4_999_900,
                currency="INR",
                kind="order",
                status="created",
                provider_order_id="order_webhook_test",
            )
            db.add(record)
            db.commit()

        raw = json.dumps({
            "event": "order.paid",
            "payload": {
                "order": {"entity": {"id": "order_webhook_test", "amount": 4_999_900, "currency": "INR"}},
                "payment": {"entity": {"id": "pay_webhook_test", "order_id": "order_webhook_test", "amount": 4_999_900, "currency": "INR"}},
            },
        }, separators=(",", ":")).encode()
        webhook_signature = hmac.new(settings.razorpay_webhook_secret.encode(), raw, hashlib.sha256).hexdigest()
        bad_webhook = client.post("/api/payments/webhook", content=raw, headers={"x-razorpay-signature": "bad", "x-razorpay-event-id": "evt-codeleaf-1", "content-type": "application/json"})
        check(bad_webhook.status_code == 400, "invalid webhook signature is rejected")
        first = client.post("/api/payments/webhook", content=raw, headers={"x-razorpay-signature": webhook_signature, "x-razorpay-event-id": "evt-codeleaf-1", "content-type": "application/json"})
        second = client.post("/api/payments/webhook", content=raw, headers={"x-razorpay-signature": webhook_signature, "x-razorpay-event-id": "evt-codeleaf-1", "content-type": "application/json"})
        check(first.status_code == 200 and second.status_code == 200, "signed webhook and provider retry both return success")
        with SessionLocal() as db:
            events = db.scalar(select(func.count(WebhookEvent.id)).where(WebhookEvent.provider_event_id == "evt-codeleaf-1")) or 0
            webhook_entitlement = db.scalar(select(Entitlement).where(Entitlement.user_id == webhook_buyer.id, Entitlement.plan_id == "full_access"))
            record = db.scalar(select(PaymentRecord).where(PaymentRecord.provider_order_id == "order_webhook_test"))
            check(events == 1, "duplicate webhook event is stored only once")
            check(record is not None and record.status == "paid", "valid order.paid webhook updates the matching payment record")
            check(webhook_entitlement is not None and webhook_entitlement.ends_at is None, "valid webhook grants idempotent lifetime entitlement")

        # A late order.paid event must not restore a refunded purchase.
        late_paid = json.dumps({
            "event": "order.paid",
            "payload": {
                "order": {"entity": {"id": "order_full_access_refunded", "amount": 4_999_900, "currency": "INR"}},
                "payment": {"entity": {"id": "pay_full_access_refunded", "order_id": "order_full_access_refunded", "amount": 4_999_900, "currency": "INR"}},
            },
        }, separators=(",", ":")).encode()
        late_signature = hmac.new(settings.razorpay_webhook_secret.encode(), late_paid, hashlib.sha256).hexdigest()
        late_response = client.post("/api/payments/webhook", content=late_paid, headers={
            "x-razorpay-signature": late_signature, "x-razorpay-event-id": "evt-late-refunded-paid", "content-type": "application/json",
        })
        with SessionLocal() as db:
            refunded_record = db.scalar(select(PaymentRecord).where(PaymentRecord.provider_order_id == "order_full_access_refunded"))
            refunded_entitlement = db.scalar(select(Entitlement).where(Entitlement.user_id == refunded_buyer.id, Entitlement.plan_id == "full_access", Entitlement.status == "active"))
            check(late_response.status_code == 200 and refunded_record.status == "refunded" and refunded_entitlement is None, "late paid webhook cannot revive a refunded lifetime purchase")
        check(provider_calls == [("POST", "/orders"), ("GET", "/payments/pay_full_access_test")], "no real provider network calls were made")
    finally:
        client.close()
        main_module.razorpay_request = old_request
        engine.dispose()
        _TEMP.cleanup()
    print("Payment security tests passed; only an isolated temporary SQLite database and mocked provider were used.")


if __name__ == "__main__":
    main()
