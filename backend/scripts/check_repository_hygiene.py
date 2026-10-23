"""Check tracked source and optional release artifacts for accidental secrets/runtime files.

Run from backend/: python scripts/check_repository_hygiene.py
Inspect a patch/release ZIP explicitly with --artifact path/to/release.zip.
The checker reports file paths and rule names only, never matched secret values.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GITIGNORE = PROJECT_ROOT / ".gitignore"
FORBIDDEN_DIRS = {".venv", "venv", "node_modules", "__pycache__", "postgres-data", ".next"}
FORBIDDEN_SECRET_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
FORBIDDEN_DB_SUFFIXES = {".db", ".sqlite", ".sqlite3", ".dump", ".bak", ".backup", ".dmp"}
SECRET_PATTERNS = (
    ("private-key material", re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("AWS access key", re.compile(rb"\bAKIA[0-9A-Z]{16}\b")),
    ("Git hosting token", re.compile(rb"\b(?:ghp|github_pat|gho|ghs|ghu|ghr|glpat)_[A-Za-z0-9_]{20,}\b")),
    ("live payment key marker", re.compile(rb"\b(?:rzp_live_[A-Za-z0-9]{10,}|sk_live_[A-Za-z0-9]{10,})\b")),
    ("Google API key marker", re.compile(rb"\bAIza[0-9A-Za-z_-]{35}\b")),
)


def forbidden_path(path: PurePosixPath) -> str | None:
    parts = path.parts
    if any(part in FORBIDDEN_DIRS for part in parts):
        return "runtime/dependency directory"
    if any(part == ".env" or (part.startswith(".env.") and part != ".env.example") for part in parts):
        return "environment file (only .env.example is permitted)"
    name = path.name.lower()
    suffix = Path(name).suffix.lower()
    if suffix in FORBIDDEN_SECRET_SUFFIXES:
        return "private key/certificate file"
    if suffix in FORBIDDEN_DB_SUFFIXES or name.endswith((".sql.gz", ".dump.gz", ".sqlite.gz")):
        return "database/runtime dump"
    if name in {"dump.sql", "database-dump.sql", "database_backup.sql", "backup.sql"}:
        return "database dump"
    return None


def scan_secret_markers(name: str, content: bytes) -> list[str]:
    # Example environment files are allowed by path policy, but are still scanned
    # for accidental live tokens/private keys before they enter a release artifact.
    return [description for description, pattern in SECRET_PATTERNS if pattern.search(content)]


def check_git_tracked() -> tuple[list[str], bool]:
    problems: list[str] = []
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"], cwd=PROJECT_ROOT,
            capture_output=True, check=False,
        )
    except OSError:
        return ["Git tracking check skipped: Git executable unavailable."], False
    if result.returncode != 0:
        return ["Git tracking check skipped: directory is not a Git checkout."], False

    tracked = [item.decode("utf-8", "replace") for item in result.stdout.split(b"\0") if item]
    checked_text = 0
    for item in tracked:
        path = PurePosixPath(item.replace("\\", "/"))
        reason = forbidden_path(path)
        if reason:
            problems.append(f"tracked path {item!r}: {reason}")
            continue
        full_path = PROJECT_ROOT.joinpath(*path.parts)
        try:
            if not full_path.is_file() or full_path.stat().st_size > 5_000_000:
                continue
            content = full_path.read_bytes()
        except OSError:
            continue
        # Binary files do not need a text marker scan.
        if b"\x00" in content[:8192]:
            continue
        checked_text += 1
        for marker in scan_secret_markers(item, content):
            problems.append(f"tracked file {item!r}: possible {marker}")
    print(f"Checked {len(tracked)} tracked paths and {checked_text} text files for repository hygiene.")
    return problems, True


def check_artifact(artifact: Path) -> list[str]:
    problems: list[str] = []
    if not artifact.exists():
        return [f"artifact does not exist: {artifact}"]
    entries: list[tuple[str, bytes | None]] = []
    if artifact.is_file() and zipfile.is_zipfile(artifact):
        try:
            with zipfile.ZipFile(artifact) as archive:
                for item in archive.infolist():
                    name = item.filename.replace("\\", "/").rstrip("/")
                    if item.is_dir() or not name:
                        continue
                    content = archive.read(item) if item.file_size <= 5_000_000 else None
                    entries.append((name, content))
        except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
            return [f"could not inspect artifact ZIP ({type(exc).__name__})"]
    elif artifact.is_dir():
        for file_path in artifact.rglob("*"):
            if not file_path.is_file():
                continue
            name = file_path.relative_to(artifact).as_posix()
            try:
                content = file_path.read_bytes() if file_path.stat().st_size <= 5_000_000 else None
            except OSError:
                content = None
            entries.append((name, content))
    else:
        return ["artifact must be a ZIP archive or directory"]

    for name, content in entries:
        path = PurePosixPath(name)
        reason = forbidden_path(path)
        if reason:
            problems.append(f"artifact entry {name!r}: {reason}")
            continue
        if content is not None and b"\x00" not in content[:8192]:
            for marker in scan_secret_markers(name, content):
                problems.append(f"artifact entry {name!r}: possible {marker}")
    print(f"Checked {len(entries)} release-artifact entries.")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, help="Inspect a release ZIP or unpacked release directory")
    args = parser.parse_args()

    problems: list[str] = []
    if not GITIGNORE.is_file():
        problems.append("root .gitignore is missing")
    else:
        patterns = set(GITIGNORE.read_text(encoding="utf-8").splitlines())
        for required in (".env", ".env.*", "!.env.example", ".venv/", "node_modules/", "*.db", "*.sqlite"):
            if required not in patterns:
                problems.append(f".gitignore is missing required pattern {required!r}")

    tracked_problems, has_git = check_git_tracked()
    problems.extend(item for item in tracked_problems if not item.startswith("Git tracking check skipped:"))
    if not has_git:
        print("WARN: tracked-file checks could not run outside a Git checkout.")
    if args.artifact:
        problems.extend(check_artifact(args.artifact.resolve()))

    if problems:
        for problem in problems[:100]:
            print("FAIL:", problem, file=sys.stderr)
        print(f"FAIL: repository hygiene found {len(problems)} issue(s).", file=sys.stderr)
        return 1
    print("PASS: no forbidden tracked files or high-confidence secret markers were found.")
    if not args.artifact:
        print("NOTE: use --artifact on the actual ZIP/directory before distributing a release artifact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
