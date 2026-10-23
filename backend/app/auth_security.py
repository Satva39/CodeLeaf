"""Shared authentication, token, mail, and rate-limit primitives for CodeLeaf."""
from __future__ import annotations

import base64
import hashlib
import hmac
import html
import logging
import smtplib
import secrets
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formatdate, make_msgid, parseaddr
from typing import Any
from uuid import UUID
from urllib.parse import urlencode

import jwt
from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy import delete, select, func
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import AccountActionToken, AuthRateLimitEvent, AuthSession, User

SESSION_COOKIE = "codeleaf_session"
CSRF_COOKIE = "codeleaf_csrf"
TOKEN_ALGORITHM = "HS256"
_logger = logging.getLogger("codeleaf.auth")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return "scrypt$16384$8$1$" + base64.urlsafe_b64encode(salt).decode().rstrip("=") + "$" + base64.urlsafe_b64encode(digest).decode().rstrip("=")


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, n, r, p, salt_text, digest_text = stored.split("$")
        if algorithm != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(salt_text + "=" * (-len(salt_text) % 4))
        expected = base64.urlsafe_b64decode(digest_text + "=" * (-len(digest_text) % 4))
        actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def user_payload(user: User) -> dict[str, Any]:
    return {
        "id": str(user.id), "email": user.email, "display_name": user.display_name,
        "username": user.username, "avatar": user.avatar or {}, "theme": user.theme,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "email_verified": bool(user.is_email_verified),
    }


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(user: User, response: Response, db: Session) -> str:
    if len(settings.jwt_secret.strip()) < 32 or settings.jwt_secret.startswith("replace-with-"):
        raise HTTPException(status_code=503, detail="Authentication is not configured safely. Contact the site administrator.")
    now = utc_now()
    csrf_value = secrets.token_urlsafe(32)
    claims = {
        "sub": str(user.id), "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.jwt_ttl_seconds)).timestamp()),
        "jti": secrets.token_urlsafe(24), "csrf": csrf_value,
    }
    token = jwt.encode(claims, settings.jwt_secret, algorithm=TOKEN_ALGORITHM)
    db.add(AuthSession(
        token_hash=token_digest(token), user_id=user.id,
        expires_at=now + timedelta(seconds=settings.jwt_ttl_seconds),
    ))
    db.commit()
    same_site = "none" if settings.cookie_secure else "lax"
    response.set_cookie(SESSION_COOKIE, token, httponly=True, secure=settings.cookie_secure,
                        samesite=same_site, max_age=settings.jwt_ttl_seconds, path="/")
    response.set_cookie(CSRF_COOKIE, csrf_value, httponly=False, secure=settings.cookie_secure,
                        samesite=same_site, max_age=settings.jwt_ttl_seconds, path="/")
    return token


def clear_session_cookies(response: Response) -> None:
    same_site = "none" if settings.cookie_secure else "lax"
    for name, http_only in ((SESSION_COOKIE, True), (CSRF_COOKIE, False)):
        response.delete_cookie(name, path="/", secure=settings.cookie_secure,
                               httponly=http_only, samesite=same_site)


def require_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            token = auth[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Sign in to continue.")
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[TOKEN_ALGORITHM])
        user_id = UUID(claims["sub"])
        csrf_claim = claims.get("csrf")
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Your session is invalid or expired. Please sign in again.")
    session = db.scalar(select(AuthSession).where(
        AuthSession.token_hash == token_digest(token),
        AuthSession.revoked_at.is_(None),
        AuthSession.expires_at > utc_now(),
    ))
    user = db.get(User, user_id)
    if not session or not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Your session is invalid or expired. Please sign in again.")
    if not user.is_email_verified:
        raise HTTPException(status_code=403, detail="Verify your email address before signing in.")
    # Keep the signed CSRF value available to the origin/CSRF middleware without storing it in the DB.
    request.state.csrf_claim = csrf_claim
    return user


