"""Syntax-check standalone PHP examples in a CodeLeaf course tree using `php -l`.

Run from backend/: python scripts/validate_php_course_examples.py --course-slug php
This lints examples only. It does not execute code, connect to databases, or validate PHP 8.5-only behavior.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
CONTENT_ROOT = BACKEND / "content" / "courses"


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def collect_snippets(course_dir: Path) -> list[tuple[str, str]]:
    snippets: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for path in sorted(course_dir.rglob("*.json")):
        try:
            data = read_json(path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise ValueError(
                f"Cannot read {path.relative_to(course_dir)}: {exc}"
            ) from exc
        relative = path.relative_to(course_dir).as_posix()
        content = data.get("content")
        if isinstance(content, dict):
            for block in content.get("content_blocks", []) or []:
                if (
                    isinstance(block, dict)
                    and block.get("type") == "code"
                    and str(block.get("language", "")).lower()
                    in {"php", "php8", "php 8"}
                ):
                    add_snippet(snippets, seen, relative, block.get("code"))
        if isinstance(data.get("starter"), dict):
            add_snippet(snippets, seen, relative, data["starter"].get("code"))
        for starter in data.get("starter_files", []) or []:
            if (
                isinstance(starter, dict)
                and str(starter.get("language", "")).lower() == "php"
            ):
                add_snippet(snippets, seen, relative, starter.get("contents"))
        # Protected exercise/project reference code is linted too, without being printed.
        answer = data.get("answer")
        if data.get("visibility") == "protected_content_repository_only":
            if isinstance(answer, str):
                add_snippet(snippets, seen, relative, answer)
            elif isinstance(answer, dict):
                add_snippet(snippets, seen, relative, answer.get("code"))
    return snippets


def collect_lesson_examples(course_dir: Path) -> list[tuple[str, str, str]]:
    """Return trusted, course-authored lesson snippets and expected output for optional local tests."""
    examples: list[tuple[str, str, str]] = []
    for path in sorted(course_dir.rglob("*.json")):
        try:
            data = read_json(path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise ValueError(
                f"Cannot read {path.relative_to(course_dir)}: {exc}"
            ) from exc
        content = data.get("content")
        if not isinstance(content, dict):
            continue
        for block in content.get("content_blocks", []) or []:
            if (
                isinstance(block, dict)
                and block.get("type") == "code"
                and str(block.get("language", "")).lower() in {"php", "php8", "php 8"}
                and isinstance(block.get("code"), str)
                and isinstance(block.get("expected_output"), str)
            ):
                examples.append(
                    (
                        path.relative_to(course_dir).as_posix(),
                        block["code"],
                        block["expected_output"],
                    )
                )
    return examples


def validate_question_alignment(course_dir: Path) -> dict[str, Any]:
    """Check that each lesson's output-tracing question matches its code block."""
    checked = 0
    errors: list[dict[str, str]] = []
    root = course_dir.resolve()
    for lesson_path in sorted(root.rglob("*.json")):
        try:
            lesson = read_json(lesson_path)
        except (OSError, json.JSONDecodeError, ValueError):
            continue
        content = lesson.get("content")
        if not isinstance(content, dict) or not content.get("knowledge_check_file"):
            continue
        code = next(
            (
                block
                for block in content.get("content_blocks", []) or []
                if isinstance(block, dict)
                and block.get("type") == "code"
                and str(block.get("language", "")).lower() == "php"
            ),
            None,
        )
        if not code:
            errors.append(
                {
                    "source": lesson_path.relative_to(root).as_posix(),
                    "message": "No PHP code block found for its knowledge check.",
                }
            )
            continue
        relative = content["knowledge_check_file"]
        quiz_path = (root / str(relative)).resolve()
        if root not in quiz_path.parents or not quiz_path.is_file():
            errors.append(
                {
                    "source": lesson_path.relative_to(root).as_posix(),
                    "message": "Knowledge-check path is missing or unsafe.",
                }
            )
            continue
        try:
            quiz = read_json(quiz_path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(
                {"source": quiz_path.relative_to(root).as_posix(), "message": str(exc)}
            )
            continue
        questions = quiz.get("questions", [])
        if len(questions) < 2 or not isinstance(questions[1], dict):
            errors.append(
                {
                    "source": quiz_path.relative_to(root).as_posix(),
                    "message": "Expected an output-tracing question at index 2.",
                }
            )
            continue
        question = questions[1]
        expected = str(code.get("expected_output", "")).rstrip("\r\n")
        options = question.get("options", [])
        if question.get("answer_key") != expected:
            errors.append(
                {
                    "source": quiz_path.relative_to(root).as_posix(),
                    "message": "Output question answer key does not match the lesson's expected output.",
                }
            )
        if (
            not isinstance(options, list)
            or len(options) != 4
            or len(set(options)) != 4
            or options.count(expected) != 1
        ):
            errors.append(
                {
                    "source": quiz_path.relative_to(root).as_posix(),
                    "message": "Output question must contain four distinct options with exactly one matching expected output.",
                }
            )
        checked += 1
    return {
        "lesson_questions_checked": checked,
        "errors": errors,
        "status": "passed" if not errors else "failed",
    }


def add_snippet(
    target: list[tuple[str, str]], seen: set[tuple[str, str]], source: str, code: Any
) -> None:
    if not isinstance(code, str) or not code.strip() or "<?php" not in code:
        return
    marker = (source, code)
    if marker not in seen:
        seen.add(marker)
        target.append(marker)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--course-slug", required=True, help="Course folder name, e.g. php"
    )
    parser.add_argument(
        "--execute-lessons",
        action="store_true",
        help="Execute trusted repository-authored lesson snippets in temporary directories and compare expected output; never use this with learner-supplied content.",
    )
    args = parser.parse_args()
    if not args.course_slug or any(
        ch not in "abcdefghijklmnopqrstuvwxyz0123456789-" for ch in args.course_slug
    ):
        parser.error(
            "course slug must contain lowercase letters, digits, and hyphens only"
        )
    course_dir = (CONTENT_ROOT / args.course_slug).resolve()
    if CONTENT_ROOT.resolve() not in course_dir.parents or not course_dir.is_dir():
        parser.error("Course folder was not found below backend/content/courses")
    php = shutil.which("php")
    if not php:
        print(
            "ERROR: PHP CLI was not found; install PHP and put php on PATH.",
            file=sys.stderr,
        )
        return 2
    version_result = subprocess.run(
        [php, "-v"], capture_output=True, text=True, check=False
    )
    version_line = (
        (version_result.stdout or version_result.stderr).splitlines()[0]
        if (version_result.stdout or version_result.stderr)
        else "PHP version unknown"
    )
    snippets = collect_snippets(course_dir)
    question_alignment = validate_question_alignment(course_dir)
    errors: list[dict[str, str]] = []
    with tempfile.TemporaryDirectory(prefix="codeleaf-php-lint-") as temporary:
        temp_dir = Path(temporary)
        for index, (source, code) in enumerate(snippets, start=1):
            sample = temp_dir / f"snippet-{index:04d}.php"
            sample.write_text(code, encoding="utf-8")
            result = subprocess.run(
                [php, "-l", str(sample)], capture_output=True, text=True, check=False
            )
            if result.returncode:
                errors.append(
                    {
                        "source": source,
                        "message": (result.stdout + result.stderr).strip(),
                    }
                )

    execution_report: dict[str, Any] = {
        "requested": bool(args.execute_lessons),
        "checked": 0,
        "mismatches": [],
    }
    if args.execute_lessons and not errors:
        # The allowlisted environment avoids accidentally passing database/API secrets to examples.
        lesson_examples = collect_lesson_examples(course_dir)
        with tempfile.TemporaryDirectory(prefix="codeleaf-php-run-") as temporary:
            run_dir = Path(temporary)
            safe_env = {
                "PATH": os.environ.get("PATH", ""),
                "HOME": temporary,
                "TMPDIR": temporary,
                "TEMP": temporary,
                "TMP": temporary,
            }
            for index, (source, code, expected) in enumerate(lesson_examples, start=1):
                sample_dir = run_dir / f"lesson-{index:04d}"
                sample_dir.mkdir()
                sample = sample_dir / "example.php"
                sample.write_text(code, encoding="utf-8")
                try:
                    result = subprocess.run(
                        [php, str(sample)],
                        capture_output=True,
                        text=True,
                        check=False,
                        cwd=sample_dir,
                        env=safe_env,
                        timeout=3,
                    )
                    actual = result.stdout.rstrip("\r\n")
                    expected_normalized = expected.rstrip("\r\n")
                    if (
                        result.returncode
                        or actual != expected_normalized
                        or result.stderr.strip()
                    ):
                        execution_report["mismatches"].append(
                            {
                                "source": source,
                                "return_code": result.returncode,
                                "actual_output": actual[:1000],
                                "expected_output": expected_normalized[:1000],
                                "stderr": result.stderr[:1000],
                            }
                        )
                except subprocess.TimeoutExpired:
                    execution_report["mismatches"].append(
                        {"source": source, "message": "Timed out after 3 seconds"}
                    )
        execution_report["checked"] = len(lesson_examples)
    execution_report["status"] = (
        ("passed" if not execution_report["mismatches"] else "failed")
        if args.execute_lessons
        else "not-run"
    )
    print(
        json.dumps(
            {
                "course_slug": args.course_slug,
                "php_cli": php,
                "runtime": version_line,
                "snippets_checked": len(snippets),
                "syntax_errors": len(errors),
                "errors": errors[:50],
                "knowledge_check_output_alignment": question_alignment,
                "lesson_execution": execution_report,
                "status": (
                    "failed"
                    if errors
                    or question_alignment["status"] == "failed"
                    or execution_report["status"] == "failed"
                    else "passed"
                ),
                "limitations": [
                    "PHP -l checks syntax only; it does not execute examples or verify runtime behavior.",
                    "Optional --execute-lessons mode runs trusted course-authored lesson code only, in temporary directories with a restricted environment; never use it for learner-supplied code.",
                    "This course targets PHP 8.5.x. A different local PHP minor version does not establish PHP 8.5 compatibility.",
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
