"""Compile-check authored C++ lesson examples and project starters without execution.

Run from backend/: python scripts/validate_cpp_course_examples.py [--compiler g++]
This is a static syntax/type check for reviewed course files, not a sandbox or
an execution service for learner-submitted code.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
COURSE_DIR = BACKEND_DIR / "content" / "courses" / "cpp"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--compiler", default="g++", help="Compiler executable (default: g++)"
    )
    parser.add_argument(
        "--limit", type=int, default=0, help="Check only the first N examples (0 = all)"
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=min(6, os.cpu_count() or 2),
        help="Parallel compiler processes (default: up to 6)",
    )
    args = parser.parse_args()

    compiler = shutil.which(args.compiler)
    if compiler is None:
        print(
            f"ERROR: compiler {args.compiler!r} was not found on PATH.", file=sys.stderr
        )
        print("Install GCC/G++ or Clang, then rerun this command.", file=sys.stderr)
        return 2
    if not COURSE_DIR.is_dir():
        print(f"ERROR: course directory not found: {COURSE_DIR}", file=sys.stderr)
        return 2
    if args.limit < 0:
        parser.error("--limit must be zero (all examples) or a positive integer")
    if args.jobs < 1 or args.jobs > 32:
        parser.error("--jobs must be between 1 and 32")

    examples: list[tuple[Path, str, str]] = []
    lesson_example_count = 0
    project_starter_count = 0
    for lesson_path in sorted(COURSE_DIR.glob("modules/*/lessons/*.json")):
        try:
            lesson = json.loads(lesson_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(
                f"ERROR: cannot parse {lesson_path.relative_to(COURSE_DIR)}: {exc}",
                file=sys.stderr,
            )
            return 2
        for block in lesson.get("content", {}).get("content_blocks", []):
            if block.get("type") != "code" or block.get("compile_validation") != "auto":
                continue
            if block.get("language") != "cpp":
                print(
                    f"ERROR: unexpected language in {lesson_path.relative_to(COURSE_DIR)}",
                    file=sys.stderr,
                )
                return 2
            code = block.get("code")
            if not isinstance(code, str) or not code.strip():
                print(
                    f"ERROR: empty code block in {lesson_path.relative_to(COURSE_DIR)}",
                    file=sys.stderr,
                )
                return 2
            standard = block.get("standard", "c++20")
            if standard not in {"c++11", "c++14", "c++17", "c++20", "c++23"}:
                print(
                    f"ERROR: unsupported standard label {standard!r} in {lesson_path.relative_to(COURSE_DIR)}",
                    file=sys.stderr,
                )
                return 2
            examples.append((lesson_path, standard, code))
            lesson_example_count += 1

    # Projects reference real starter files from their own metadata. Validate each
    # referenced path (including its README), then compile every standalone starter.
    for project_path in sorted(COURSE_DIR.glob("projects/[0-9][0-9][0-9]-*.json")):
        try:
            project = json.loads(project_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(
                f"ERROR: cannot parse {project_path.relative_to(COURSE_DIR)}: {exc}",
                file=sys.stderr,
            )
            return 2
        starter_files = project.get("starter_files", [])
        starter_readme = project.get("starter_readme")
        if not starter_files or not starter_readme:
            print(
                f"ERROR: {project_path.relative_to(COURSE_DIR)} must list starter_files and starter_readme",
                file=sys.stderr,
            )
            return 2
        for relative in [*starter_files, starter_readme]:
            target = (COURSE_DIR / relative).resolve()
            if COURSE_DIR.resolve() not in target.parents or not target.is_file():
                print(
                    f"ERROR: missing/unsafe project starter path {relative!r} in {project_path.relative_to(COURSE_DIR)}",
                    file=sys.stderr,
                )
                return 2
        for relative in starter_files:
            source = (COURSE_DIR / relative).resolve()
            try:
                code = source.read_text(encoding="utf-8")
            except OSError as exc:
                print(f"ERROR: cannot read starter {relative}: {exc}", file=sys.stderr)
                return 2
            if source.suffix != ".cpp" or not code.strip():
                print(
                    f"ERROR: project starter must be a non-empty .cpp file: {relative}",
                    file=sys.stderr,
                )
                return 2
            examples.append((source, "c++20", code))
            project_starter_count += 1

    if args.limit:
        examples = examples[: args.limit]
    if not examples:
        print("ERROR: no compile-validation examples found.", file=sys.stderr)
        return 2

    def compile_one(
        index: int, lesson_path: Path, standard: str, code: str, tmp_dir: Path
    ):
        source_path = tmp_dir / f"example_{index:03d}.cpp"
        source_path.write_text(code, encoding="utf-8")
        cmd = [
            compiler,
            f"-std={standard}",
            "-Wall",
            "-Wextra",
            "-Wpedantic",
            "-fsyntax-only",
            str(source_path),
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=45, check=False
            )
        except subprocess.TimeoutExpired:
            return (lesson_path, standard, "compiler timed out after 45 seconds")
        if result.returncode == 0:
            return None
        detail = (
            result.stderr or result.stdout or f"compiler exited {result.returncode}"
        ).strip()
        return (lesson_path, standard, detail)

    passed = 0
    failed: list[tuple[Path, str, str]] = []
    with tempfile.TemporaryDirectory(prefix="codeleaf-cpp-check-") as tmp:
        tmp_dir = Path(tmp)
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures = [
                pool.submit(compile_one, index, lesson_path, standard, code, tmp_dir)
                for index, (lesson_path, standard, code) in enumerate(examples, start=1)
            ]
            for completed, future in enumerate(
                concurrent.futures.as_completed(futures), start=1
            ):
                result = future.result()
                if result is None:
                    passed += 1
                else:
                    failed.append(result)
                if completed % 25 == 0 or completed == len(futures):
                    print(
                        f"Progress: {completed}/{len(futures)} checked; {passed} passed; {len(failed)} failed",
                        flush=True,
                    )

    print(f"Compiler: {compiler}")
    print(
        f"Mode: compile-only syntax/type validation (-fsyntax-only); no example executed; parallel jobs: {args.jobs}"
    )
    print(
        f"Lesson examples discovered: {lesson_example_count} | Project starter files discovered: {project_starter_count}"
    )
    print(f"Checked: {len(examples)} | Passed: {passed} | Failed: {len(failed)}")
    if failed:
        for lesson_path, standard, detail in failed:
            print(f"\nFAIL [{standard}] {lesson_path.relative_to(COURSE_DIR)}")
            print(detail[:5000])
        return 1
    print(
        "All selected authored C++ lesson examples and project starter files passed compilation checks."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
