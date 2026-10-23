"""Small deterministic services used by Phase 5 learner recommendations and review."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import LearningPreference, ReviewSchedule


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_or_create_preferences(db: Session, user_id) -> LearningPreference:
    preferences = db.scalar(select(LearningPreference).where(LearningPreference.user_id == user_id))
    if preferences is None:
        preferences = LearningPreference(user_id=user_id)
        db.add(preferences)
        db.flush()
    return preferences


def record_review_result(db: Session, user_id, course_slug: str, item_type: str, item_slug: str, correct: bool) -> ReviewSchedule:
    """Update spaced retrieval only from a server-recorded lesson/exercise outcome."""
    now = utc_now()
    row = db.scalar(select(ReviewSchedule).where(
        ReviewSchedule.user_id == user_id,
        ReviewSchedule.course_slug == course_slug,
        ReviewSchedule.item_type == item_type,
        ReviewSchedule.item_slug == item_slug,
    ))
    if row is None:
        row = ReviewSchedule(user_id=user_id, course_slug=course_slug,
                             item_type=item_type, item_slug=item_slug,
                             due_at=now + timedelta(days=1))
        db.add(row)
        db.flush()
    preferences = get_or_create_preferences(db, user_id)
    row.last_reviewed_at = now
    row.last_result = "correct" if correct else "incorrect"
    row.dismissed_until = None
    if correct:
        row.repetitions = min(row.repetitions + 1, 30)
        if row.repetitions == 1:
            row.interval_days = max(1, preferences.review_frequency_days)
        elif row.repetitions == 2:
            row.interval_days = max(2, preferences.review_frequency_days * 2)
        else:
            row.interval_days = min(180, max(1, round(row.interval_days * row.ease_factor)))
            row.ease_factor = min(3.0, max(1.3, row.ease_factor + 0.05))
    else:
        row.repetitions = 0
        row.interval_days = 1
        row.ease_factor = max(1.3, row.ease_factor - 0.2)
    row.due_at = now + timedelta(days=row.interval_days)
    return row
