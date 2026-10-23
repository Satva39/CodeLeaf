"""Validate CodeLeaf course manifests, referenced content and dynamic diagram assets.

Run from backend/:
  python scripts/validate_course_manifests.py
  python scripts/validate_course_manifests.py --course html

This script is read-only. It never publishes a course or writes to PostgreSQL.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.diagram_assets import (  # noqa: E402
    resolve_dynamic_diagram as _resolve_dynamic_diagram,
    validate_dynamic_diagram_model,
)

CONTENT_ROOT = BACKEND_ROOT / "content" / "courses"


@dataclass
class ValidationReport:
    course_slug: str
    title: str = ""
    modules: int = 0
    lessons: int = 0
    exercises: int = 0
    projects: int = 0
    assessments: int = 0
    diagrams: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def read_object(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid or unreadable JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return data


def resolve_json(root: Path, base: Path, relative: Any, label: str) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise ValueError(f"{label}: expected a relative JSON path")
    path = (base / relative).resolve()
    root = root.resolve()
    if root not in path.parents or path.suffix.lower() != ".json" or not path.is_file():
        raise ValueError(f"{label}: missing or unsafe path {relative!r}")
    return path


def walk_values(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_values(child)


def resolve_dynamic_diagram(course_dir: Path, relative_asset: str, label: str) -> Path:
    """Compatibility wrapper around the shared path-safe diagram contract."""
    return _resolve_dynamic_diagram(course_dir, relative_asset, label)


def validate_dynamic_model(model_path: Path, label: str) -> dict[str, Any]:
    """Compatibility wrapper around the shared native-model validator."""
    return validate_dynamic_diagram_model(model_path, label)


def validate_course_directory(course_dir: Path) -> ValidationReport:
    course_dir = course_dir.resolve()
    report = ValidationReport(course_slug=course_dir.name)
    course_path = course_dir / "course.json"
    if not course_path.is_file():
        raise ValueError(f"missing {course_path}")
    course_doc = read_object(course_path)
    course = course_doc.get("course")
    if not isinstance(course, dict):
        raise ValueError(f"{course_path}: expected a 'course' object")
    slug = course.get("slug")
    title = course.get("title")
    if slug != course_dir.name:
        raise ValueError(f"{course_path}: course slug must match directory name")
    if not isinstance(title, str) or not title.strip():
        raise ValueError(f"{course_path}: missing course title")
    report.title = title
    if not str(course.get("description", "")).strip():
        report.warnings.append("course description is empty")

    module_files = course_doc.get("module_files")
    if not isinstance(module_files, list) or not module_files:
        raise ValueError(f"{course_path}: module_files must be a non-empty array")
    seen_module_slugs: set[str] = set()
    seen_lesson_slugs: set[str] = set()
    diagram_cache: dict[Path, dict[str, Any]] = {}

    for module_rel in module_files:
        module_path = resolve_json(course_dir, course_dir, module_rel, "module_files")
        module = read_object(module_path)
        report.modules += 1
        if not str(module.get("title", "")).strip() or not str(module.get("slug", "")).strip():
            raise ValueError(f"{module_path}: module requires title and slug")
        if module["slug"] in seen_module_slugs:
            raise ValueError(f"{module_path}: duplicate module slug {module['slug']!r}")
        seen_module_slugs.add(module["slug"])
        lesson_files = module.get("lesson_files")
        if not isinstance(lesson_files, list) or not lesson_files:
            raise ValueError(f"{module_path}: lesson_files must be a non-empty array")

        for lesson_rel in lesson_files:
            lesson_path = resolve_json(course_dir, module_path.parent, lesson_rel, "lesson_files")
            lesson = read_object(lesson_path)
            report.lessons += 1
            if not str(lesson.get("title", "")).strip() or not str(lesson.get("slug", "")).strip():
                raise ValueError(f"{lesson_path}: lesson requires title and slug")
            if lesson["slug"] in seen_lesson_slugs:
                raise ValueError(f"{lesson_path}: duplicate lesson slug {lesson['slug']!r} in course")
            seen_lesson_slugs.add(lesson["slug"])
            if not isinstance(lesson.get("content", {}), (dict, list)):
                raise ValueError(f"{lesson_path}: content must be an object or array")
            assets_root = (course_dir / "assets").resolve()
            for node in walk_values(lesson):
                if node.get("type") == "diagram" and isinstance(node.get("asset_path"), str):
                    model_path = resolve_dynamic_diagram(
                        course_dir, node["asset_path"], f"{lesson_path.name}.diagram"
                    )
                    if model_path not in diagram_cache:
                        diagram_cache[model_path] = validate_dynamic_model(
                            model_path, f"{lesson_path.name}.diagram"
                        )
                    report.diagrams += 1
                    if not str(node.get("alt_text", "")).strip():
                        report.warnings.append(
                            f"diagram missing alt text: {lesson_path.relative_to(course_dir)}"
                        )
                # Validate referenced private files without exposing their content.
                for key in ("knowledge_check_file", "reference_solution_file", "answer_key_file"):
                    rel = node.get(key)
                    if rel:
                        resolved = (course_dir / str(rel)).resolve()
                        if course_dir not in resolved.parents or not resolved.is_file():
                            raise ValueError(f"{lesson_path}: missing or unsafe {key} {rel!r}")

            exercise_files = lesson.get("exercise_files", [])
            if not isinstance(exercise_files, list):
                raise ValueError(f"{lesson_path}: exercise_files must be an array")
            seen_exercises: set[str] = set()
            for exercise_rel in exercise_files:
                exercise_path = resolve_json(course_dir, lesson_path.parent, exercise_rel, "exercise_files")
                exercise = read_object(exercise_path)
                report.exercises += 1
                if not str(exercise.get("title", "")).strip() or not str(exercise.get("slug", "")).strip():
                    raise ValueError(f"{exercise_path}: exercise requires title and slug")
                if exercise["slug"] in seen_exercises:
                    raise ValueError(f"{exercise_path}: duplicate exercise slug within lesson")
                seen_exercises.add(exercise["slug"])
                if not isinstance(exercise.get("grading_config"), dict):
                    raise ValueError(f"{exercise_path}: grading_config must be an object")

    project_files = course_doc.get("project_files", [])
    if not isinstance(project_files, list):
        raise ValueError(f"{course_path}: project_files must be an array")
    seen_projects: set[str] = set()
    for project_rel in project_files:
        project_path = resolve_json(course_dir, course_dir, project_rel, "project_files")
        project = read_object(project_path)
        report.projects += 1
        if not str(project.get("title", "")).strip() or not str(project.get("slug", "")).strip():
            raise ValueError(f"{project_path}: project requires title and slug")
        if project["slug"] in seen_projects:
            raise ValueError(f"{project_path}: duplicate project slug")
        seen_projects.add(project["slug"])

    assessment_files = course_doc.get("assessment_files", [])
    if not isinstance(assessment_files, list):
        raise ValueError(f"{course_path}: assessment_files must be an array")
    for assessment_rel in assessment_files:
        assessment_path = resolve_json(course_dir, course_dir, assessment_rel, "assessment_files")
        assessment = read_object(assessment_path)
        report.assessments += 1
        question_files = assessment.get("question_files", [])
        if not isinstance(question_files, list):
            raise ValueError(f"{assessment_path}: question_files must be an array")
        for question_rel in question_files:
            question_path = resolve_json(course_dir, assessment_path.parent, question_rel, "exam question_files")
            read_object(question_path)

    reference_rel = course_doc.get("reference_index") or "references/reference-index.json"
    reference_path = (course_dir / str(reference_rel)).resolve()
    if course_dir not in reference_path.parents:
        raise ValueError(f"{course_path}: unsafe reference_index path")
    if reference_path.is_file():
        reference = read_object(reference_path)
        items = reference.get("items", reference.get("references", []))
        if not isinstance(items, list):
            report.warnings.append("reference index has no array named items/references")
    else:
        report.warnings.append(f"reference index missing: {reference_rel}")

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course", help="Validate one course slug, e.g. html")
    args = parser.parse_args()
    if args.course:
        course_dirs = [CONTENT_ROOT / args.course]
        if not course_dirs[0].is_dir():
            parser.error(f"Course not found: {args.course}")
    else:
        course_dirs = sorted(path.parent for path in CONTENT_ROOT.glob("*/course.json"))
    if not course_dirs:
        print(f"No course manifests found under {CONTENT_ROOT}", file=sys.stderr)
        return 1

    reports: list[ValidationReport] = []
    errors: list[tuple[str, str]] = []
    for course_dir in course_dirs:
        try:
            reports.append(validate_course_directory(course_dir))
        except Exception as exc:
            errors.append((course_dir.name, str(exc)))
    print(f"Course manifests checked: {len(course_dirs)}; passed: {len(reports)}; failed: {len(errors)}")
    print("Records: " + ", ".join(
        f"{field}={sum(getattr(r, field) for r in reports)}"
        for field in ("modules", "lessons", "exercises", "projects", "assessments", "diagrams")
    ))
    warning_count = sum(len(report.warnings) for report in reports)
    print(f"Content warnings: {warning_count}")
    for slug, error in errors[:100]:
        print(f"FAIL {slug}: {error}")
    if errors:
        return 1
    print("PASS: all manifest-referenced JSON, diagram files, node IDs, and edge references are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
