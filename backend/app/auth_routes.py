"""Authentication and account lifecycle API routes."""
from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .auth_security import (
    clear_session_cookies, create_session, email_action_link, get_action_token,
    hash_password, issue_action_token, record_auth_attempt, require_user,
    revoke_user_sessions, send_action_email, require_email_delivery_configured, user_payload, verify_password,
    utc_now, token_digest, SESSION_COOKIE,
)
from .config import settings
from .db import get_db
from .models import (
    AccountActionToken, AuthSession, Bookmark, Certificate, Entitlement,
    ExamAttempt, ExerciseProgress, LessonProgress, PaymentRecord, ProjectSubmission,
    User, UserActivityDay, XPTransaction,
)
from .schemas import (
    AccountDeleteInput, ChangeEmailInput, ChangePasswordInput, EmailInput,
    LoginInput, RegisterInput, ResetPasswordInput, VerifyEmailInput,
)

router = APIRouter(tags=["authentication"])


@router.post("/api/auth/register", status_code=status.HTTP_202_ACCEPTED)
def register(body: RegisterInput, request: Request, db: Session = Depends(get_db)) -> dict:
    email = str(body.email).strip().lower()
    username = body.username.strip().lower()
    record_auth_attempt(db, request, "register", email)
    require_email_delivery_configured()
    exists = db.scalar(select(User.id).where((User.email == email) | (User.username == username)))
    # Match the success response to avoid disclosing whether an email/username is registered.
    if exists:
        return {"message": "If registration can be completed, verification instructions will be sent.", "verification_required": True}
    user = User(
        email=email, username=username, display_name=body.display_name,
        password_hash=hash_password(body.password), avatar={"variant": "spark"},
        theme="dark", is_email_verified=False,
    )
    db.add(user)
    try:
        db.flush()
        raw = issue_action_token(db, user, "verify_email", timedelta(hours=24))
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"message": "If registration can be completed, verification instructions will be sent.", "verification_required": True}
    link = email_action_link("/verify-email", raw)
    delivery = send_action_email(email, "Verify your CodeLeaf email", "Verify your CodeLeaf account", link, "Verify email", "in 24 hours")
    result = {"message": "If registration can be completed, verification instructions will be sent.", "verification_required": True}
    if delivery.get("test_url"):
        result.update({"delivery_mode": "test_mode", "test_url": delivery["test_url"]})
    return result


@router.post("/api/auth/login")
def login(body: LoginInput, request: Request, response: Response, db: Session = Depends(get_db)) -> dict:
    email = str(body.email).strip().lower()
    record_auth_attempt(db, request, "login", email)
    user = db.scalar(select(User).where(User.email == email))
    if not user or not user.is_active or not verify_password(body.password, user.password_hash) or not user.is_email_verified:
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    create_session(user, response, db)
    return {"user": user_payload(user)}


