"""Policy regression checks for the allowed Practice task types.

Run from backend/: python scripts/test_practice_exercise_policy.py
This check uses only local JSON fixtures and does not connect to a database.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.practice_policy import practice_exercise_kind, public_practice_type


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS {message}")


def main() -> None:
    check(practice_exercise_kind("choice", {"options": ["A", "B"]}, "html") == "mcq", "MCQ remains available")
    check(practice_exercise_kind("multiple_choice", {"options": ["A", "B"]}, "python") == "mcq", "multiple_choice alias remains available")
    check(practice_exercise_kind("coding", {"language": "java", "code": "class Main {}"}, "java") == "code_challenge", "code tasks are exposed as code challenges")
    check(practice_exercise_kind("short_answer", {"response_template": "Answer:"}, "ai", "Explain the concept.") is None, "ordinary short-answer tasks are hidden")
    check(practice_exercise_kind("practical", {"context": "Review a privacy scenario", "use": "Write a report", "submission_sections": ["Risk"]}, "cybersecurity") is None, "written practical reports are not shown as code challenges")
    check(practice_exercise_kind("workbook_practice", {"headers": ["name"], "rows": [["Ada"]]}, "excel") == "code_challenge", "structured workbook challenges remain available")

    check(practice_exercise_kind("short_answer", {"language": "r", "source_code": "x <- c(1,2)", "mode": "static-validation"}, "r", "Write an R function.") == "code_challenge", "legacy R code challenges are recognized")
    check(practice_exercise_kind("short_answer", {"language": "bash", "starter": "#!/usr/bin/env bash\necho hello\n"}, "bash", "Build a script.") == "code_challenge", "legacy Bash script challenges are recognized")
    check(practice_exercise_kind("short_answer", {}, "dart", "Implement a shopping list in Dart.") == "code_challenge", "legacy Dart implementation tasks are recognized")
    check(practice_exercise_kind("short_answer", {}, "lua", "Write a deep-copy function for nested tables.") == "code_challenge", "legacy Lua implementation tasks are recognized")
    check(practice_exercise_kind("short_answer", {"language": "Solidity / local EVM test notes", "starter": "// scaffold"}, "solidity", "Build a local Solidity contract.") == "code_challenge", "legacy Solidity implementation tasks are recognized")

    repo_root = Path(__file__).resolve().parents[1]
    course_root = repo_root / "content" / "courses"
    hidden = []
    visible_short = []
    ai_items = []
    for path in course_root.glob("*/modules/*/exercises/*.json"):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise AssertionError(f"Invalid exercise JSON: {path}: {exc}") from exc
        course_slug = path.parts[-5]
        exercise_type = item.get("type", "short_answer")
        normalized = re.sub(r"[-\s]+", "_", str(exercise_type).strip().lower())
        kind = practice_exercise_kind(exercise_type, item.get("starter"), course_slug, item.get("prompt"))
        if normalized == "short_answer":
            if kind is None:
                hidden.append((course_slug, item.get("slug")))
            else:
                visible_short.append((course_slug, item.get("slug")))
        if course_slug == "ai":
            ai_items.append((item.get("slug"), kind))

    check(not visible_short, "source content no longer labels visible tasks short_answer")
    visible_ai = [(slug, kind) for slug, kind in ai_items if kind is not None]
    check(len(visible_ai) == 12, "AI Practice exposes only eligible MCQ/code-challenge tasks")
    check(sum(kind == "mcq" for _slug, kind in visible_ai) == 1, "AI practice keeps its MCQ")
    check(sum(kind == "code_challenge" for _slug, kind in visible_ai) == 11, "AI practice keeps its course-specific code challenges")
    print(f"Hidden non-code short-answer/report tasks: {len(hidden)}")


if __name__ == "__main__":
    main()
