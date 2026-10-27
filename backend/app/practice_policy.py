"""Shared policy for learner-facing Practice tasks.

Practice supports only multiple-choice questions and course-specific coding challenges.
A small compatibility path converts older, mislabelled language-code exercises into
coding challenges when their stored starter clearly identifies the matching language.
"""
from __future__ import annotations

import re
from typing import Any

MCQ_EXERCISE_TYPES = frozenset({"choice", "multiple_choice", "mcq"})
CODE_CHALLENGE_TYPES = frozenset(
    {"coding", "code", "code_challenge", "implementation", "practical", "workbook_practice"}
)
SUPPORTED_PRACTICE_TYPES = MCQ_EXERCISE_TYPES | CODE_CHALLENGE_TYPES


def normalize_exercise_type(value: Any) -> str:
    return re.sub(r"[-\s]+", "_", str(value or "").strip().lower())


def _starter_code_text(starter: Any) -> str:
    if not isinstance(starter, dict):
        return ""
    for key in ("source_code", "code", "starter", "content", "template"):
        value = starter.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _is_legacy_language_challenge(
    course_slug: str, starter: Any, prompt: str | None
) -> bool:
    """Recognize clearly code-oriented legacy tasks whose type was saved as short_answer."""
    if not isinstance(starter, dict):
        starter = {}

    course = str(course_slug or "").strip().lower().replace("_", "-")
    language = str(starter.get("language") or "").strip().lower()
    source = _starter_code_text(starter)
    prompt_text = str(prompt or "").strip()

    # R tasks contain actual R source code; all 40 legacy rows follow this schema.
    if course == "r" and language in {"r", "r language"}:
        return bool(starter.get("source_code") and source)

    # Bash tasks contain a real executable-script scaffold, not a free-text response.
    if course == "bash" and language in {"bash", "shell"}:
        return source.startswith("#!/usr/bin/env bash")

    # These Dart records are implementation prompts stored without starter files.
    if course == "dart":
        return bool(prompt_text and re.search(r"\bDart\b", prompt_text, re.IGNORECASE)
                    and re.search(r"\b(implement|write|create|build|refactor|test|benchmark)\b", prompt_text, re.IGNORECASE))

    # The current Lua course's legacy short_answer rows are implementation exercises.
    if course == "lua":
        return bool(prompt_text and re.search(
            r"\b(implement|write|create|build|sort|count|print|compare|refactor|benchmark|analy[sz]e|design)\b",
            prompt_text,
            re.IGNORECASE,
        ))

    # Solidity task scaffolds explicitly identify the Solidity/local-EVM environment.
    if course == "solidity" and "solidity" in language:
        return bool(prompt_text)

    return False


def practice_exercise_kind(
    exercise_type: Any,
    starter: Any = None,
    course_slug: str = "",
    prompt: str | None = None,
) -> str | None:
    """Return ``mcq``, ``code_challenge``, or None for items not allowed in Practice."""
    normalized = normalize_exercise_type(exercise_type)
    if normalized in MCQ_EXERCISE_TYPES:
        return "mcq"

    if normalized in CODE_CHALLENGE_TYPES:
        # A generic written-review task must not masquerade as a code challenge. Keep
        # practical tasks only when they provide a code/data workspace scaffold.
        if normalized == "practical":
            if not isinstance(starter, dict) or not any(
                isinstance(starter.get(key), (str, list)) and starter.get(key)
                for key in ("code", "source_code", "starter", "content", "template", "headers", "rows")
            ):
                return None
        return "code_challenge"

    if normalized == "short_answer" and _is_legacy_language_challenge(course_slug, starter, prompt):
        return "code_challenge"

    return None


def is_supported_practice_exercise(
    exercise_type: Any,
    starter: Any = None,
    course_slug: str = "",
    prompt: str | None = None,
) -> bool:
    return practice_exercise_kind(exercise_type, starter, course_slug, prompt) is not None


def public_practice_type(
    exercise_type: Any,
    starter: Any = None,
    course_slug: str = "",
    prompt: str | None = None,
) -> str | None:
    kind = practice_exercise_kind(exercise_type, starter, course_slug, prompt)
    if kind == "mcq":
        return "choice"
    if kind == "code_challenge":
        return "coding"
    return None