def record_auth_attempt(db: Session, request: Request, action: str, subject: str = "") -> None:
    """Persist per-IP and per-subject attempts so limits survive process restarts."""
    now = utc_now()
    window = max(60, int(settings.auth_rate_limit_window_seconds))
    limit = max(1, int(settings.auth_rate_limit_max_attempts))
    client_ip = request.client.host if request.client else "unknown"
    dimensions = [("ip", client_ip), ("subject", (subject or "anonymous").strip().lower())]
    keys = [hmac.new(settings.jwt_secret.encode(), f"{action}\0{kind}\0{value}".encode(), hashlib.sha256).hexdigest() for kind, value in dimensions]
    db.execute(delete(AuthRateLimitEvent).where(AuthRateLimitEvent.occurred_at < now - timedelta(seconds=window * 3)))
    counts = db.execute(select(AuthRateLimitEvent.key_hash, func.count(AuthRateLimitEvent.id))
                        .where(AuthRateLimitEvent.action == action,
                               AuthRateLimitEvent.key_hash.in_(keys),
                               AuthRateLimitEvent.occurred_at >= now - timedelta(seconds=window))
                        .group_by(AuthRateLimitEvent.key_hash)).all()
    by_key = {key: count for key, count in counts}
    if any(by_key.get(key, 0) >= limit for key in keys):
        db.rollback()
        raise HTTPException(status_code=429, detail="Too many attempts. Please wait before trying again.", headers={"Retry-After": str(window)})
    for key in keys:
        db.add(AuthRateLimitEvent(action=action, key_hash=key, occurred_at=now))
    db.commit()


def issue_action_token(db: Session, user: User, purpose: str, ttl: timedelta,
                       target_email: str | None = None) -> str:
    now = utc_now()
    old_tokens = db.scalars(select(AccountActionToken).where(
        AccountActionToken.user_id == user.id, AccountActionToken.purpose == purpose,
        AccountActionToken.consumed_at.is_(None),
    )).all()
    for old in old_tokens:
        old.consumed_at = now
    raw = secrets.token_urlsafe(32)
    db.add(AccountActionToken(
        user_id=user.id, token_hash=token_digest(raw), purpose=purpose,
        target_email=target_email, created_at=now, expires_at=now + ttl,
    ))
    db.commit()
    return raw


def get_action_token(db: Session, raw: str, purpose: str) -> AccountActionToken:
    if not raw or len(raw) > 200:
        raise HTTPException(status_code=400, detail="This link is invalid or expired. Request a new one.")
    token = db.scalar(select(AccountActionToken).where(
        AccountActionToken.token_hash == token_digest(raw),
        AccountActionToken.purpose == purpose,
        AccountActionToken.consumed_at.is_(None),
        AccountActionToken.expires_at > utc_now(),
    ))
    if not token:
        raise HTTPException(status_code=400, detail="This link is invalid or expired. Request a new one.")
    return token


def email_action_link(path: str, raw_token: str) -> str:
    base = settings.frontend_base_url.rstrip("/")
    return f"{base}{path}?{urlencode({'token': raw_token})}"


def smtp_configuration_problems() -> list[str]:
    """Return missing/unsafe SMTP setting names without exposing their values."""
    problems: list[str] = []
    required = {
        "EMAIL_FROM": settings.email_from,
        "SMTP_HOST": settings.smtp_host,
        "SMTP_USERNAME": settings.smtp_username,
        "SMTP_PASSWORD": settings.smtp_password,
    }
    problems.extend(name for name, value in required.items() if not value or not str(value).strip())
    sender = parseaddr(settings.email_from or "")[1]
    if settings.email_from and (not sender or "@" not in sender):
        problems.append("EMAIL_FROM")
    if settings.smtp_port != 465 and not settings.smtp_use_tls:
        problems.append("SMTP_USE_TLS")
    return sorted(set(problems))


def require_email_delivery_configured() -> None:
    # Explicit local test mode may return a manual link, but production email flows
    # always require a fully configured, authenticated SMTP transport.
    if settings.email_test_mode and settings.app_env.strip().lower() not in {"production", "prod"}:
        return
    problems = smtp_configuration_problems()
    if problems:
        _logger.error("account_email_configuration_invalid missing_settings=%s", ",".join(problems))
        raise HTTPException(status_code=503, detail="Email delivery is not configured. Please check the backend SMTP settings.")