@router.post("/api/auth/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)) -> dict[str, bool]:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        row = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_digest(token)))
        if row and row.revoked_at is None:
            row.revoked_at = utc_now()
            db.commit()
    clear_session_cookies(response)
    return {"ok": True}


@router.post("/api/auth/verify-email")
def verify_email(body: VerifyEmailInput, request: Request, db: Session = Depends(get_db)) -> dict[str, bool]:
    record_auth_attempt(db, request, "verify_email", body.token[:20])
    action = get_action_token(db, body.token, "verify_email")
    user = db.get(User, action.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="This link is invalid or expired. Request a new one.")
    user.is_email_verified = True
    action.consumed_at = utc_now()
    db.commit()
    return {"ok": True}


@router.post("/api/auth/verification/resend")
def resend_verification(body: EmailInput, request: Request, db: Session = Depends(get_db)) -> dict:
    email = str(body.email).strip().lower()
    record_auth_attempt(db, request, "verification_resend", email)
    require_email_delivery_configured()
    response = {"message": "If the account needs verification, an email will be sent."}
    user = db.scalar(select(User).where(User.email == email, User.is_active.is_(True), User.is_email_verified.is_(False)))
    if not user:
        return response
    raw = issue_action_token(db, user, "verify_email", timedelta(hours=24))
    link = email_action_link("/verify-email", raw)
    delivery = send_action_email(email, "Verify your CodeLeaf email", "Verify your CodeLeaf account", link, "Verify email", "in 24 hours")
    if delivery.get("test_url"):
        response.update({"delivery_mode": "test_mode", "test_url": delivery["test_url"]})
    return response


@router.post("/api/auth/forgot-password")
def forgot_password(body: EmailInput, request: Request, db: Session = Depends(get_db)) -> dict:
    email = str(body.email).strip().lower()
    record_auth_attempt(db, request, "forgot_password", email)
    require_email_delivery_configured()
    response = {"message": "If an eligible account exists, password reset instructions will be sent."}
    user = db.scalar(select(User).where(User.email == email, User.is_active.is_(True), User.is_email_verified.is_(True)))
    if not user:
        return response
    raw = issue_action_token(db, user, "reset_password", timedelta(minutes=30))
    link = email_action_link("/reset-password", raw)
    delivery = send_action_email(email, "Reset your CodeLeaf password", "Reset your CodeLeaf password", link, "Reset password", "in 30 minutes")
    if delivery.get("test_url"):
        response.update({"delivery_mode": "test_mode", "test_url": delivery["test_url"]})
    return response


@router.post("/api/auth/reset-password")
def reset_password(body: ResetPasswordInput, request: Request, response: Response, db: Session = Depends(get_db)) -> dict[str, bool]:
    record_auth_attempt(db, request, "reset_password", body.token[:20])
    action = get_action_token(db, body.token, "reset_password")
    user = db.get(User, action.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="This link is invalid or expired. Request a new one.")
    user.password_hash = hash_password(body.password)
    action.consumed_at = utc_now()
    revoke_user_sessions(db, user.id)
    db.commit()
    clear_session_cookies(response)
    return {"ok": True}


@router.post("/api/auth/change-password")
def change_password(body: ChangePasswordInput, request: Request, response: Response,
                    user: User = Depends(require_user), db: Session = Depends(get_db)) -> dict[str, bool]:
    record_auth_attempt(db, request, "change_password", str(user.id))
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    user.password_hash = hash_password(body.new_password)
    revoke_user_sessions(db, user.id)
    db.commit()
    clear_session_cookies(response)
    return {"ok": True}


@router.post("/api/auth/change-email")
def change_email(body: ChangeEmailInput, request: Request,
                 user: User = Depends(require_user), db: Session = Depends(get_db)) -> dict:
    record_auth_attempt(db, request, "change_email", str(user.id))
    require_email_delivery_configured()
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    target = str(body.new_email).strip().lower()
    exists = db.scalar(select(User.id).where(User.email == target, User.id != user.id))
    response = {"message": "If this address can be used, a verification link will be sent."}
    if exists:
        return response
    raw = issue_action_token(db, user, "change_email", timedelta(hours=1), target_email=target)
    link = email_action_link("/verify-email-change", raw)
    delivery = send_action_email(target, "Confirm your CodeLeaf email change", "Confirm your new CodeLeaf email address", link, "Confirm email", "in 1 hour")
    if delivery.get("test_url"):
        response.update({"delivery_mode": "test_mode", "test_url": delivery["test_url"]})
    return response


@router.post("/api/auth/verify-email-change")
def verify_email_change(body: VerifyEmailInput, request: Request, response: Response, db: Session = Depends(get_db)) -> dict[str, bool]:
    record_auth_attempt(db, request, "verify_email_change", body.token[:20])
    action = get_action_token(db, body.token, "change_email")
    user = db.get(User, action.user_id)
    if not user or not user.is_active or not action.target_email:
        raise HTTPException(status_code=400, detail="This link is invalid or expired. Request a new one.")
    conflict = db.scalar(select(User.id).where(User.email == action.target_email, User.id != user.id))
    if conflict:
        raise HTTPException(status_code=400, detail="This link is invalid or expired. Request a new one.")
    user.email = action.target_email
    user.is_email_verified = True
    action.consumed_at = utc_now()
    revoke_user_sessions(db, user.id)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="This link is invalid or expired. Request a new one.")
    clear_session_cookies(response)
    return {"ok": True}


