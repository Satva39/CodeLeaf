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

def apply_review_rating(row: ReviewSchedule, preferences: LearningPreference, rating: str, *, now: datetime | None = None) -> ReviewSchedule:
    """Apply a learner self-rating to a review interval without granting XP/mastery.

    The rating is a scheduling preference, not a server-verified correctness result.
    This intentionally stays separate from ``record_review_result`` used by graded work.
    """
    if rating not in {"again", "hard", "good", "easy"}:
        raise ValueError("rating must be again, hard, good, or easy")
    moment = now or utc_now()
    interval = max(1, int(row.interval_days or 1))
    ease = min(3.0, max(1.3, float(row.ease_factor or 2.3)))

    if rating == "again":
        row.repetitions = 0
        interval = 1
        ease = max(1.3, ease - 0.2)
    elif rating == "hard":
        row.repetitions = min(int(row.repetitions or 0) + 1, 30)
        interval = min(180, max(1, round(interval * 1.2)))
        ease = max(1.3, ease - 0.15)
    elif rating == "good":
        row.repetitions = min(int(row.repetitions or 0) + 1, 30)
        if row.repetitions == 1:
            interval = max(1, int(preferences.review_frequency_days or 1))
        elif row.repetitions == 2:
            interval = max(2, int(preferences.review_frequency_days or 1) * 2)
        else:
            interval = min(180, max(1, round(interval * ease)))
        ease = min(3.0, max(1.3, ease + 0.05))
    else:  # easy
        row.repetitions = min(int(row.repetitions or 0) + 1, 30)
        interval = min(180, max(3, round(interval * ease * 1.3)))
        ease = min(3.0, max(1.3, ease + 0.15))

    row.interval_days = interval
    row.ease_factor = ease
    row.last_result = rating
    row.last_reviewed_at = moment
    row.due_at = moment + timedelta(days=interval)
    row.dismissed_until = None
    return row
