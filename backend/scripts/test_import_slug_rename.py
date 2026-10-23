"""Verify stable-ID upserts update a lesson slug without leaving a duplicate row."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_TEMP_DIR = tempfile.TemporaryDirectory(prefix="codeleaf-slug-migration-test-")
os.environ["APP_ENV"] = "test"
os.environ["JWT_SECRET"] = "test-only-secret-not-for-deployment"
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TEMP_DIR.name) / 'slug-test.db'}"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import func, select  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.models import Course, Lesson, Module  # noqa: E402
from import_course_files import upsert_lesson  # noqa: E402


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        course = Course(
            slug="rename-test", title="Rename test", description="", category="Test",
            level="Beginner", published=False, sort_order=0,
        )
        db.add(course)
        db.flush()
        module = Module(course_id=course.id, slug="one", title="One", sort_order=1, level="Core")
        db.add(module)
        db.flush()
        old = Lesson(
            module_id=module.id, slug="old-slug", title="Stable ID lesson", sort_order=1,
            estimated_minutes=8, is_published=False,
            content={"intro": "existing"},
        )
        db.add(old)
        db.commit()
        old_id = old.id

        updated = upsert_lesson(
            db, module,
            {"id": "stable-lesson-001", "slug": "corrected-slug", "title": "Stable ID lesson",
             "sequence": 1, "estimated_minutes": 8, "intro": "updated"},
            published=True,
        )
        db.commit()
        count = db.scalar(select(func.count()).select_from(Lesson).where(Lesson.module_id == module.id))
        assert updated.id == old_id, "slug rename should update the existing row by stable ID"
        assert updated.slug == "corrected-slug", "the row should carry the new canonical slug"
        assert count == 1, f"expected one lesson row, found {count}"
        assert updated.content.get("id") == "stable-lesson-001", "stable manifest ID should be persisted in content"
    engine.dispose()
    _TEMP_DIR.cleanup()
    print("PASS stable lesson ID updates a renamed slug without leaving duplicate rows")


if __name__ == "__main__":
    main()
