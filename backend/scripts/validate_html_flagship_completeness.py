"""Read-only completeness checks for the HTML flagship curriculum.

Run from backend/: python scripts/validate_html_flagship_completeness.py
This validates the local structured source files and does not publish course content.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
from app.diagram_assets import resolve_dynamic_diagram, validate_dynamic_diagram_model  # noqa: E402

COURSE_DIR = BACKEND_ROOT / "content" / "courses" / "html"
SUPPORTED_GRADERS = {"choice", "exact_text", "contains_all"}


def require(ok: bool, message: str, errors: list[str]) -> None:
    if ok:
        print(f"PASS {message}")
    else:
        errors.append(message)
        print(f"FAIL {message}")


def read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def main() -> int:
    errors: list[str] = []
    manifest = read_json(COURSE_DIR / "course.json")
    require(manifest.get("status") == "draft", "HTML course remains draft pending review", errors)
    modules = []
    lessons = []
    exercises = []
    seen_module_slugs: set[str] = set()
    seen_lesson_slugs: set[str] = set()
    lesson_diagram_models: dict[str, Path] = {}
    content_block_counts: Counter[str] = Counter()
    code_example_counts: Counter[str] = Counter()
    for module_rel in manifest.get("module_files", []):
        module_path = (COURSE_DIR / module_rel).resolve()
        require(COURSE_DIR.resolve() in module_path.parents and module_path.is_file(), f"module file resolves: {module_rel}", errors)
        if not module_path.is_file():
            continue
        module = read_json(module_path)
        modules.append(module)
        require(module.get("slug") not in seen_module_slugs, f"unique module slug: {module.get('slug')}", errors)
        seen_module_slugs.add(module.get("slug"))
        for lesson_rel in module.get("lesson_files", []):
            lesson_path = (module_path.parent / lesson_rel).resolve()
            require(COURSE_DIR.resolve() in lesson_path.parents and lesson_path.is_file(), f"lesson file resolves: {lesson_rel}", errors)
            if not lesson_path.is_file():
                continue
            lesson = read_json(lesson_path)
            lessons.append((lesson_path, lesson))
            slug = lesson.get("slug")
            require(isinstance(slug, str) and slug not in seen_lesson_slugs, f"unique lesson slug: {slug}", errors)
            seen_lesson_slugs.add(slug)
            doc = lesson.get("content") or {}
            blocks = doc.get("content_blocks", []) if isinstance(doc, dict) else []
            content_doc = doc if isinstance(doc, dict) else {}
            for required_field in ("intro", "why_it_matters", "task", "task_acceptance_criteria", "hints", "expected_output", "troubleshooting", "common_mistakes", "summary"):
                require(bool(content_doc.get(required_field)), f"lesson has {required_field}: {slug}", errors)
            require(bool(lesson.get("learning_outcomes")), f"lesson has learning outcomes: {slug}", errors)
            sources = lesson.get("sources") or content_doc.get("references") or []
            valid_sources = 0
            for source in sources if isinstance(sources, list) else []:
                if not isinstance(source, dict):
                    continue
                parsed_source = urlsplit(str(source.get("url") or ""))
                if parsed_source.scheme in {"http", "https"} and parsed_source.netloc:
                    valid_sources += 1
            require(valid_sources > 0, f"lesson has at least one HTTP(S) source: {slug}", errors)
            for block in blocks:
                block_type = str(block.get("type") or "unknown")
                content_block_counts[block_type] += 1
                if block_type == "code" and isinstance(block.get("code"), str) and block.get("code").strip():
                    code_example_counts[block["code"].strip()] += 1
                if block_type == "diagram":
                    asset_path = block.get("asset_path")
                    try:
                        model_path = resolve_dynamic_diagram(COURSE_DIR, asset_path, lesson_path.name)
                        model = validate_dynamic_diagram_model(model_path, lesson_path.name)
                        key = model_path
                        require(key not in lesson_diagram_models, f"lesson diagram is unique: {slug}", errors)
                        lesson_diagram_models[key] = lesson_path
                        require(bool(str(block.get("alt_text") or "").strip()), f"diagram has alt text: {slug}", errors)
                        require(model.get("text_mapping_complete") is True, f"diagram preserves source text mapping: {slug}", errors)
                    except (ValueError, TypeError) as exc:
                        errors.append(f"diagram failed for {slug}: {exc}")
                        print(f"FAIL diagram model resolves and validates: {slug}: {exc}")
            for exercise_rel in lesson.get("exercise_files", []):
                exercise_path = (lesson_path.parent / exercise_rel).resolve()
                require(COURSE_DIR.resolve() in exercise_path.parents and exercise_path.is_file(), f"exercise file resolves: {exercise_rel}", errors)
                if not exercise_path.is_file():
                    continue
                exercise = read_json(exercise_path)
                exercises.append((exercise_path, exercise))
                config = exercise.get("grading_config") or {}
                mode = config.get("mode") if isinstance(config, dict) else None
                require(mode in SUPPORTED_GRADERS, f"exercise has supported server grader: {exercise.get('slug')} ({mode})", errors)

    # Question bank contains private keys on disk; this validator checks but never prints them.
    question_files = manifest.get("assessment_files", [])
    blueprint_path = COURSE_DIR / "exams" / "exam-blueprint.json"
    blueprint = read_json(blueprint_path)
    all_question_ids: set[str] = set()
    question_total = 0
    question_file_count = 0
    for relative in blueprint.get("question_files", []):
        path = (COURSE_DIR / "exams" / relative).resolve()
        require(COURSE_DIR.resolve() in path.parents and path.is_file(), f"exam question file resolves: {relative}", errors)
        if not path.is_file():
            continue
        question_file_count += 1
        question_set = read_json(path)
        require(question_set.get("status") == "draft", f"question set remains draft: {path.name}", errors)
        for question in question_set.get("questions", []):
            question_total += 1
            qid = question.get("id")
            options = question.get("options")
            answer_key = question.get("answer_key")
            require(isinstance(qid, str) and qid not in all_question_ids, f"unique question ID: {qid}", errors)
            all_question_ids.add(qid)
            require(isinstance(options, list) and len(options) >= 2 and answer_key in options, f"answer key is one of its options: {qid}", errors)
    require(blueprint.get("status") == "draft", "final exam blueprint remains draft", errors)

    ref_index_path = (COURSE_DIR / (manifest.get("reference_index") or "references/reference-index.json")).resolve()
    require(COURSE_DIR.resolve() in ref_index_path.parents and ref_index_path.is_file(), "reference index exists inside course root", errors)
    ref_count = 0
    if ref_index_path.is_file():
        ref_index = read_json(ref_index_path)
        for relative in ref_index.get("references", []):
            path = (COURSE_DIR / relative).resolve()
            require(COURSE_DIR.resolve() in path.parents and path.is_file(), f"reference entry resolves: {relative}", errors)
            if not path.is_file():
                continue
            entry = read_json(path)
            parsed = urlsplit(str(entry.get("url") or ""))
            require(parsed.scheme in {"http", "https"} and bool(parsed.netloc), f"reference has an official HTTP(S) source: {entry.get('slug')}", errors)
            require(bool(entry.get("explanation")) and bool(entry.get("example")), f"reference has explanation and example: {entry.get('slug')}", errors)
            ref_count += 1

    project_count = 0
    for relative in manifest.get("project_files", []):
        path = (COURSE_DIR / relative).resolve()
        require(COURSE_DIR.resolve() in path.parents and path.is_file(), f"project file resolves: {relative}", errors)
        if path.is_file():
            project = read_json(path)
            project_count += 1
            require(project.get("status") == "draft", f"project remains draft: {project.get('slug')}", errors)

    asset_manifest_path = COURSE_DIR / "assets" / "asset-manifest.json"
    asset_manifest = read_json(asset_manifest_path)
    manifest_items = asset_manifest.get("assets", [])
    listed = {item.get("path") for item in manifest_items if isinstance(item, dict)}
    for model_rel in sorted({f"diagrams/{path.relative_to(COURSE_DIR / 'assets' / 'diagrams').as_posix()}" for path in lesson_diagram_models}):
        logical_svg = model_rel.replace(".diagram.json", ".svg")
        require(logical_svg in listed or f"assets/{logical_svg}" in listed or model_rel in listed or f"assets/{model_rel}" in listed, f"diagram has asset-manifest entry: {logical_svg}", errors)

    # The supplied HTML curriculum PDF is required for page-by-page coverage, but no PDF was uploaded.
    pdf_candidates = list(COURSE_DIR.glob("*.pdf")) + list(BACKEND_ROOT.parent.glob("HTML*.pdf"))
    if not pdf_candidates:
        print("WARN HTML curriculum PDF is absent; page-by-page PDF-to-file traceability cannot be confirmed.")

    print("\nHTML Flagship Source Audit")
    print(f"Course status: {manifest.get('status')} (must remain draft until review)")
    print(f"Modules: {len(modules)} | Lessons: {len(lessons)} | Exercises: {len(exercises)} | Projects: {project_count}")
    print(f"Exam question files: {question_file_count} | Questions: {question_total} | Reference entries: {ref_count}")
    print(f"Unique lesson diagrams: {len(lesson_diagram_models)} | Content blocks: {dict(sorted(content_block_counts.items()))}")
    print(f"Distinct authored code examples: {len(code_example_counts)} across {sum(code_example_counts.values())} code blocks")
    if code_example_counts:
        most_reused_example_count = max(code_example_counts.values())
        if len(code_example_counts) < len(lessons) or most_reused_example_count > 1:
            print(f"WARN editorial review needed: {sum(code_example_counts.values()) - len(code_example_counts)} code blocks repeat examples used elsewhere; a single example appears up to {most_reused_example_count} times.")
    print(f"Validation errors: {len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
