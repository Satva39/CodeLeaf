"""Run one coordinated, safety-gated course-content + portfolio ZIP copy to Catalyst.

Default invocation is read-only dry-run. Execute copies to Production Stratus and
verifies both object families. Neon payloads are retained; cleanup/cutover remain
separate operations after app-level validation.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_ENV = {
    "CATALYST_PROJECT_ID": "98281000000013054",
    "CATALYST_PROJECT_ZAID": "50047335443",
    "CATALYST_ENVIRONMENT": "Production",
    "CATALYST_STRATUS_BUCKET": "codeleaf-project-archives-prod-8392",
    "CATALYST_PROJECT_DOMAIN": "https://api.catalyst.zoho.in",
    "CATALYST_ACCOUNTS_URL": "https://accounts.zoho.in",
    "CATALYST_STRATUS_RESOURCE_SUFFIX": ".zohostratus.in",
    "PORTFOLIO_STORAGE_PROVIDER": "database",
    "CATALYST_STRATUS_ENABLED": "false",
    "LESSON_CONTENT_STORAGE_PROVIDER": "database",
}
for name, value in PRODUCTION_ENV.items():
    os.environ[name] = value


def run(label: str, args: list[str]) -> int:
    print(f"\n=== {label} ===", flush=True)
    try:
        return subprocess.run(args, cwd=BACKEND_ROOT, check=False).returncode
    except OSError as exc:
        print(f"Unable to start {label}: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 127


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="read-only inventory (default)")
    mode.add_argument("--execute", action="store_true", help="copy lesson and project ZIP objects to Catalyst; keep Neon copies")
    parser.add_argument("--billing-reviewed", action="store_true", help="confirms Catalyst eligibility/usage has been reviewed")
    parser.add_argument("--backup-ready", action="store_true", help="confirms a recent restorable Neon backup exists")
    parser.add_argument("--batch-size", type=int, default=10, choices=range(1, 51))
    args = parser.parse_args()

    py = sys.executable
    lessons = [py, "scripts/migrate_lesson_content_to_stratus.py"]
    projects = [py, "scripts/migrate_portfolio_archives_to_stratus.py"]

    for script in (
        "scripts/test_catalyst_stratus_adapter.py",
        "scripts/test_migration_repeatability.py",
        "scripts/test_portfolio_zip_upload.py",
        "scripts/test_course_content_bundle.py",
    ):
        code = run(f"Regression test: {script}", [py, script])
        if code:
            return code

    if not args.execute:
        lesson_code = run("Lesson content dry-run", lessons + ["--dry-run"])
        if lesson_code:
            return lesson_code
        return run("Project ZIP dry-run", projects + ["--dry-run"])

    if not args.billing_reviewed:
        print("STOP: review the applicable Catalyst student/non-commercial eligibility and usage terms, then pass --billing-reviewed.", file=sys.stderr)
        return 2
    if not args.backup_ready:
        print("STOP: confirm a recent restorable Neon backup before migration with --backup-ready.", file=sys.stderr)
        return 2

    # Re-run dry-runs immediately before transfer so execution uses a fresh inventory.
    lesson_code = run("Preflight lesson bundle dry-run", lessons + ["--dry-run"])
    if lesson_code:
        return lesson_code
    project_code = run("Preflight portfolio ZIP dry-run", projects + ["--dry-run"])
    if project_code:
        return project_code

    phrase = input('\nAfter reviewing both inventories, type MIGRATE ALL CONTENT to copy lessons and ZIPs: ').strip()
    if phrase != "MIGRATE ALL CONTENT":
        print("Cancelled. No archive or lesson transfer was started.")
        return 0

    lesson_code = run(
        "Copy lesson content to course bundles (Neon bodies retained)",
        lessons + ["--execute", "--billing-reviewed", "--backup-ready", "--batch-size", str(args.batch_size)],
    )
    if lesson_code:
        print("Lesson bundle copy failed; project ZIP migration was not started.", file=sys.stderr)
        return lesson_code

    project_code = run(
        "Copy project ZIP archives (Neon payloads retained)",
        projects + ["--execute", "--batch-size", str(min(args.batch_size, 10))],
    )
    if project_code:
        print("Project ZIP copy failed. Lesson bundle copies remain in Catalyst and can be verified/resumed.", file=sys.stderr)
        return project_code

    lesson_verify = run("Verify every course lesson bundle", lessons + ["--verify"])
    project_verify = run("Verify every project ZIP", projects + ["--verify"])
    if lesson_verify or project_verify:
        print("At least one object family did not fully verify. Neon originals remain intact; do not run cleanup.", file=sys.stderr)
        return 1

    print("\nFULL STORAGE COPY + VERIFICATION: PASS")
    print("Course lessons: copied to compressed course bundles and verified.")
    print("Project ZIPs: copied to Catalyst and verified.")
    print("Neon lesson JSON and ZIP payloads: retained.")
    print("Portfolio provider: database; Catalyst portfolio writes: disabled.")
    print("Next: deploy/test lesson reads and portfolio flows; only then consider Neon cleanup and new-write cutover.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
