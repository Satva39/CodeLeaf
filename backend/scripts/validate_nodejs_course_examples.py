"""Syntax-check the Node.js course examples without executing learner code.

Run from backend/: python scripts/validate_nodejs_course_examples.py
The checker writes temporary .mjs files outside the course tree and invokes
`node --check`; it does not import dependencies, contact services, or execute examples.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parents[1] / "content" / "courses" / "nodejs"


def iter_examples():
    for path in sorted(COURSE_ROOT.glob("modules/*/lessons/*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for index, block in enumerate(data.get("content", {}).get("content_blocks", []), 1):
            if block.get("type") == "code" and block.get("language") == "javascript":
                code = block.get("code")
                if isinstance(code, str) and code.strip():
                    yield f"lesson {data.get('sequence')} ({data.get('title')}) block {index}", code

    for path in sorted(COURSE_ROOT.glob("modules/*/exercises/*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        code = data.get("starter", {}).get("code")
        if isinstance(code, str) and code.strip():
            yield f"exercise {data.get('sequence')} ({data.get('title')}) starter", code


def main() -> int:
    node = shutil.which("node")
    if not node:
        print("NOT RUN: Node.js executable was not found on PATH.", file=sys.stderr)
        return 2
    if not COURSE_ROOT.is_dir():
        print(f"FAIL: Node.js course folder not found: {COURSE_ROOT}", file=sys.stderr)
        return 2

    examples = list(iter_examples())
    failures: list[tuple[str, str]] = []
    with tempfile.TemporaryDirectory(prefix="codeleaf-nodejs-check-") as temporary:
        temp_root = Path(temporary)
        for index, (label, code) in enumerate(examples, 1):
            source = temp_root / f"example-{index:04d}.mjs"
            source.write_text(code + "\n", encoding="utf-8")
            result = subprocess.run(
                [node, "--check", str(source)],
                text=True,
                capture_output=True,
                check=False,
                timeout=10,
            )
            if result.returncode:
                message = (result.stderr or result.stdout or "node --check failed").strip()
                failures.append((label, message))

    print(json.dumps({
        "course_slug": "nodejs",
        "node_version": subprocess.run([node, "--version"], text=True, capture_output=True, check=False).stdout.strip(),
        "checked_examples": len(examples),
        "passed": len(examples) - len(failures),
        "failed": len(failures),
        "execution_performed": False,
        "scope": "Syntax only: Node.js --check on temporary .mjs copies; no application code was executed.",
        "failures": [{"example": label, "error": message} for label, message in failures[:50]],
    }, indent=2, ensure_ascii=False))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
