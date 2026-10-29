"""Import a directory-based CodeLeaf course into SQLAlchemy/PostgreSQL.

The command defaults to a validation-only dry run. Apply only after reviewing every file.
Run from backend/: python scripts/import_course_files.py --course-slug html --apply [--publish]
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select
from app.db import SessionLocal, engine
from app.models import Course, Module, Lesson, Exercise
from app.course_content_validation import validate_course_tree

CONTENT_ROOT = Path(__file__).resolve().parents[1] / "content" / "courses"


def read_json(path: Path) -> dict[str, Any]:
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read valid JSON from {path}: {exc}") from exc
    if not isinstance(result, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return result


def upsert_course(db, course_data, published: bool):
    """Upsert by the course's stable public slug; never delete existing rows."""
    row = db.scalar(select(Course).where(Course.slug == course_data["slug"]))
    values = {
        "title": course_data["title"],
        "description": course_data.get("description", ""),
        "category": course_data.get("category", "Programming"),
        "level": course_data.get("level", "Beginner"),
        "published": published,
        "sort_order": int(course_data.get("sort_order", 0)),
    }
    if row is None:
        row = Course(slug=course_data["slug"], **values)
        db.add(row)
        db.flush()
    else:
        for key, value in values.items():
            setattr(row, key, value)
    return row


def upsert_module(db, course, data, published: bool):
    """Upsert by (course_id, module slug), preserving module identity/relations."""
    row = db.scalar(select(Module).where(Module.course_id == course.id, Module.slug == data["slug"]))
    values = {"title": data["title"], "sort_order": int(data.get("sequence", 0)), "level": data.get("track", data.get("level", "Core"))}
    if row is None:
        row = Module(course_id=course.id, slug=data["slug"], **values)
        db.add(row)
        db.flush()
    else:
        for key, value in values.items():
            setattr(row, key, value)
    return row


def upsert_lesson(db, module, data, published: bool):
    """Upsert by (module_id, slug), then stable content ID for safe slug renames."""
    row = db.scalar(select(Lesson).where(Lesson.module_id == module.id, Lesson.slug == data["slug"]))
    # If a lesson slug is corrected but its stable content ID remains the same, update
    # the existing row instead of inserting a second record and leaving a stale URL.
    content_id = data.get("id")
    module_lessons = None
    if row is None and content_id:
        module_lessons = db.scalars(select(Lesson).where(Lesson.module_id == module.id)).all()
        row = next(
            (candidate for candidate in module_lessons if (candidate.content or {}).get("id") == content_id),
            None,
        )
    # Older imports did not persist the manifest ID in content JSON. Fall back only
    # when sort order and title identify exactly one row within the same module.
    sequence = int(data.get("sequence", 0))
    if row is None and sequence > 0:
        candidates = db.scalars(
            select(Lesson).where(Lesson.module_id == module.id, Lesson.sort_order == sequence)
        ).all()
        if len(candidates) == 1 and candidates[0].title == data["title"]:
            row = candidates[0]
    # Persist the stable ID in lesson content for future migrations and API identity.
    content = {key: value for key, value in data.items() if key not in {"slug", "title", "sequence", "estimated_minutes", "exercise_files", "status"}}
    values = {"slug": data["slug"], "title": data["title"], "content": content,
              "sort_order": sequence,
              "estimated_minutes": int(data.get("estimated_minutes", 8)), "is_published": published}
    if row is None:
        row = Lesson(module_id=module.id, **values)
        db.add(row)
        db.flush()
    else:
        for key, value in values.items():
            setattr(row, key, value)
    return row


def upsert_exercise(db, lesson, data, published: bool):
    """Upsert by (lesson_id, exercise slug); existing exercise rows are never deleted."""
    row = db.scalar(select(Exercise).where(Exercise.lesson_id == lesson.id, Exercise.slug == data["slug"]))
    values = {
        "title": data["title"], "exercise_type": data.get("type", "short_answer"),
        "prompt": data["prompt"], "starter": data.get("starter", {}),
        "public_tests": data.get("public_tests", []), "acceptance_criteria": data.get("acceptance_criteria", []),
        "hints": data.get("hints", []), "solution": data.get("solution", {}),
        "grading_config": data.get("grading_config", {}), "sequence": int(data.get("sequence", 0)),
        "difficulty": data.get("difficulty", "easy"), "xp_points": 20, "is_published": published,
    }
    # Premium flags may be managed in the database while course manifests are
    # being migrated. Do not silently clear an existing lock if a routine import
    # omits the optional flag; only an explicit manifest value changes it.
    if "is_premium" in data or "premium" in data:
        values["is_premium"] = bool(data.get("is_premium", data.get("premium", False)))
    if row is None:
        row = Exercise(lesson_id=lesson.id, slug=data["slug"], **values)
        db.add(row)
    else:
        for key, value in values.items():
            setattr(row, key, value)


