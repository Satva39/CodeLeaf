"""Integration regressions for auth lifecycle APIs using an isolated in-memory SQLite DB.

Run from backend/: python scripts/test_auth_lifecycle.py
This does not connect to or modify any configured production database.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from datetime import timedelta
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Force a deterministic local test configuration before importing the application.
os.environ.update({
    "APP_ENV": "development",
    "DATABASE_URL": "sqlite+pysqlite:///:memory:",
    "JWT_SECRET": "auth-lifecycle-test-secret-48-chars-4QxK7Pz9Vt2Lm6Aa",
    "COOKIE_SECURE": "false",
    "FRONTEND_ORIGINS": "http://localhost:5173",
    "FRONTEND_BASE_URL": "http://localhost:5173",
    "EMAIL_TEST_MODE": "true",
})

import httpx
from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.responses import Response as StarletteResponse

from app.config import settings
from app.db import Base, get_db
from app.models import AccountActionToken, AuthRateLimitEvent, AuthSession, User
from app.auth_security import create_session, token_digest, utc_now
from app.main import app

engine = create_engine(
    "sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
Base.metadata.create_all(engine)
TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def override_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_db
ORIGIN = "http://localhost:5173"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS {message}")


def reset_rate_events() -> None:
    with TestSession() as db:
        db.execute(delete(AuthRateLimitEvent))
        db.commit()


async def run_tests() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=ORIGIN) as client:
        blank_name = await client.post("/api/auth/register", headers={"Origin": ORIGIN}, json={
            "email": "blank-name@gmail.com", "username": "blank_name", "display_name": "   ", "password": "a-long-test-password-1"
        })
        require(blank_name.status_code == 422, "registration rejects whitespace-only display names")

        # Registration intentionally creates no authenticated session before email confirmation.
        response = await client.post("/api/auth/register", headers={"Origin": ORIGIN}, json={
            "email": "learner@gmail.com", "username": "test_learner", "display_name": "Test Learner", "password": "a-long-test-password-1"
        })
        require(response.status_code == 202, "registration returns an enumeration-safe accepted response")
        data = response.json()
        require(data.get("verification_required") is True and data.get("delivery_mode") == "test_mode" and bool(data.get("test_url")), "local email test mode is explicit and does not claim email delivery")
        require(client.cookies.get("codeleaf_session") is None, "unverified registration does not create a session")
        unverified_login = await client.post("/api/auth/login", headers={"Origin": ORIGIN}, json={"email": "learner@gmail.com", "password": "a-long-test-password-1"})
        require(unverified_login.status_code == 401, "unverified registrations cannot sign in")
        verify_token = parse_qs(urlparse(data["test_url"]).query)["token"][0]
        with TestSession() as db:
            stored = db.scalar(select(AccountActionToken).where(AccountActionToken.purpose == "verify_email"))
            require(stored is not None and stored.token_hash == token_digest(verify_token) and stored.token_hash != verify_token, "one-time action token is stored only as a digest")

        response = await client.get("/api/me")
        require(response.status_code == 401, "protected resources reject anonymous users")
        response = await client.post("/api/auth/verify-email", headers={"Origin": ORIGIN}, json={"token": verify_token})
        require(response.status_code == 200, "valid email verification token succeeds")
        replay = await client.post("/api/auth/verify-email", headers={"Origin": ORIGIN}, json={"token": verify_token})
        require(replay.status_code == 400, "verification tokens cannot be replayed")

        response = await client.post("/api/auth/login", headers={"Origin": ORIGIN}, json={"email": "learner@gmail.com", "password": "a-long-test-password-1"})
        require(response.status_code == 200, "verified account can log in")
        session_cookie = client.cookies.get("codeleaf_session")
        csrf_cookie = client.cookies.get("codeleaf_csrf")
        require(bool(session_cookie) and bool(csrf_cookie), "login issues session and CSRF cookies")
        cookies = response.headers.get_list("set-cookie")
        require(any("codeleaf_session=" in value and "httponly" in value.lower() for value in cookies), "session cookie is HttpOnly")
        require(any("codeleaf_session=" in value and "samesite=lax" in value.lower() and "secure" not in value.lower() for value in cookies), "local session cookie uses the local-development flags")
        require(any("codeleaf_csrf=" in value and "httponly" not in value.lower() for value in cookies), "CSRF cookie is readable by the frontend helper")
        previous_cookie_setting = settings.cookie_secure
        try:
            settings.cookie_secure = True
            with TestSession() as db:
                verified_user = db.scalar(select(User).where(User.email == "learner@gmail.com"))
                secure_response = StarletteResponse()
                secure_session_token = create_session(verified_user, secure_response, db)
                secure_cookie_headers = secure_response.headers.getlist("set-cookie")
                require(any("codeleaf_session=" in value and "httponly" in value.lower() and "secure" in value.lower() and "samesite=none" in value.lower() for value in secure_cookie_headers), "production session cookie uses Secure, HttpOnly and SameSite=None")
                require(any("codeleaf_csrf=" in value and "secure" in value.lower() and "samesite=none" in value.lower() and "httponly" not in value.lower() for value in secure_cookie_headers), "production CSRF cookie is Secure, SameSite=None and readable")
                saved_secure_session = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_digest(secure_session_token)))
                saved_secure_session.revoked_at = utc_now()
                db.commit()
        finally:
            settings.cookie_secure = previous_cookie_setting
        with TestSession() as db:
            saved_session = db.scalar(select(AuthSession).where(AuthSession.user_id == db.scalar(select(User.id).where(User.email == "learner@gmail.com"))))
            require(saved_session is not None and saved_session.token_hash == token_digest(session_cookie) and saved_session.token_hash != session_cookie, "session revocation stores only a digest of the signed cookie")

        require((await client.get("/api/me")).status_code == 200, "signed-in learner can access their account")
        foreign_origin = await client.post("/api/auth/logout", headers={"Origin": "https://attacker.example", "X-CSRF-Token": csrf_cookie})
        require(foreign_origin.status_code == 403, "foreign origins cannot perform cookie-authenticated state changes")
        rejected_csrf = await client.post("/api/auth/logout", headers={"Origin": ORIGIN})
        require(rejected_csrf.status_code == 403, "cookie-authenticated state changes require a CSRF token")
        response = await client.post("/api/auth/logout", headers={"Origin": ORIGIN, "X-CSRF-Token": csrf_cookie})
        require(response.status_code == 200, "logout succeeds with valid CSRF token")
        require((await client.get("/api/me")).status_code == 401, "logout revokes the server-side session")

        # Exercise the configured persistent rate limit without waiting for its window.
        reset_rate_events()
        settings.auth_rate_limit_max_attempts = 2
        for index in range(2):
            response = await client.post("/api/auth/login", headers={"Origin": ORIGIN}, json={"email": "learner@gmail.com", "password": f"wrong-{index}"})
            require(response.status_code == 401, f"wrong password attempt {index + 1} is rejected generically")
        response = await client.post("/api/auth/login", headers={"Origin": ORIGIN}, json={"email": "learner@gmail.com", "password": "wrong-again"})
        require(response.status_code == 429, "repeated auth attempts are rate-limited")
        settings.auth_rate_limit_max_attempts = 8
        reset_rate_events()

        # Password-reset token is single-use; reset also invalidates any prior session.
        response = await client.post("/api/auth/forgot-password", headers={"Origin": ORIGIN}, json={"email": "learner@gmail.com"})
        require(response.status_code == 200 and response.json().get("message"), "password recovery uses a generic response")
        reset_token = parse_qs(urlparse(response.json()["test_url"]).query)["token"][0]
        response = await client.post("/api/auth/reset-password", headers={"Origin": ORIGIN}, json={"token": reset_token, "password": "a-new-test-password-2"})
        require(response.status_code == 200, "valid password reset succeeds")
        replay = await client.post("/api/auth/reset-password", headers={"Origin": ORIGIN}, json={"token": reset_token, "password": "another-new-password-3"})
        require(replay.status_code == 400, "password-reset token cannot be replayed")
        response = await client.post("/api/auth/login", headers={"Origin": ORIGIN}, json={"email": "learner@gmail.com", "password": "a-new-test-password-2"})
        require(response.status_code == 200, "reset password can be used to sign in")

        # Expired token is rejected even if its digest exists in the table.
        with TestSession() as db:
            user = db.scalar(select(User).where(User.email == "learner@gmail.com"))
            from uuid import uuid4
            expired_raw = "expired-token-" + uuid4().hex
            db.add(AccountActionToken(user_id=user.id, token_hash=token_digest(expired_raw), purpose="reset_password", created_at=utc_now() - timedelta(hours=2), expires_at=utc_now() - timedelta(seconds=1)))
            db.commit()
        response = await client.post("/api/auth/reset-password", headers={"Origin": ORIGIN, "X-CSRF-Token": client.cookies.get("codeleaf_csrf")}, json={"token": expired_raw, "password": "another-new-password-3"})
        require(response.status_code == 400, "expired account-action token is rejected")

        # Current-password checks, email changes, exports and account deletion.
        csrf = client.cookies.get("codeleaf_csrf")
        response = await client.post("/api/auth/change-password", headers={"Origin": ORIGIN, "X-CSRF-Token": csrf}, json={"current_password": "wrong-current-password", "new_password": "a-third-test-password-3"})
        require(response.status_code == 400, "password change rejects an incorrect current password")
        response = await client.post("/api/auth/change-password", headers={"Origin": ORIGIN, "X-CSRF-Token": csrf}, json={"current_password": "a-new-test-password-2", "new_password": "a-third-test-password-3"})
        require(response.status_code == 200, "password change succeeds and clears session cookies")
        require((await client.get("/api/me")).status_code == 401, "password change revokes existing sessions")
        response = await client.post("/api/auth/login", headers={"Origin": ORIGIN}, json={"email": "learner@gmail.com", "password": "a-third-test-password-3"})
        require(response.status_code == 200, "new password works after changing it")
        csrf = client.cookies.get("codeleaf_csrf")
        response = await client.post("/api/auth/change-email", headers={"Origin": ORIGIN, "X-CSRF-Token": csrf}, json={"current_password": "a-third-test-password-3", "new_email": "updated@gmail.com"})
        require(response.status_code == 200 and response.json().get("test_url"), "email change sends/returns a one-time confirmation action")
        email_token = parse_qs(urlparse(response.json()["test_url"]).query)["token"][0]
        response = await client.post("/api/auth/verify-email-change", headers={"Origin": ORIGIN, "X-CSRF-Token": csrf}, json={"token": email_token})
        require(response.status_code == 200, "verified email change is applied")
        require((await client.get("/api/me")).status_code == 401, "email change revokes existing sessions")
        response = await client.post("/api/auth/login", headers={"Origin": ORIGIN}, json={"email": "updated@gmail.com", "password": "a-third-test-password-3"})
        require(response.status_code == 200, "new email is usable after confirmation")
        require((await client.get("/api/me/export")).status_code == 200, "authenticated account export is available")
        csrf = client.cookies.get("codeleaf_csrf")
        response = await client.post("/api/me/delete", headers={"Origin": ORIGIN, "X-CSRF-Token": csrf}, json={"password": "a-third-test-password-3"})
        require(response.status_code == 200, "account deletion requires and accepts the current password")
        require((await client.get("/api/me")).status_code == 401, "deleted account cannot keep an active session")
        response = await client.post("/api/auth/login", headers={"Origin": ORIGIN}, json={"email": "updated@gmail.com", "password": "a-third-test-password-3"})
        require(response.status_code == 401, "deleted account cannot sign in")

    app.dependency_overrides.clear()
    print("All auth lifecycle integration tests passed.")


if __name__ == "__main__":
    asyncio.run(run_tests())
