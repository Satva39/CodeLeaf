"""Audit every published course exam bank using the production loader.

Run from backend/: python scripts/test_exam_question_bank_compatibility.py
A temporary SQLite URL is configured before importing the app; no production DB is used.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_TEMP_DIR = tempfile.TemporaryDirectory(prefix="codeleaf-exam-bank-compat-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TEMP_DIR.name) / 'exam-bank.db'}"
os.environ["JWT_SECRET"] = "exam-bank-compatibility-test-only-secret-2026"
os.environ["APP_ENV"] = "development"
os.environ["PREVIEW_DRAFT_COURSES"] = "false"

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import app.main as main_module  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.models import Course  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


def main() -> None:
    course_root = BACKEND_ROOT / "content" / "courses"
    checked = 0
    failures: list[str] = []
    published_courses: list[tuple[Path, dict[str, object], dict[str, object]]] = []
    for course_dir in sorted(path for path in course_root.iterdir() if path.is_dir()):
        manifest_path = course_dir / "course.json"
        blueprint_path = course_dir / "exams" / "exam-blueprint.json"
        if not manifest_path.is_file() or not blueprint_path.is_file():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            blueprint = json.loads(blueprint_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"{course_dir.name}: invalid manifest/blueprint JSON: {exc}")
            continue

        course_metadata = manifest.get("course", manifest)
        manifest_status = (
            course_metadata.get("status")
            if isinstance(course_metadata, dict) and course_metadata.get("status")
            else manifest.get("status")
        )
        if manifest_status != "published" or blueprint.get("status") != "published":
            continue
        published_courses.append((course_dir, manifest, blueprint))

    # Exercise the same manifest/database gate that the live exam routes use. Every
    # record lives in a temporary SQLite database, not the developer's configured DB.
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        for sort_order, (course_dir, manifest, _blueprint) in enumerate(published_courses):
            metadata = manifest.get("course") or {}
            db.add(
                Course(
                    slug=course_dir.name,
                    title=str(metadata.get("title") or course_dir.name.title()),
                    description=str(metadata.get("description") or "temporary exam test"),
                    category=str(metadata.get("category") or "Programming"),
                    level=str(metadata.get("level") or "Beginner"),
                    published=True,
                    sort_order=sort_order,
                )
            )
        db.commit()

        catalog_client = TestClient(main_module.app)
        catalog_response = catalog_client.get("/api/exams/catalog")
        if catalog_response.status_code != 200:
            failures.append(
                f"exam catalog endpoint returned HTTP {catalog_response.status_code}"
            )
            catalog_items = {}
        else:
            catalog_items = {
                item["slug"]: item
                for item in catalog_response.json().get("items", [])
                if isinstance(item, dict) and isinstance(item.get("slug"), str)
            }

        for course_dir, _manifest, blueprint in published_courses:
            slug = course_dir.name
            try:
                _course, resolved_dir, resolved_blueprint = main_module._load_exam_blueprint(slug, db)
                if resolved_dir != course_dir.resolve():
                    raise AssertionError("exam resolver returned an unexpected course directory")
                if resolved_blueprint.get("status") != "published":
                    raise AssertionError("published source blueprint was not returned as published")
                if slug not in catalog_items:
                    raise AssertionError("published course is absent from the exam catalog")
                if catalog_items[slug].get("available") is not True:
                    raise AssertionError(
                        f"catalog marked a published exam unavailable: {catalog_items[slug].get('message')}"
                    )
            except Exception as exc:
                failures.append(f"{slug}: exam publication gate: {type(exc).__name__}: {exc}")

    for course_dir, _manifest, blueprint in published_courses:
        slug = course_dir.name
        checked += 1
        try:
            pool = main_module._load_exam_question_pool(course_dir, blueprint)
            slot_count = len({int(item.get("lesson_number") or 0) for item in pool if int(item.get("lesson_number") or 0) > 0})
            picked = main_module._choose_exam_questions(pool, blueprint, count=20)
            if not pool:
                raise AssertionError("published question pool contains no usable questions")
            if slot_count < 1:
                raise AssertionError("question pool has no positive sampling slots")
            if not picked:
                raise AssertionError("exam selector returned no questions")
            if len({item["id"] for item in picked}) != len(picked):
                raise AssertionError("exam selector returned duplicate question IDs")
            if not main_module._has_published_exam_question_set(course_dir, blueprint):
                raise AssertionError("catalog readiness disagrees with the full question loader")
        except Exception as exc:  # include HTTPException validation errors in the report
            failures.append(f"{course_dir.name}: {type(exc).__name__}: {exc}")
            continue
        print(f"PASS {course_dir.name}: {len(pool)} published questions, {slot_count} sampling slots, {len(picked)} selectable")

    if failures:
        print("\nExam question-bank compatibility failures:")
        for failure in failures:
            print(f"FAIL {failure}")
        raise SystemExit(1)
    if checked == 0:
        raise SystemExit("No published course blueprints were found to validate.")
    print(f"\nExam question-bank compatibility passed for {checked} published course(s).")


if __name__ == "__main__":
    main()