def preflight_course(course_dir: Path, expected_slug: str | None = None):
    """Fully validate referenced content before opening a database transaction."""
    course_dir = course_dir.resolve()
    course_path = course_dir / "course.json"
    course_doc = read_json(course_path)
    course_data = course_doc.get("course")
    if not isinstance(course_data, dict) or not course_data.get("slug") or not course_data.get("title"):
        raise ValueError("course.json needs course.slug and course.title")
    if expected_slug is not None and course_data["slug"] != expected_slug:
        raise ValueError(
            f"Course folder/slug mismatch: folder={expected_slug}, metadata={course_data['slug']}"
        )
    # Validates manifest references, stable IDs, relationships, grader shapes, assets,
    # native diagram models, and source-text mappings without mutating files or the DB.
    validate_course_tree(course_dir)
    return course_doc, validate_course(course_dir, course_doc)


def import_course_records(db, course_data: dict[str, Any], tree, published: bool):
    """Apply one course's upserts within a caller-owned transaction."""
    course = upsert_course(db, course_data, published)
    for _module_path, module_data, lessons_tree in tree:
        module = upsert_module(db, course, module_data, published)
        for _lesson_path, lesson_data, exercises_tree in lessons_tree:
            lesson = upsert_lesson(db, module, lesson_data, published)
            for _exercise_path, exercise_data in exercises_tree:
                upsert_exercise(db, lesson, exercise_data, published)
    db.flush()
    return course


def import_course_transaction(course_data: dict[str, Any], tree, published: bool, session_factory=None):
    """Commit all course rows together or roll them all back on any exception."""
    factory = session_factory or SessionLocal
    if factory is None:
        raise RuntimeError("DATABASE_URL is not configured; set backend/.env first.")
    with factory() as db:
        try:
            course = import_course_records(db, course_data, tree, published)
            db.commit()
            return course
        except Exception:
            db.rollback()
            raise


def validate_course(course_dir: Path, course_doc: dict[str, Any]) -> list[tuple[Path, dict[str, Any], list[tuple[Path, dict[str, Any], list[tuple[Path, dict[str, Any]]]]]]]:
    tree = []
    module_files = course_doc.get("module_files", [])
    if not module_files:
        raise ValueError("course.json must contain a non-empty module_files array")
    for module_rel in module_files:
        module_path = (course_dir / module_rel).resolve()
        if course_dir.resolve() not in module_path.parents:
            raise ValueError(f"Module path escapes course directory: {module_rel}")
        module_data = read_json(module_path)
        lessons_tree = []
        for lesson_rel in module_data.get("lesson_files", []):
            lesson_path = (module_path.parent / lesson_rel).resolve()
            if course_dir.resolve() not in lesson_path.parents:
                raise ValueError(f"Lesson path escapes course directory: {lesson_rel}")
            lesson_data = read_json(lesson_path)
            exercises_tree = []
            for exercise_rel in lesson_data.get("exercise_files", []):
                exercise_path = (lesson_path.parent / exercise_rel).resolve()
                if course_dir.resolve() not in exercise_path.parents:
                    raise ValueError(f"Exercise path escapes course directory: {exercise_rel}")
                exercise_data = read_json(exercise_path)
                if "grading_config" not in exercise_data:
                    raise ValueError(f"Exercise has no server-side grading_config: {exercise_path}")
                exercises_tree.append((exercise_path, exercise_data))
            lessons_tree.append((lesson_path, lesson_data, exercises_tree))
        tree.append((module_path, module_data, lessons_tree))
    return tree


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course-slug", required=True, help="Course folder name, e.g. html or python")
    parser.add_argument("--apply", action="store_true", help="Write draft records to the configured database")
    parser.add_argument("--publish", action="store_true", help="Publish the course, modules' lessons and exercises (use only after review)")
    args = parser.parse_args()
    if args.publish and not args.apply:
        parser.error("--publish requires --apply")
    course_dir = (CONTENT_ROOT / args.course_slug).resolve()
    if CONTENT_ROOT.resolve() not in course_dir.parents:
        parser.error("Invalid course slug/path")
    try:
        course_doc, tree = preflight_course(course_dir, args.course_slug)
        course_data = course_doc["course"]
    except (OSError, ValueError, TypeError) as exc:
        raise SystemExit(f"Course preflight failed before any database writes: {exc}") from exc
    module_count = len(tree)
    lesson_count = sum(len(lessons) for _, _, lessons in tree)
    exercise_count = sum(len(exercises) for _, _, lessons in tree for _, _, exercises in lessons)
    print(f"Validated course '{course_data['title']}': {module_count} module(s), {lesson_count} lesson(s), {exercise_count} exercise(s).")
    print(f"Mode: {'PUBLISH' if args.publish else 'DRAFT'}; action: {'DATABASE WRITE' if args.apply else 'DRY RUN ONLY'}.")
    if not args.apply:
        print("No database changes made. Re-run with --apply after reviewing the content files.")
        return
    if engine is None or SessionLocal is None:
        raise SystemExit("DATABASE_URL is not configured; set backend/.env first.")
    import_course_transaction(course_data, tree, args.publish)
    print("Import complete. Course visibility follows the requested publish flag.")


if __name__ == "__main__":
    main()
