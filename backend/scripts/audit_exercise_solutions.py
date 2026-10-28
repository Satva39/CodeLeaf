"""Audit published exercise manifests for usable worked-solution sources.

This is a structural audit: it verifies solution references and learner-facing answer fields;
subject-matter correctness still requires course-specific review and executable tests.
"""
from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "content" / "courses"


def main() -> int:
    courses = 0
    exercise_count = 0
    linked_count = 0
    inline_count = 0
    missing = []
    malformed = []
    weak = []
    by_course = {}

    for course_dir in sorted(path for path in ROOT.iterdir() if path.is_dir()):
        courses += 1
        course_stats = Counter()
        for directory, _, files in os.walk(course_dir):
            if Path(directory).name != "exercises" or "solutions" in Path(directory).parts:
                continue
            for filename in files:
                if not filename.endswith(".json"):
                    continue
                manifest_path = Path(directory) / filename
                try:
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                    malformed.append(str(manifest_path.relative_to(ROOT)))
                    continue
                if not isinstance(manifest, dict):
                    malformed.append(str(manifest_path.relative_to(ROOT)))
                    continue
                exercise_count += 1
                course_stats["exercises"] += 1
                solution_doc = None
                solution_rel = manifest.get("solution_file")
                if isinstance(solution_rel, str) and solution_rel.strip():
                    solution_path = (manifest_path.parent / solution_rel).resolve()
                    try:
                        solution_path.relative_to(course_dir.resolve())
                    except ValueError:
                        solution_path = None
                    if solution_path and solution_path.is_file():
                        try:
                            solution_doc = json.loads(solution_path.read_text(encoding="utf-8"))
                        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                            malformed.append(str(solution_path))
                    else:
                        missing.append(str(manifest_path.relative_to(ROOT)))
                if isinstance(solution_doc, dict):
                    linked_count += 1
                    course_stats["linked_solution_files"] += 1
                    has_answer = bool(solution_doc.get("answer") or solution_doc.get("reference_code") or solution_doc.get("example_code") or solution_doc.get("solution_code"))
                    has_explanation = bool(solution_doc.get("explanation") or solution_doc.get("steps") or solution_doc.get("expected_result") or solution_doc.get("expected_output"))
                    answer_text = json.dumps(solution_doc.get("answer", ""), ensure_ascii=False).lower()
                    placeholder_markers = (
                        "reference approach:",
                        "a strong solution should",
                        "implement ",
                        "protected reference solution is stored",
                        "required implementation evidence includes",
                        "this exercise checks",
                    )
                    if not (has_answer and has_explanation) or any(marker in answer_text for marker in placeholder_markers):
                        weak.append(str(manifest_path.relative_to(ROOT)))
                else:
                    inline = manifest.get("solution")
                    if isinstance(inline, dict) and any(inline.get(key) for key in ("answer", "explanation", "expected_result", "steps")):
                        inline_count += 1
                        course_stats["inline_solutions"] += 1
                    else:
                        missing.append(str(manifest_path.relative_to(ROOT)))
        by_course[course_dir.name] = dict(course_stats)

    report = {
        "courses": courses,
        "exercise_count": exercise_count,
        "linked_solution_files": linked_count,
        "inline_solution_sources": inline_count,
        "missing_solution_sources": len(missing),
        "malformed_json_files": len(malformed),
        "needs_content_review": len(weak),
        "missing_examples": missing[:500],
        "malformed_files": malformed[:500],
        "needs_content_review_examples": weak[:500],
        "by_course": by_course,
        "note": "Structural availability is not proof that every answer is technically correct or sufficiently detailed; review flagged entries and test runnable code in supported isolated environments.",
    }
    out = ROOT.parents[1] / "docs" / "exercise-solution-audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("courses", "exercise_count", "linked_solution_files", "inline_solution_sources", "missing_solution_sources", "malformed_json_files", "needs_content_review")}, indent=2))
    print(f"Report: {out}")
    return 1 if missing or malformed else 0


if __name__ == "__main__":
    raise SystemExit(main())
