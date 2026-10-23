"""Strict, filesystem-only validation for CodeLeaf's directory-based course content."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .diagram_assets import (
    resolve_dynamic_diagram,
    validate_dynamic_diagram_model,
)

ALLOWED_GRADING_MODES = {"choice", "exact_text", "contains_all"}
FORBIDDEN_XP_KEYS = {
    "xp_reward",
    "xp_points",
    "xp_override",
    "lesson_xp",
    "exercise_xp",
}
ALLOWED_ASSET_SUFFIXES = {".svg", ".webp", ".png", ".jpg", ".jpeg", ".gif", ".mp4"}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _safe_relative(base: Path, relative: str, boundary: Path, label: str) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise ValueError(f"{label}: expected a non-empty relative path")
    candidate = (base / relative).resolve()
    root = boundary.resolve()
    if root != candidate and root not in candidate.parents:
        raise ValueError(f"{label}: path escapes allowed directory: {relative}")
    if not candidate.is_file():
        raise ValueError(f"{label}: file does not exist: {relative}")
    return candidate


def _asset_or_dynamic_model(
    base: Path, relative: str, boundary: Path, label: str, *, prefer_dynamic: bool = True
) -> Path:
    """Resolve a safe asset, routing diagram paths through the shared model contract."""
    if not isinstance(relative, str) or not relative.strip():
        raise ValueError(f"{label}: expected a non-empty relative asset path")
    clean = relative.strip()
    path_parts = clean.split("/")
    normalized_for_diagram = clean[7:] if clean.startswith("assets/") else clean
    is_diagram_path = normalized_for_diagram.startswith("diagrams/")
    if is_diagram_path and (
        normalized_for_diagram.lower().endswith(".svg")
        or normalized_for_diagram.lower().endswith(".diagram.json")
    ):
        # `boundary` is the course assets root at all call sites; `base` may be
        # either that root or the course root (for paths beginning with assets/).
        return resolve_dynamic_diagram(boundary.resolve().parent, normalized_for_diagram, label)

    rel = Path(clean)
    if "\\" in clean or rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"{label}: unsafe asset path {relative!r}")
    root = boundary.resolve()
    candidate = (base / rel).resolve()
    if root not in candidate.parents:
        raise ValueError(f"{label}: asset path escapes allowed directory")
    if candidate.suffix.lower() == ".svg" and prefer_dynamic:
        paired = candidate.with_suffix(".diagram.json")
        if root not in paired.resolve().parents:
            raise ValueError(f"{label}: dynamic diagram path escapes allowed directory")
        if paired.is_file():
            return paired.resolve()
    if candidate.is_file():
        return candidate
    raise ValueError(f"{label}: asset does not exist: {relative!r}")


def _validate_dynamic_model(model_path: Path, label: str) -> None:
    """Backward-compatible name for the shared native diagram validator."""
    validate_dynamic_diagram_model(model_path, label)


def _walk_forbidden_xp(value: Any, path: str, findings: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in FORBIDDEN_XP_KEYS:
                findings.append(f"{path}: forbidden course-authored XP key '{key}'")
            _walk_forbidden_xp(child, f"{path}.{key}", findings)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_forbidden_xp(child, f"{path}[{index}]", findings)


def validate_course_tree(course_dir: Path) -> dict[str, Any]:
    """Validate all referenced course files, not just files imported into SQL tables."""
    course_dir = course_dir.resolve()
    course_path = course_dir / "course.json"
    if not course_path.is_file():
        raise ValueError(f"Course metadata missing: {course_path}")
    course_doc = _read_json(course_path)
    course_data = course_doc.get("course")
    if not isinstance(course_data, dict):
        raise ValueError("course.json must contain a course object")
    slug = course_data.get("slug")
    if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        raise ValueError("course.slug must be a lowercase URL slug")
    if course_dir.name != slug:
        raise ValueError(f"Course folder/slug mismatch: {course_dir.name} != {slug}")
    if (
        not isinstance(course_data.get("title"), str)
        or not course_data["title"].strip()
    ):
        raise ValueError("course.title must be a non-empty string")
    if course_data.get("status", "draft") not in {"draft", "published"}:
        raise ValueError("course.status must be 'draft' or 'published'")

    all_json: dict[Path, dict[str, Any]] = {}
    findings: list[str] = []
    for path in sorted(course_dir.rglob("*.json")):
        try:
            all_json[path.resolve()] = _read_json(path)
        except ValueError as exc:
            findings.append(str(exc))
    if findings:
        raise ValueError("\n".join(findings))

    seen_ids: dict[str, str] = {}

    def claim_id(doc: dict[str, Any], path: Path) -> None:
        item_id = doc.get("id")
        if not isinstance(item_id, str) or not item_id.strip():
            findings.append(f"{path.relative_to(course_dir)}: missing stable id")
        elif item_id in seen_ids:
            findings.append(
                f"duplicate id '{item_id}' in {seen_ids[item_id]} and {path.relative_to(course_dir)}"
            )
        else:
            seen_ids[item_id] = str(path.relative_to(course_dir))

    module_files = course_doc.get("module_files")
    if not isinstance(module_files, list) or not module_files:
        findings.append("course.json must contain a non-empty module_files array")
        module_files = []
    module_docs: list[tuple[Path, dict[str, Any]]] = []
    lesson_docs: list[tuple[Path, dict[str, Any], Path]] = []
    exercise_docs: list[tuple[Path, dict[str, Any], Path]] = []
    module_seqs: list[int] = []
    lesson_seqs: list[int] = []
    exercise_paths_referenced: set[Path] = set()

    for module_rel in module_files:
        try:
            module_path = _safe_relative(
                course_dir, module_rel, course_dir, "module_files"
            )
            module_doc = _read_json(module_path)
        except ValueError as exc:
            findings.append(str(exc))
            continue
        module_docs.append((module_path, module_doc))
        claim_id(module_doc, module_path)
        sequence = module_doc.get("sequence")
        if not isinstance(sequence, int):
            findings.append(f"{module_path}: sequence must be an integer")
        else:
            module_seqs.append(sequence)
        if not isinstance(module_doc.get("slug"), str) or not isinstance(
            module_doc.get("title"), str
        ):
            findings.append(f"{module_path}: module needs slug and title")
        if module_doc.get("status") not in {"draft", "published"}:
            findings.append(f"{module_path}: status must be 'draft' or 'published'")
        visual = module_doc.get("overview_visual") or {}
        visual_path = visual.get("path") if isinstance(visual, dict) else None
        if visual_path and str(visual_path).lower().endswith((".svg", ".diagram.json")):
            try:
                model_path = _asset_or_dynamic_model(
                    course_dir, visual_path, course_dir / "assets",
                    f"{module_path.name}.overview_visual",
                )
                if model_path.name.endswith(".diagram.json"):
                    _validate_dynamic_model(model_path, f"{module_path.name}.overview_visual")
            except ValueError as exc:
                findings.append(str(exc))
        lesson_files = module_doc.get("lesson_files")
        if not isinstance(lesson_files, list) or not lesson_files:
            findings.append(f"{module_path}: lesson_files must be a non-empty array")
            continue
        module_folder = module_path.parent
        seen_module_slugs = set()
        for lesson_rel in lesson_files:
            try:
                lesson_path = _safe_relative(
                    module_folder,
                    lesson_rel,
                    course_dir,
                    f"{module_path.name}.lesson_files",
                )
                lesson_doc = _read_json(lesson_path)
            except ValueError as exc:
                findings.append(str(exc))
                continue
            lesson_docs.append((lesson_path, lesson_doc, module_path))
            claim_id(lesson_doc, lesson_path)
            lseq = lesson_doc.get("sequence")
            if isinstance(lseq, int):
                lesson_seqs.append(lseq)
            else:
                findings.append(f"{lesson_path}: sequence must be an integer")
            if lesson_doc.get("module_id") != module_doc.get("id"):
                findings.append(
                    f"{lesson_path}: module_id does not match parent module"
                )
            if lesson_doc.get("status") not in {"draft", "published"}:
                findings.append(f"{lesson_path}: status must be 'draft' or 'published'")
            for required in (
                "slug",
                "title",
                "learning_outcomes",
                "content",
                "exercise_files",
                "sources",
            ):
                if required not in lesson_doc:
                    findings.append(
                        f"{lesson_path}: missing required field '{required}'"
                    )
            outcomes = lesson_doc.get("learning_outcomes", [])
            if not isinstance(outcomes, list) or not 2 <= len(outcomes) <= 4:
                findings.append(f"{lesson_path}: expected 2-4 learning outcomes")
            content = lesson_doc.get("content") or {}
            blocks = (
                content.get("content_blocks") if isinstance(content, dict) else None
            )
            if not isinstance(blocks, list) or not any(
                b.get("type") == "diagram" for b in blocks if isinstance(b, dict)
            ):
                findings.append(f"{lesson_path}: content needs a visual/diagram block")
            if not any(
                b.get("type") == "code" for b in blocks or [] if isinstance(b, dict)
            ):
                findings.append(
                    f"{lesson_path}: content needs a runnable or inspectable code block"
                )
            for block in blocks or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "diagram":
                    asset_path = block.get("asset_path")
                    try:
                        model_path = _asset_or_dynamic_model(
                            course_dir / "assets", asset_path, course_dir / "assets",
                            f"{lesson_path.name}.diagram.asset_path",
                        )
                        if model_path.name.endswith(".diagram.json"):
                            _validate_dynamic_model(model_path, f"{lesson_path.name}.diagram")
                    except ValueError as exc:
                        findings.append(str(exc))
                if block.get("type") == "code" and (
                    not block.get("code") or not block.get("expected_output")
                ):
                    findings.append(
                        f"{lesson_path}: code block requires code and expected_output"
                    )
            qref = (
                content.get("knowledge_check_file")
                if isinstance(content, dict)
                else None
            )
            if qref:
                try:
                    qpath = _safe_relative(
                        course_dir,
                        qref,
                        course_dir,
                        f"{lesson_path.name}.knowledge_check_file",
                    )
                    qdoc = _read_json(qpath)
                    claim_id(qdoc, qpath)
                    if qdoc.get("lesson_id") != lesson_doc.get("id"):
                        findings.append(f"{qpath}: lesson_id does not match lesson")
                    if qdoc.get("status") not in {"draft", "published"}:
                        findings.append(
                            f"{qpath}: status must be 'draft' or 'published'"
                        )
                    qs = qdoc.get("questions", [])
                    if len(qs) < 3:
                        findings.append(
                            f"{qpath}: expected at least three knowledge-check questions"
                        )
                    for q in qs:
                        if not all(
                            k in q
                            for k in (
                                "id",
                                "prompt",
                                "options",
                                "answer_key",
                                "explanation",
                            )
                        ):
                            findings.append(
                                f"{qpath}: question is missing prompt/options/answer/explanation"
                            )
                        qid = q.get("id")
                        if qid in seen_ids:
                            findings.append(f"duplicate id '{qid}' in {qpath}")
                        else:
                            seen_ids[qid] = str(qpath.relative_to(course_dir))
                except ValueError as exc:
                    findings.append(str(exc))
            exercise_files = lesson_doc.get("exercise_files", [])
            if not isinstance(exercise_files, list):
                findings.append(f"{lesson_path}: exercise_files must be an array")
                continue
            for exercise_rel in exercise_files:
                try:
                    exercise_path = _safe_relative(
                        lesson_path.parent,
                        exercise_rel,
                        course_dir,
                        f"{lesson_path.name}.exercise_files",
                    )
                    exercise_doc = _read_json(exercise_path)
                except ValueError as exc:
                    findings.append(str(exc))
                    continue
                exercise_docs.append((exercise_path, exercise_doc, lesson_path))
                exercise_paths_referenced.add(exercise_path.resolve())
                claim_id(exercise_doc, exercise_path)
                if exercise_doc.get("lesson_id") != lesson_doc.get("id"):
                    findings.append(
                        f"{exercise_path}: lesson_id does not match linked lesson"
                    )
                if exercise_doc.get("status") not in {"draft", "published"}:
                    findings.append(
                        f"{exercise_path}: status must be 'draft' or 'published'"
                    )
                config = exercise_doc.get("grading_config")
                if (
                    not isinstance(config, dict)
                    or config.get("mode") not in ALLOWED_GRADING_MODES
                ):
                    findings.append(
                        f"{exercise_path}: grading_config.mode must be supported"
                    )
                elif config.get("mode") == "choice" and not config.get(
                    "correct_answer"
                ):
                    findings.append(
                        f"{exercise_path}: choice grading needs a correct_answer"
                    )
                elif (
                    config.get("mode") == "exact_text" and "expected_text" not in config
                ):
                    findings.append(
                        f"{exercise_path}: exact_text grading needs expected_text"
                    )
                elif config.get("mode") == "contains_all" and not config.get(
                    "required_strings"
                ):
                    findings.append(
                        f"{exercise_path}: contains_all grading needs required_strings"
                    )
                if not exercise_doc.get("hints") or not exercise_doc.get(
                    "acceptance_criteria"
                ):
                    findings.append(
                        f"{exercise_path}: exercise needs hints and acceptance criteria"
                    )
                # Optional repository-only answer files keep solution content separate
                # from learner-facing exercise instructions. Existing course formats
                # without solution_file remain backward compatible.
                solution_rel = exercise_doc.get("solution_file")
                if solution_rel is not None:
                    try:
                        solution_path = _safe_relative(
                            exercise_path.parent,
                            solution_rel,
                            course_dir,
                            f"{exercise_path.name}.solution_file",
                        )
                        solution_doc = _read_json(solution_path)
                        claim_id(solution_doc, solution_path)
                        if solution_doc.get("exercise_id") != exercise_doc.get("id"):
                            findings.append(
                                f"{solution_path}: exercise_id does not match linked exercise"
                            )
                        if (
                            solution_doc.get("visibility")
                            != "protected_content_repository_only"
                        ):
                            findings.append(
                                f"{solution_path}: protected solution visibility must be repository-only"
                            )
                        if solution_doc.get("status") not in {"draft", "published"}:
                            findings.append(
                                f"{solution_path}: status must be 'draft' or 'published'"
                            )
                        if not solution_doc.get("answer") or not solution_doc.get(
                            "explanation"
                        ):
                            findings.append(
                                f"{solution_path}: solution needs an answer and explanation"
                            )
                    except ValueError as exc:
                        findings.append(str(exc))

    if len(module_docs) != len(module_files):
        findings.append("One or more module files failed to load")
    if len(module_seqs) != len(set(module_seqs)):
        findings.append("Duplicate module sequence numbers")
    if module_seqs and sorted(module_seqs) != list(range(1, len(module_seqs) + 1)):
        findings.append("Module sequence numbers must be consecutive starting at 1")
    if len(lesson_seqs) != len(set(lesson_seqs)):
        findings.append("Duplicate lesson sequence numbers")
    if lesson_seqs and sorted(lesson_seqs) != list(range(1, len(lesson_seqs) + 1)):
        findings.append("Lesson sequence numbers must be consecutive starting at 1")

    # Stable identifiers and previous/next edges must point to existing lessons.
    lesson_ids = {doc.get("id") for _, doc, _ in lesson_docs}
    lesson_slugs = {doc.get("slug") for _, doc, _ in lesson_docs}
    for path, doc, _ in lesson_docs:
        for field in ("previous_lesson_id", "next_lesson_id"):
            target = doc.get(field)
            if target is not None and target not in lesson_ids:
                findings.append(f"{path}: {field} points to missing lesson ID {target}")
        for target in doc.get("prerequisites", []) or []:
            if target not in lesson_ids:
                findings.append(
                    f"{path}: prerequisite points to missing lesson ID {target}"
                )

    # Validate all referenced projects, solutions, exam files, reference index, and asset manifest.
    project_files = course_doc.get("project_files", [])
    project_docs = []
    if not isinstance(project_files, list):
        findings.append("course.json project_files must be an array")
        project_files = []
    for rel in project_files:
        try:
            path = _safe_relative(course_dir, rel, course_dir, "project_files")
            doc = _read_json(path)
            project_docs.append((path, doc))
            claim_id(doc, path)
            if doc.get("status") not in {"draft", "published"}:
                findings.append(f"{path}: status must be 'draft' or 'published'")
            rubric = doc.get("rubric", [])
            if not rubric or sum(x.get("points", 0) for x in rubric) != 100:
                findings.append(f"{path}: rubric points must total 100")
            sol = doc.get("reference_solution_file")
            if sol:
                try:
                    solution_path = _safe_relative(
                        course_dir,
                        sol,
                        course_dir,
                        f"{path.name}.reference_solution_file",
                    )
                    sol_doc = _read_json(solution_path)
                    claim_id(sol_doc, solution_path)
                except ValueError as exc:
                    findings.append(str(exc))
        except ValueError as exc:
            findings.append(str(exc))

    assessment_files = course_doc.get("assessment_files", [])
    if not isinstance(assessment_files, list):
        findings.append("course.json assessment_files must be an array")
        assessment_files = []
    for rel in assessment_files:
        try:
            path = _safe_relative(course_dir, rel, course_dir, "assessment_files")
            doc = _read_json(path)
            if path.name == "exam-blueprint.json":
                claim_id(doc, path)
                if doc.get("status") not in {"draft", "published"}:
                    findings.append(f"{path}: status must be 'draft' or 'published'")
                for qref in doc.get("question_files", []):
                    try:
                        _safe_relative(
                            path.parent,
                            qref,
                            path.parent,
                            "exam-blueprint.question_files",
                        )
                    except ValueError as exc:
                        findings.append(str(exc))
        except ValueError as exc:
            findings.append(str(exc))

    # Validate references, every asset path, and SVG XML parseability.
    ref_rel = course_doc.get("reference_index")
    if ref_rel:
        try:
            _safe_relative(course_dir, ref_rel, course_dir, "reference_index")
        except ValueError as exc:
            findings.append(str(exc))
    manifest_rel = course_doc.get("asset_manifest")
    asset_count = 0
    if manifest_rel:
        try:
            manifest_path = _safe_relative(
                course_dir, manifest_rel, course_dir, "asset_manifest"
            )
            manifest = _read_json(manifest_path)
            for asset in manifest.get("assets", []):
                rel = asset.get("path")
                try:
                    apath = _asset_or_dynamic_model(
                        course_dir, rel, course_dir / "assets", "asset-manifest.path"
                    )
                    asset_count += 1
                    # The manifest may retain a legacy .svg logical path; the actual served
                    # asset is now its .diagram.json partner and must be validated as JSON.
                    declared_suffix = Path(str(rel)).suffix.lower()
                    if declared_suffix not in ALLOWED_ASSET_SUFFIXES and not str(rel).endswith(".diagram.json"):
                        findings.append(f"{apath}: unsupported asset extension")
                    if apath.suffix.lower() == ".svg":
                        try:
                            ET.parse(apath)
                        except ET.ParseError as exc:
                            findings.append(f"{apath}: invalid SVG XML: {exc}")
                    elif apath.name.endswith(".diagram.json"):
                        try:
                            _validate_dynamic_model(apath, "asset-manifest.path")
                        except ValueError as exc:
                            findings.append(str(exc))
                    for need in (
                        "extension",
                        "format",
                        "purpose",
                        "alt_text",
                        "caption",
                        "status",
                    ):
                        if not asset.get(need):
                            findings.append(
                                f"{manifest_path}: asset {rel} missing {need}"
                            )
                except ValueError as exc:
                    findings.append(str(exc))
        except ValueError as exc:
            findings.append(str(exc))

    # Scan every JSON file for forbidden author-supplied XP settings.
    for path, doc in all_json.items():
        _walk_forbidden_xp(doc, str(path.relative_to(course_dir)), findings)

    # The per-course generated package has explicit expected counts from the reviewed syllabus.
    expected = course_doc.get("course", {})
    if expected.get("module_count") is not None and int(
        expected["module_count"]
    ) != len(module_docs):
        findings.append(
            f"course.module_count={expected['module_count']} but {len(module_docs)} modules are listed"
        )
    if expected.get("lesson_count") is not None and int(
        expected["lesson_count"]
    ) != len(lesson_docs):
        findings.append(
            f"course.lesson_count={expected['lesson_count']} but {len(lesson_docs)} lessons are linked"
        )

    if findings:
        # Keep logs usable when one class of validation failure causes many related reports.
        raise ValueError("Course validation failed:\n- " + "\n- ".join(findings))

    return {
        "course_slug": slug,
        "course_title": course_data["title"],
        "modules": len(module_docs),
        "lessons": len(lesson_docs),
        "exercises": len(exercise_docs),
        "projects": len(project_docs),
        "knowledge_check_sets": len(lesson_docs),
        "knowledge_check_questions": sum(
            len((_read_json(p).get("questions") or []))
            for p in course_dir.glob("exams/question-files/*.json")
        ),
        "assessments": 1,
        "visual_assets": asset_count,
        "json_files": len(all_json),
        "status": course_data.get("status", "draft"),
        "message": "All referenced course files, IDs, relationships, graders, asset paths, and SVG XML passed validation.",
    }
