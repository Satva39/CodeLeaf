"""Verify importer idempotency, slug-rename identity, and course-level rollback.

Uses an isolated SQLite database and synthetic in-memory records. Does not reset,
drop, or connect to any configured user/production database.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

TEMP_DIR = tempfile.TemporaryDirectory(prefix="codeleaf-import-safety-")
DATABASE_PATH = Path(TEMP_DIR.name) / "import-safety.sqlite"
os.environ["APP_ENV"] = "test"
os.environ["JWT_SECRET"] = "course-import-test-only-secret-not-for-deployment"
os.environ["COOKIE_SECURE"] = "false"
os.environ["FRONTEND_ORIGINS"] = "http://localhost:5173"
os.environ["DATABASE_URL"] = f"sqlite:///{DATABASE_PATH.as_posix()}"

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(BACKEND_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT / "scripts"))

from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from app.db import Base, engine  # noqa: E402
from app.models import Course, Exercise, Lesson, LessonProgress, Module, User  # noqa: E402
import import_course_files as importer  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS {message}")


def make_tree(course_slug: str, lesson_slug: str = "lesson-start"):
    course_data = {
        "slug": course_slug,
        "title": f"{course_slug.title()} test course",
        "description": "Isolated importer test",
        "category": "Test",
        "level": "Beginner",
        "sort_order": 1,
    }
    module_data = {"id": f"{course_slug}-module-1", "slug": "intro", "title": "Introduction", "sequence": 1}
    lesson_data = {
        "id": f"{course_slug}-lesson-stable-001",
        "slug": lesson_slug,
        "title": "Stable lesson identity",
        "sequence": 1,
        "estimated_minutes": 8,
        "intro": "Initial content",
    }
    exercise_data = {
        "id": f"{course_slug}-exercise-001",
        "slug": "practice-1",
        "title": "Practice",
        "type": "short_answer",
        "prompt": "Write a short answer.",
        "grading_config": {"mode": "exact_text", "expected": "ok"},
        "sequence": 1,
    }
    tree = [(
        Path("module.json"),
        module_data,
        [(Path("lesson.json"), lesson_data, [(Path("exercise.json"), exercise_data)])],
    )]
    return course_data, tree


def count_rows(db, model) -> int:
    return int(db.scalar(select(func.count()).select_from(model)) or 0)


def main() -> int:
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    course_data, tree = make_tree("repeat-import")
    importer.import_course_transaction(course_data, tree, published=False, session_factory=TestSession)
    with TestSession() as db:
        first_counts = (count_rows(db, Course), count_rows(db, Module), count_rows(db, Lesson), count_rows(db, Exercise))
        course = db.scalar(select(Course).where(Course.slug == "repeat-import"))
        module = db.scalar(select(Module).where(Module.course_id == course.id))
        lesson = db.scalar(select(Lesson).where(Lesson.module_id == module.id))
        user = User(
            email="import-safety@example.invalid",
            display_name="Import Safety Test",
            username="import-safety-test",
            password_hash="not-a-real-login-hash",
        )
        db.add(user)
        db.flush()
        progress = LessonProgress(user_id=user.id, lesson_id=lesson.id, completed=True, time_spent_seconds=42)
        db.add(progress)
        db.commit()
        stable_lesson_id = lesson.id
        progress_id = progress.id
        learner_id = user.id

    importer.import_course_transaction(course_data, tree, published=False, session_factory=TestSession)
    with TestSession() as db:
        repeated_counts = (count_rows(db, Course), count_rows(db, Module), count_rows(db, Lesson), count_rows(db, Exercise))
    require(first_counts == repeated_counts, "importing the same course twice leaves row counts unchanged")

    renamed_course_data, renamed_tree = make_tree("repeat-import", lesson_slug="lesson-start-corrected")
    importer.import_course_transaction(renamed_course_data, renamed_tree, published=False, session_factory=TestSession)
    with TestSession() as db:
        lesson = db.scalar(select(Lesson).where(Lesson.module_id == module.id))
        progress = db.scalar(select(LessonProgress).where(LessonProgress.id == progress_id))
        count = db.scalar(select(func.count()).select_from(Lesson).where(Lesson.module_id == module.id))
        require(lesson.id == stable_lesson_id and lesson.slug == "lesson-start-corrected", "stable lesson ID safely updates a renamed slug")
        require(count == 1, "renamed lesson does not create a duplicate row")
        require(progress is not None and progress.user_id == learner_id and progress.lesson_id == stable_lesson_id, "learner progress remains attached to the existing lesson")

    before_rollback_counts = None
    with TestSession() as db:
        before_rollback_counts = (count_rows(db, Course), count_rows(db, Module), count_rows(db, Lesson), count_rows(db, Exercise))
    rollback_data, rollback_tree = make_tree("rollback-course")
    original_upsert_exercise = importer.upsert_exercise

    def fail_after_partial_write(db, lesson, data, published):
        original_upsert_exercise(db, lesson, data, published)
        raise RuntimeError("simulated importer failure after partial course writes")

    importer.upsert_exercise = fail_after_partial_write
    try:
        try:
            importer.import_course_transaction(rollback_data, rollback_tree, published=False, session_factory=TestSession)
        except RuntimeError as exc:
            require("simulated importer failure" in str(exc), "simulated DB/import exception is surfaced")
        else:
            raise AssertionError("expected simulated import failure")
    finally:
        importer.upsert_exercise = original_upsert_exercise
    with TestSession() as db:
        after_rollback_counts = (count_rows(db, Course), count_rows(db, Module), count_rows(db, Lesson), count_rows(db, Exercise))
        rollback_course = db.scalar(select(Course).where(Course.slug == "rollback-course"))
        progress = db.scalar(select(LessonProgress).where(LessonProgress.id == progress_id))
    require(before_rollback_counts == after_rollback_counts and rollback_course is None, "failed course transaction rolls back all partial writes")
    require(progress is not None and progress.lesson_id == stable_lesson_id, "rollback preserves existing learner records")

    bad_course = Path(TEMP_DIR.name) / "malformed-course"
    bad_course.mkdir()
    (bad_course / "course.json").write_text(json.dumps({
        "course": {"slug": "malformed-course", "title": "Malformed test", "status": "draft"},
        "module_files": ["../outside.json"],
    }), encoding="utf-8")
    try:
        importer.preflight_course(bad_course, "malformed-course")
    except ValueError:
        pass
    else:
        raise AssertionError("malformed/traversal manifest passed preflight")
    with TestSession() as db:
        require(db.scalar(select(Course).where(Course.slug == "malformed-course")) is None, "malformed manifest fails before any database writes")

    engine.dispose()
    TEMP_DIR.cleanup()
    print("All course importer safety checks passed; no configured user/production database was used.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
