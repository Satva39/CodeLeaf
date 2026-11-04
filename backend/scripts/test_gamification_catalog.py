"""Isolated tests for the dog-avatar catalog and one-time achievement rewards.

Run from backend/: python scripts/test_gamification_catalog.py
Uses a temporary SQLite database and never connects to the configured production DB.
"""
from __future__ import annotations
import os
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

_TEMP = tempfile.TemporaryDirectory(prefix="codeleaf-gamification-")
os.environ["DATABASE_URL"] = f"sqlite:///{(Path(_TEMP.name) / 'gamification.db').as_posix()}"
os.environ["JWT_SECRET"] = "gamification-test-secret-not-for-deployment"
os.environ["APP_ENV"] = "test"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select, func  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.models import Course, Module, Lesson, LessonProgress, User, UserAchievement, UserAvatarInventory, XPTransaction  # noqa: E402
from app.gamification import ACHIEVEMENTS, AVATAR_ITEMS, ITEM_BY_ID, XP_REWARDS, evaluate_achievements, ensure_avatar_records  # noqa: E402


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS {message}")


def main() -> None:
    Base.metadata.create_all(bind=engine)
    check(len(AVATAR_ITEMS) >= 30, "avatar catalog includes at least 30 cosmetics")
    check(len({item["id"] for item in AVATAR_ITEMS}) == len(AVATAR_ITEMS), "cosmetic item IDs are unique")
    check(len({item["id"] for item in ACHIEVEMENTS}) == len(ACHIEVEMENTS), "achievement IDs are unique")
    reward_ids = [item["reward_item_id"] for item in ACHIEVEMENTS]
    check(len(set(reward_ids)) == len(reward_ids), "each achievement maps to exactly one distinct reward item")
    check(all(item_id in ITEM_BY_ID for item_id in reward_ids), "every achievement points to a defined cosmetic")
    check(set(XP_REWARDS.values()) == {10, 100}, "normal XP is 10 and project XP is the only 100 XP exception")

    with SessionLocal() as db:
        user = User(email="dog-test@example.invalid", display_name="Dog Test", username=f"dog_{uuid4().hex[:12]}", password_hash="test-only-hash")
        course = Course(slug="dog-test", title="Dog Test Course", published=False)
        db.add_all([user, course]); db.flush()
        module = Module(course_id=course.id, slug="intro", title="Intro", sort_order=1)
        db.add(module); db.flush()
        lesson = Lesson(module_id=module.id, slug="first", title="First", is_published=True)
        db.add(lesson); db.flush()
        db.add(LessonProgress(user_id=user.id, lesson_id=lesson.id, completed=True))
        db.flush()
        first = evaluate_achievements(db, user.id)
        db.commit()
        check(len(first) == 1 and first[0]["achievement_id"] == "first-task", "first completed learning task unlocks its matching achievement")
        check(first[0]["item_id"] == "starter-cap" and first[0]["xp_awarded"] == 10, "achievement grants its designated item and exactly 10 XP")
        second = evaluate_achievements(db, user.id)
        db.commit()
        achievement_count = db.scalar(select(func.count(UserAchievement.id)).where(UserAchievement.user_id == user.id))
        item_count = db.scalar(select(func.count(UserAvatarInventory.id)).where(UserAvatarInventory.user_id == user.id, UserAvatarInventory.item_id == "starter-cap"))
        xp_count = db.scalar(select(func.count(XPTransaction.id)).where(XPTransaction.user_id == user.id, XPTransaction.source_type == "achievement_completed", XPTransaction.source_id == "first-task"))
        check(not second and achievement_count == 1, "re-running achievement evaluation does not duplicate the achievement")
        check(item_count == 1 and xp_count == 1, "cosmetic ownership and achievement XP are each granted exactly once")
        ensure_avatar_records(db, user.id); db.commit()
        starter_count = db.scalar(select(func.count(UserAvatarInventory.id)).where(UserAvatarInventory.user_id == user.id, UserAvatarInventory.acquired_via == "starter"))
        check(starter_count == 5, "new dog avatar receives free collar, bandana, and three background cosmetics")
    engine.dispose()
    _TEMP.cleanup()
    print("Gamification catalog tests passed.")


if __name__ == "__main__":
    main()