def send_smtp_message(message: EmailMessage) -> None:
    """Send one email using STARTTLS on normal SMTP ports or implicit TLS on 465."""
    problems = smtp_configuration_problems()
    if problems:
        raise ValueError("SMTP configuration is incomplete: " + ", ".join(problems))

    timeout = max(3, int(settings.smtp_timeout_seconds))
    username = settings.smtp_username.strip()
    password = settings.smtp_password
    # Google displays app passwords in groups for readability. Remove only that
    # formatting for Gmail; preserve credentials exactly for other SMTP providers.
    if settings.smtp_host.strip().lower() == "smtp.gmail.com":
        password = "".join(password.split())
    if settings.smtp_port == 465:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=timeout) as smtp:
            smtp.ehlo()
            smtp.login(username, password)
            refused = smtp.send_message(message)
    else:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=timeout) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(username, password)
            refused = smtp.send_message(message)
    # SMTP's send_message can return a refusal map rather than raising if a
    # server accepts some recipients but refuses others. CodeLeaf sends to one.
    if refused:
        raise smtplib.SMTPRecipientsRefused(refused)


def send_action_email(to_email: str, subject: str, heading: str, action_url: str,
                      action_label: str, expires_text: str) -> dict[str, Any]:
    """Send an action email, or return an explicit local-only test link."""
    if settings.email_test_mode and settings.app_env.strip().lower() not in {"production", "prod"}:
        return {"delivery_mode": "test_mode", "test_url": action_url}
    require_email_delivery_configured()

    body = (f"{heading}\n\nUse this link to continue: {action_url}\n\n"
            f"This link expires {expires_text}. If you did not request this, you can ignore this email.\n")
    safe_heading = html.escape(heading)
    safe_action_label = html.escape(action_label)
    safe_url = html.escape(action_url, quote=True)
    safe_expiry = html.escape(f"This link expires {expires_text}. If you did not request this, you can ignore this email.")
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.email_from.strip()
    message["To"] = to_email
    message["Date"] = formatdate(localtime=True)
    message["Message-ID"] = make_msgid(domain=(parseaddr(settings.email_from)[1].split("@")[-1] if "@" in parseaddr(settings.email_from)[1] else None))
    message.set_content(body)
    message.add_alternative(
        "<!doctype html><html><body style=\"font-family:Arial,sans-serif;line-height:1.6;color:#172033\">"
        f"<h2>{safe_heading}</h2><p>Use the button below to continue with CodeLeaf.</p>"
        f"<p><a href=\"{safe_url}\" style=\"display:inline-block;padding:12px 18px;background:#16c79a;color:#09231d;"
        f"text-decoration:none;border-radius:8px;font-weight:700\">{safe_action_label}</a></p>"
        f"<p>If the button does not work, copy this link into your browser:<br><a href=\"{safe_url}\">{safe_url}</a></p>"
        f"<p style=\"color:#667085;font-size:13px\">{safe_expiry}</p></body></html>",
        subtype="html",
    )
    try:
        send_smtp_message(message)
    except (OSError, smtplib.SMTPException, ValueError) as exc:
        # Never log recipients, action URLs, message bodies, SMTP response text, or credentials.
        smtp_code = getattr(exc, "smtp_code", None)
        if smtp_code is not None:
            _logger.warning("account_email_delivery_failed error_type=%s smtp_code=%s", type(exc).__name__, smtp_code)
        else:
            _logger.warning("account_email_delivery_failed error_type=%s", type(exc).__name__)
        return {"delivery_mode": "not_confirmed"}
    return {"delivery_mode": "email"}


def revoke_user_sessions(db: Session, user_id: UUID, except_hash: str | None = None) -> None:
    rows = db.scalars(select(AuthSession).where(
        AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None)
    )).all()
    now = utc_now()
    for row in rows:
        if except_hash is None or row.token_hash != except_hash:
            row.revoked_at = now
