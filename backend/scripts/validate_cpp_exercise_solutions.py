"""Compile-check protected C++ exercise reference implementations without running them.

Run from backend/: python scripts/validate_cpp_exercise_solutions.py
The nlohmann/json example is skipped unless --check-external is passed and the
external single-header library is installed in the compiler's include path.
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
        "--jobs",
        type=int,
        default=min(6, os.cpu_count() or 2),
        help="Parallel compiler processes (default: up to 6)",
    )
    parser.add_argument(
        "--check-external",
        action="store_true",
        help="Attempt the JSON example too; requires nlohmann/json.hpp",
    )
    args = parser.parse_args()
    compiler = shutil.which(args.compiler)
    if compiler is None:
        print(
            f"ERROR: compiler {args.compiler!r} was not found on PATH.", file=sys.stderr
        )
        return 2
    if not 1 <= args.jobs <= 32:
        parser.error("--jobs must be between 1 and 32")

    entries: list[tuple[Path, str, bool]] = []
    for path in sorted(COURSE_DIR.glob("modules/*/solutions/*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(
                f"ERROR: cannot parse {path.relative_to(COURSE_DIR)}: {exc}",
                file=sys.stderr,
            )
            return 2
        answer = doc.get("answer", "")
        if not isinstance(answer, str) or "#include" not in answer:
            continue
        external = "#include <nlohmann/json.hpp>" in answer
        if external and not args.check_external:
            entries.append((path, answer, True))
        else:
            entries.append((path, answer, False))
    if not entries:
        print("ERROR: no protected exercise reference code found.", file=sys.stderr)
        return 2

    to_check = [(p, code) for p, code, skip in entries if not skip]
    skipped = [(p, code) for p, code, skip in entries if skip]
    passed = 0
    failed: list[tuple[Path, str]] = []

    def compile_one(index: int, path: Path, code: str, temp_dir: Path):
        source = temp_dir / f"solution_{index:03d}.cpp"
        source.write_text(code, encoding="utf-8")
        cmd = [
            compiler,
            "-std=c++20",
            "-Wall",
            "-Wextra",
            "-Wpedantic",
            "-fsyntax-only",
            str(source),
        ]
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=45, check=False
            )
        except subprocess.TimeoutExpired:
            return (path, "compiler timed out after 45 seconds")
        if proc.returncode == 0:
            return None
        return (
            path,
            (
                proc.stderr or proc.stdout or f"compiler exited {proc.returncode}"
            ).strip(),
        )

    with tempfile.TemporaryDirectory(prefix="codeleaf-cpp-solutions-") as tmp:
        temp_dir = Path(tmp)
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures = [
                pool.submit(compile_one, i, path, code, temp_dir)
                for i, (path, code) in enumerate(to_check, 1)
            ]
            for complete, future in enumerate(
                concurrent.futures.as_completed(futures), 1
            ):
                result = future.result()
                if result is None:
                    passed += 1
                else:
                    failed.append(result)
                if complete % 10 == 0 or complete == len(futures):
                    print(
                        f"Progress: {complete}/{len(futures)} checked; {passed} passed; {len(failed)} failed",
                        flush=True,
                    )

    print(f"Compiler: {compiler}")
    print("Mode: compile-only syntax/type validation; reference code was not executed")
    print(
        f"Reference solutions: {len(entries)} | Passed compile checks: {passed} | Failed: {len(failed)} | External-dependency skip: {len(skipped)}"
    )
    for path, detail in failed:
        print(f"\nFAIL {path.relative_to(COURSE_DIR)}\n{detail[:5000]}")
    for path, _ in skipped:
        print(
            f"\nSKIP {path.relative_to(COURSE_DIR)} — requires nlohmann/json.hpp (not bundled)"
        )
    if failed:
        return 1
    print("All checked protected C++ exercise reference implementations passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