@router.get("/api/me/export")
def export_account(user: User = Depends(require_user), db: Session = Depends(get_db)) -> dict:
    lesson_rows = db.execute(select(LessonProgress,).where(LessonProgress.user_id == user.id)).scalars().all()
    exercise_rows = db.execute(select(ExerciseProgress).where(ExerciseProgress.user_id == user.id)).scalars().all()
    bookmarks = db.scalars(select(Bookmark).where(Bookmark.user_id == user.id)).all()
    activity = db.scalars(select(UserActivityDay).where(UserActivityDay.user_id == user.id)).all()
    projects = db.scalars(select(ProjectSubmission).where(ProjectSubmission.user_id == user.id)).all()
    return {
        "exported_at": utc_now().isoformat(), "user": user_payload(user),
        "lesson_progress": [{"lesson_id": str(x.lesson_id), "completed": x.completed, "time_spent_seconds": x.time_spent_seconds, "last_opened_at": x.last_opened_at.isoformat() if x.last_opened_at else None, "completed_at": x.completed_at.isoformat() if x.completed_at else None} for x in lesson_rows],
        "exercise_progress": [{"exercise_id": str(x.exercise_id), "completed": x.completed, "attempts": x.attempts, "last_attempt_at": x.last_attempt_at.isoformat() if x.last_attempt_at else None, "completed_at": x.completed_at.isoformat() if x.completed_at else None} for x in exercise_rows],
        "bookmarks": [{"lesson_id": str(x.lesson_id), "created_at": x.created_at.isoformat() if x.created_at else None} for x in bookmarks],
        "activity_days": [{"activity_date": x.activity_date.isoformat(), "timezone": x.timezone_name} for x in activity],
        "project_submissions": [{"project_slug": x.project_slug, "title": x.title, "visibility": x.visibility, "submitted_at": x.submitted_at.isoformat(), "code_bundle": x.code_bundle} for x in projects],
    }


@router.post("/api/me/delete")
def delete_account(body: AccountDeleteInput, request: Request, response: Response,
                   user: User = Depends(require_user), db: Session = Depends(get_db)) -> dict[str, bool]:
    record_auth_attempt(db, request, "delete_account", str(user.id))
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Password is incorrect.")
    # Preserve payment/audit rows for accounting, but remove learning and public-identity data.
    for model in (LessonProgress, ExerciseProgress, Bookmark, UserActivityDay, XPTransaction, Certificate, ExamAttempt, ProjectSubmission):
        db.execute(delete(model).where(model.user_id == user.id))
    db.execute(delete(AccountActionToken).where(AccountActionToken.user_id == user.id))
    revoke_user_sessions(db, user.id)
    for entitlement in db.scalars(select(Entitlement).where(Entitlement.user_id == user.id)).all():
        entitlement.status = "cancelled"
        entitlement.cancelled_at = utc_now()
    deleted_key = user.id.hex[:24]
    user.email = f"deleted+{deleted_key}@deleted.invalid"
    user.username = f"deleted_{deleted_key}"
    user.display_name = "Deleted learner"
    user.password_hash = hash_password(uuid4().hex + uuid4().hex)
    user.avatar = {}
    user.theme = "dark"
    user.is_active = False
    user.is_email_verified = False
    db.commit()
    clear_session_cookies(response)
    return {"ok": True}
