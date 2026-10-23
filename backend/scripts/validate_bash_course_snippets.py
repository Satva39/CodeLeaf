"""Syntax-check Bash examples and starter scripts without executing them.

Run from backend/: python scripts/validate_bash_course_snippets.py
Requires a runnable GNU Bash. On Windows, Git Bash is detected in common install
locations; set BASH_EXE to an explicit executable path to override discovery.
Lesson 139 is parsed with extglob enabled because that syntax requires the option.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
COURSE = BACKEND / "content" / "courses" / "bash"


def bash_candidates() -> list[str]:
    """Return likely Bash executables, preferring an explicit BASH_EXE setting."""
    candidates: list[str] = []

    def add(value: str | os.PathLike[str] | None) -> None:
        if not value:
            return
        candidate = str(value).strip().strip('"')
        if candidate and candidate not in candidates:
            candidates.append(candidate)

    add(os.environ.get("BASH_EXE"))

    # PowerShell may resolve `bash` to the Windows WSL relay even when no Linux
    # distribution is installed. Try common Git for Windows locations as well.
    if os.name == "nt":
        roots = [
            os.environ.get("ProgramFiles"),
            os.environ.get("ProgramFiles(x86)"),
            (
                str(Path(os.environ.get("LOCALAPPDATA", "")) / "Programs")
                if os.environ.get("LOCALAPPDATA")
                else None
            ),
        ]
        for root in roots:
            if root:
                add(Path(root) / "Git" / "bin" / "bash.exe")
                add(Path(root) / "Git" / "usr" / "bin" / "bash.exe")

    add(shutil.which("bash"))
    return candidates


def find_runnable_bash() -> tuple[str | None, list[str]]:
    """Probe Bash once so a missing WSL distro is not reported as syntax errors."""
    diagnostics: list[str] = []
    candidates = bash_candidates()
    if not candidates:
        return None, ["No Bash executable was found on PATH or in known locations."]

    for candidate in candidates:
        try:
            result = subprocess.run(
                [candidate, "--version"],
                text=True,
                capture_output=True,
                check=False,
                timeout=5,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            diagnostics.append(f"{candidate}: {exc}")
            continue

        version_text = f"{result.stdout}\n{result.stderr}".lower()
        if result.returncode == 0 and "bash" in version_text:
            return candidate, diagnostics

        detail = (
            result.stderr or result.stdout or f"exit code {result.returncode}"
        ).strip()
        diagnostics.append(f"{candidate}: {detail}")

    return None, diagnostics


def syntax_check(
    bash_exe: str, label: str, code: str, *, extglob: bool = False
) -> tuple[str, str] | None:
    """Return a syntax failure tuple, or None on success; never execute code."""
    command = [bash_exe]
    if extglob:
        command.extend(["-O", "extglob"])
    command.append("-n")
    try:
        # Use stdin rather than a temporary file: this avoids Windows-path
        # translation issues with Git Bash while still performing parse-only checks.
        result = subprocess.run(
            command,
            input=code.rstrip() + "\n",
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return label, "Bash syntax check timed out after 10 seconds"
    except OSError as exc:
        # This should be rare after preflight, but distinguish infrastructure
        # failure from a Bash parser rejection.
        return label, f"Bash could not be started: {exc}"

    if result.returncode:
        return label, (result.stderr.strip() or f"bash -n exited {result.returncode}")
    return None


def main() -> int:
    if not COURSE.is_dir():
        print(f"Course directory not found: {COURSE}", file=sys.stderr)
        return 2

    bash_exe, diagnostics = find_runnable_bash()
    if bash_exe is None:
        print(
            "Bash syntax validation was NOT RUN: no runnable Bash interpreter could be started.",
            file=sys.stderr,
        )
        for diagnostic in diagnostics:
            print(f"  - {diagnostic}", file=sys.stderr)
        print(
            "No snippets were classified as syntax failures. Install Git for Windows (Git Bash) "
            "or a WSL Linux distribution, then rerun. On Windows, you may set BASH_EXE to "
            r'"C:\Program Files\Git\bin\bash.exe".',
            file=sys.stderr,
        )
        return 2

    checked = 0
    failures: list[tuple[str, str]] = []

    for path in sorted(COURSE.glob("modules/*/lessons/*.json")):
        try:
            lesson = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            failures.append((str(path.relative_to(BACKEND)), f"invalid JSON: {exc}"))
            continue
        for block in lesson.get("content", {}).get("content_blocks", []):
            if (
                block.get("type") != "code"
                or block.get("language", "").lower() != "bash"
            ):
                continue
            checked += 1
            fail = syntax_check(
                bash_exe,
                f"lesson {lesson.get('sequence')}: {lesson.get('title')}",
                block.get("code", ""),
                extglob=lesson.get("sequence") == 139,
            )
            if fail:
                failures.append(fail)

    for path in sorted(COURSE.glob("modules/*/exercises/solutions/*.json")):
        try:
            solution = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            failures.append((str(path.relative_to(BACKEND)), f"invalid JSON: {exc}"))
            continue
        answer = solution.get("answer", {})
        if answer.get("language", "").lower() == "bash" and answer.get("code"):
            checked += 1
            fail = syntax_check(
                bash_exe,
                f"exercise solution {solution.get('exercise_id', path.stem)}",
                answer["code"],
            )
            if fail:
                failures.append(fail)

    for path in sorted(COURSE.glob("projects/*.json")):
        try:
            project = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            failures.append((str(path.relative_to(BACKEND)), f"invalid JSON: {exc}"))
            continue
        for starter in project.get("starter_files", []):
            if starter.get("language", "").lower() == "bash":
                checked += 1
                fail = syntax_check(
                    bash_exe,
                    f"project {project.get('sequence')}: {starter.get('path', 'starter')}",
                    starter.get("contents", ""),
                )
                if fail:
                    failures.append(fail)

    print(f"Bash executable: {bash_exe}")
    print(f"Bash snippets/scripts checked: {checked}")
    print(f"Syntax failures: {len(failures)}")
    for label, error in failures:
        print(f"FAIL: {label}\n  {error}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
