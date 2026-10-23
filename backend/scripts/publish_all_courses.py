"""Publish and import every validated CodeLeaf course manifest.

Run from backend/:
  python scripts/publish_all_courses.py                 # safe dry run
  python scripts/publish_all_courses.py --apply --publish

The script sets only publication status fields in manifest-referenced public content,
then invokes the existing importer per course. If validation/import fails for a course,
that course's edited files are restored to their previous bytes. Existing data and user
progress are preserved by the importer's natural-key upserts.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[1]
# A script launched as `python scripts/publish_all_courses.py` gets scripts/ as
# sys.path[0]. Add backend/ explicitly so imports such as `from app.db import engine` work.
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
from app.diagram_assets import resolve_dynamic_diagram, validate_dynamic_diagram_model

CONTENT_ROOT = BACKEND_ROOT / "content" / "courses"
IMPORT_SCRIPT = BACKEND_ROOT / "scripts" / "import_course_files.py"
_DIAGRAM_MODEL_CACHE: dict[Path, dict[str, Any]] = {}


@dataclass
class CoursePlan:
    slug: str
    title: str
    target_fields: dict[Path, str]
    modules: int
    lessons: int
    exercises: int
    projects: int
    assessments: int
    references: int


def read_object(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid or unreadable JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return data


def safe_json_path(course_dir: Path, base: Path, relative: Any, label: str) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise ValueError(f"{label}: expected a relative JSON path")
    path = (base / relative).resolve()
    root = course_dir.resolve()
    if root not in path.parents or path.suffix.lower() != ".json" or not path.is_file():
        raise ValueError(f"{label}: missing or unsafe JSON path {relative!r}")
    # Validate the bytes now so publishing doesn't begin with a broken manifest.
    read_object(path)
    return path


def add_target(targets: dict[Path, str], path: Path, field: str = "status") -> None:
    previous = targets.get(path)
    if previous and previous != field:
        raise ValueError(f"Conflicting publication fields for {path}")
    targets[path] = field



def walk_objects(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_objects(child)


def validate_lesson_diagram_assets(course_dir: Path, lesson_path: Path, lesson_doc: dict[str, Any]) -> int:
    """Validate diagram links through the same contract as import and API reads."""
    count = 0
    for node in walk_objects(lesson_doc):
        if node.get("type") != "diagram":
            continue
        if "asset_path" not in node:
            raise ValueError(f"{lesson_path}: diagram block is missing asset_path")
        model_path = resolve_dynamic_diagram(
            course_dir, node.get("asset_path"), f"{lesson_path.name}.diagram"
        )
        if model_path not in _DIAGRAM_MODEL_CACHE:
            _DIAGRAM_MODEL_CACHE[model_path] = validate_dynamic_diagram_model(
                model_path, f"{lesson_path.name}.diagram"
            )
        count += 1
    return count


def make_plan(course_dir: Path) -> CoursePlan:
    course_json = (course_dir / "course.json").resolve()
    if not course_json.is_file():
        raise ValueError(f"Missing course.json in {course_dir}")
    course_doc = read_object(course_json)
    course = course_doc.get("course")
    if not isinstance(course, dict):
        raise ValueError(f"{course_json}: expected a 'course' object")
    slug = course.get("slug")
    title = course.get("title")
    if slug != course_dir.name or not isinstance(title, str) or not title.strip():
        raise ValueError(f"{course_json}: folder/slug mismatch or missing title")

    targets: dict[Path, str] = {course_json: "course.status"}
    counts = {key: 0 for key in ("modules", "lessons", "exercises", "projects", "assessments", "references")}

    module_files = course_doc.get("module_files")
    if not isinstance(module_files, list) or not module_files:
        raise ValueError(f"{course_json}: module_files must be a non-empty array")
    for module_rel in module_files:
        module_path = safe_json_path(course_dir, course_dir, module_rel, "module_files")
        module = read_object(module_path)
        if not str(module.get("title", "")).strip() or not str(module.get("slug", "")).strip():
            raise ValueError(f"{module_path}: module requires title and slug")
        add_target(targets, module_path)
        counts["modules"] += 1
        lesson_files = module.get("lesson_files")
        if not isinstance(lesson_files, list) or not lesson_files:
            raise ValueError(f"{module_path}: lesson_files must be a non-empty array")
        for lesson_rel in lesson_files:
            lesson_path = safe_json_path(course_dir, module_path.parent, lesson_rel, "lesson_files")
            lesson = read_object(lesson_path)
            if not str(lesson.get("title", "")).strip() or not str(lesson.get("slug", "")).strip():
                raise ValueError(f"{lesson_path}: lesson requires title and slug")
            validate_lesson_diagram_assets(course_dir, lesson_path, lesson)
            add_target(targets, lesson_path)
            counts["lessons"] += 1
            # Knowledge-check answer keys remain in backend content; the API must continue
            # to return only learner-safe question fields.
            content = lesson.get("content") or {}
            if isinstance(content, dict) and content.get("knowledge_check_file"):
                question_path = safe_json_path(
                    course_dir, course_dir, content["knowledge_check_file"], "knowledge_check_file"
                )
                add_target(targets, question_path)
            exercise_files = lesson.get("exercise_files", [])
            if not isinstance(exercise_files, list):
                raise ValueError(f"{lesson_path}: exercise_files must be an array")
            for exercise_rel in exercise_files:
                exercise_path = safe_json_path(
                    course_dir, lesson_path.parent, exercise_rel, "exercise_files"
                )
                exercise_doc = read_object(exercise_path)
                if not str(exercise_doc.get("title", "")).strip() or not str(exercise_doc.get("slug", "")).strip() or not str(exercise_doc.get("prompt", "")).strip():
                    raise ValueError(f"{exercise_path}: exercise requires title, slug and prompt")
                if not isinstance(exercise_doc.get("grading_config"), dict):
                    raise ValueError(f"{exercise_path}: grading_config must be an object")
                add_target(targets, exercise_path)
                counts["exercises"] += 1

    project_files = course_doc.get("project_files", [])
    if not isinstance(project_files, list):
        raise ValueError(f"{course_json}: project_files must be an array")
    for project_rel in project_files:
        project_path = safe_json_path(course_dir, course_dir, project_rel, "project_files")
        add_target(targets, project_path)
        counts["projects"] += 1

    assessment_files = course_doc.get("assessment_files", [])
    if not isinstance(assessment_files, list):
        raise ValueError(f"{course_json}: assessment_files must be an array")
    for assessment_rel in assessment_files:
        assessment_path = safe_json_path(course_dir, course_dir, assessment_rel, "assessment_files")
        add_target(targets, assessment_path)
        counts["assessments"] += 1
        assessment_doc = read_object(assessment_path)
        if assessment_path.name == "exam-blueprint.json":
            for question_rel in assessment_doc.get("question_files", []):
                question_path = safe_json_path(
                    course_dir, assessment_path.parent, question_rel, "exam question_files"
                )
                add_target(targets, question_path)

    reference_rel = course_doc.get("reference_index") or "references/reference-index.json"
    reference_path = (course_dir / str(reference_rel)).resolve()
    if course_dir.resolve() not in reference_path.parents:
        raise ValueError(f"{course_json}: unsafe reference_index path")
    if reference_path.is_file():
        read_object(reference_path)
        add_target(targets, reference_path)
        counts["references"] = 1

    return CoursePlan(
        slug=slug,
        title=title,
        target_fields=targets,
        modules=counts["modules"],
        lessons=counts["lessons"],
        exercises=counts["exercises"],
        projects=counts["projects"],
        assessments=counts["assessments"],
        references=counts["references"],
    )


def set_published(plan: CoursePlan) -> dict[Path, bytes]:
    """Write publication fields and return the original bytes for rollback."""
    originals: dict[Path, bytes] = {}
    try:
        for path, field in plan.target_fields.items():
            original = path.read_bytes()
            data = read_object(path)
            changed = False
            if field == "course.status":
                if not isinstance(data.get("course"), dict):
                    raise ValueError(f"{path}: missing course object")
                if data["course"].get("status") != "published":
                    data["course"]["status"] = "published"
                    changed = True
            elif data.get("status") != "published":
                data["status"] = "published"
                changed = True
            if changed:
                originals[path] = original
                path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return originals
    except Exception:
        restore_files(originals)
        raise


def restore_files(originals: dict[Path, bytes]) -> None:
    for path, original in originals.items():
        path.write_bytes(original)


def check_database() -> None:
    try:
        from sqlalchemy import inspect
        from app.db import engine
    except Exception as exc:
        raise RuntimeError(f"Could not load database dependencies: {exc}") from exc
    if engine is None:
        raise RuntimeError("DATABASE_URL is not configured. Set backend/.env and restart this command.")
    try:
        with engine.connect():
            tables = set(inspect(engine).get_table_names())
    except Exception as exc:
        raise RuntimeError(f"Cannot connect to PostgreSQL: {exc}") from exc
    required = {"courses", "course_modules", "lessons", "exercises"}
    missing = sorted(required - tables)
    if missing:
        raise RuntimeError(
            "Database tables are missing: " + ", ".join(missing)
            + ". From backend/, run `alembic upgrade head` and `python scripts/init_db.py`, then retry."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write publication statuses and import courses")
    parser.add_argument("--publish", action="store_true", help="Explicitly confirm public publication of all validated course manifests")
    parser.add_argument("--course-slug", help="Optional: publish/import one course only")
    args = parser.parse_args()
    if args.publish and not args.apply:
        parser.error("--publish requires --apply")
    if args.apply and not args.publish:
        parser.error("Publishing requires both --apply and --publish")

    course_dirs = sorted(
        path for path in CONTENT_ROOT.iterdir()
        if path.is_dir() and (path / "course.json").is_file()
    ) if CONTENT_ROOT.is_dir() else []
    if args.course_slug:
        course_dirs = [path for path in course_dirs if path.name == args.course_slug]
        if not course_dirs:
            parser.error(f"No course manifest found for slug {args.course_slug!r}")
    if not course_dirs:
        raise SystemExit(f"No course manifests found under {CONTENT_ROOT}")

    plans: list[CoursePlan] = []
    preflight_errors: list[tuple[str, str]] = []
    for course_dir in course_dirs:
        try:
            # Check every manifest reference and diagram model while constructing the
            # publication plan, before statuses or database rows can be changed.
            plans.append(make_plan(course_dir))
        except Exception as exc:
            preflight_errors.append((course_dir.name, str(exc)))
    print(f"Course manifests discovered: {len(course_dirs)}; preflight-ready: {len(plans)}")
    print("Records:",
          f"{sum(p.modules for p in plans)} modules,",
          f"{sum(p.lessons for p in plans)} lessons,",
          f"{sum(p.exercises for p in plans)} exercises,",
          f"{sum(p.projects for p in plans)} projects,",
          f"{sum(p.assessments for p in plans)} assessment files,",
          f"{sum(p.references for p in plans)} reference indexes.")
    if preflight_errors:
        print("Preflight errors (no files changed):")
        for slug, error in preflight_errors:
            print(f"  - {slug}: {error}")
        return 1
    if not args.apply:
        print("DRY RUN ONLY: no files or database rows changed.")
        print("After checking the output, run: python scripts/publish_all_courses.py --apply --publish")
        return 0

    check_database()  # Fail before modifying any content if PostgreSQL is unavailable.
    succeeded: list[str] = []
    failed: list[tuple[str, str]] = []
    for index, plan in enumerate(plans, 1):
        print(f"\n[{index}/{len(plans)}] Publishing {plan.slug} — {plan.title}", flush=True)
        try:
            originals = set_published(plan)
        except Exception as exc:
            failed.append((plan.slug, f"could not update status fields: {exc}"))
            print(f"  FAILED before import: {exc}", flush=True)
            continue
        result = subprocess.run(
            [sys.executable, str(IMPORT_SCRIPT), "--course-slug", plan.slug, "--apply", "--publish"],
            cwd=BACKEND_ROOT,
            check=False,
        )
        if result.returncode == 0:
            succeeded.append(plan.slug)
            print(f"  PUBLISHED: {plan.slug}", flush=True)
        else:
            restore_files(originals)
            failed.append((plan.slug, f"import/validation exited with code {result.returncode}; source statuses restored"))
            print(f"  FAILED: {plan.slug}; source statuses restored.", flush=True)

    print("\nPUBLICATION SUMMARY")
    print(f"Succeeded: {len(succeeded)} / {len(plans)}")
    if succeeded:
        print("Published slugs: " + ", ".join(succeeded))
    if failed:
        print("Failed courses (fix the reported validation/database problem and retry):")
        for slug, reason in failed:
            print(f"  - {slug}: {reason}")
        return 1
    print("All selected courses were validated, imported, and published.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
