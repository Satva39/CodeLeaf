"""One-run, safety-gated Neon -> Catalyst Stratus portfolio archive migration.

This script copies existing project ZIP archives to the CodeLeaf Production
Stratus bucket, updates each submission's storage reference, and verifies the
remote object. It NEVER deletes legacy Neon ZIP bytes and NEVER toggles the
active portfolio provider. Run from backend/ after applying the installer.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# Pin the migration process to the verified India Production Catalyst project.
# OAuth credentials and DATABASE_URL are read from the user's backend/.env.
PRODUCTION_ENV = {
    "CATALYST_PROJECT_ID": "98281000000013054",
    "CATALYST_PROJECT_ZAID": "50047335443",
    "CATALYST_ENVIRONMENT": "Production",
    "CATALYST_STRATUS_BUCKET": "codeleaf-project-archives-prod-8392",
    "CATALYST_PROJECT_DOMAIN": "https://api.catalyst.zoho.in",
    "CATALYST_ACCOUNTS_URL": "https://accounts.zoho.in",
    "CATALYST_STRATUS_RESOURCE_SUFFIX": ".zohostratus.in",
    # Keep live writes on Neon throughout this archive-copy phase.
    "PORTFOLIO_STORAGE_PROVIDER": "database",
    "CATALYST_STRATUS_ENABLED": "false",
}
for _name, _value in PRODUCTION_ENV.items():
    os.environ[_name] = _value

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import inspect, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from app.config import settings  # noqa: E402
from app.db import engine  # noqa: E402

EXPECTED_ALEMBIC_REVISION = "0010_catalyst_stratus"
SUMMARY_RE = re.compile(r"^([a-z][a-z0-9_]+):\s*([0-9,]+)\s*$", re.MULTILINE)


def fail(message: str, code: int = 2) -> int:
    print(f"\nSTOP: {message}", file=sys.stderr)
    return code


def run_command(label: str, args: list[str], *, capture: bool = False) -> tuple[int, str]:
    print(f"\n=== {label} ===")
    try:
        result = subprocess.run(
            args,
            cwd=BACKEND_ROOT,
            text=True,
            capture_output=capture,
            check=False,
        )
    except OSError as exc:
        return 127, str(exc)
    output = ""
    if capture:
        output = (result.stdout or "") + (result.stderr or "")
        print(output, end="" if output.endswith("\n") else "\n")
    else:
        print(f"Exit code: {result.returncode}")
    return result.returncode, output


def parse_summary(output: str) -> dict[str, int]:
    return {key: int(value.replace(",", "")) for key, value in SUMMARY_RE.findall(output)}


def validate_configuration() -> str | None:
    if engine is None:
        return "DATABASE_URL is not configured; backend/.env must point to the Neon PostgreSQL database."
    if settings.catalyst_environment.strip().casefold() != "production":
        return "CATALYST_ENVIRONMENT is not Production."
    checks = {
        "CATALYST_PROJECT_ID": (settings.catalyst_project_id or "", PRODUCTION_ENV["CATALYST_PROJECT_ID"]),
        "CATALYST_PROJECT_ZAID": (settings.catalyst_project_zaid or "", PRODUCTION_ENV["CATALYST_PROJECT_ZAID"]),
        "CATALYST_STRATUS_BUCKET": (settings.catalyst_stratus_bucket or "", PRODUCTION_ENV["CATALYST_STRATUS_BUCKET"]),
        "CATALYST_PROJECT_DOMAIN": (settings.catalyst_project_domain.rstrip("/"), PRODUCTION_ENV["CATALYST_PROJECT_DOMAIN"]),
        "CATALYST_ACCOUNTS_URL": (settings.catalyst_accounts_url.rstrip("/"), PRODUCTION_ENV["CATALYST_ACCOUNTS_URL"]),
        "CATALYST_STRATUS_RESOURCE_SUFFIX": (settings.catalyst_stratus_resource_suffix, PRODUCTION_ENV["CATALYST_STRATUS_RESOURCE_SUFFIX"]),
    }
    for name, (actual, expected) in checks.items():
        if actual != expected:
            return f"{name} does not match the verified Production setting."
    if not all((settings.catalyst_client_id, settings.catalyst_client_secret, settings.catalyst_refresh_token)):
        return "Catalyst OAuth credentials are incomplete in backend/.env."
    if settings.portfolio_storage_provider.strip().casefold() != "database":
        return "PORTFOLIO_STORAGE_PROVIDER must remain database during migration."
    if settings.catalyst_stratus_enabled is not False:
        return "CATALYST_STRATUS_ENABLED must remain false during migration."
    if not settings.catalyst_verify_upload_checksum:
        return "CATALYST_VERIFY_UPLOAD_CHECKSUM must be true."
    try:
        database_url = make_url(settings.sqlalchemy_database_url or "")
    except Exception:
        return "DATABASE_URL could not be parsed."
    host = (database_url.host or "").lower()
    if not host.endswith(".neon.tech"):
        return "DATABASE_URL host is not a recognized Neon hostname; refusing to migrate an unknown database."
    return None


def validate_schema() -> tuple[str | None, dict[str, Any]]:
    if engine is None:
        return "Database engine is unavailable.", {}
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        required_tables = {"alembic_version", "project_submissions", "project_submission_zip_chunks"}
        missing = sorted(required_tables - tables)
        if missing:
            return "Required migration tables are missing: " + ", ".join(missing), {}
        with engine.connect() as connection:
            revisions = connection.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
            database_name = connection.execute(text("SELECT current_database()")).scalar_one()
            database_size = int(connection.execute(text("SELECT pg_database_size(current_database())")).scalar_one())
        if revisions != [EXPECTED_ALEMBIC_REVISION]:
            return (
                f"Neon schema revision is {revisions!r}; expected {EXPECTED_ALEMBIC_REVISION}. "
                "The deployed Render start command normally runs Alembic; verify the Neon backup and schema before continuing."
            ), {}
        columns = {column["name"] for column in inspector.get_columns("project_submissions")}
        needed_columns = {
            "storage_provider", "storage_bucket", "storage_key", "file_size_bytes",
            "checksum_sha256", "object_status", "uploaded_at", "migrated_at",
            "zip_bundle", "stored_bytes",
        }
        missing_columns = sorted(needed_columns - columns)
        if missing_columns:
            return "project_submissions is missing required columns: " + ", ".join(missing_columns), {}
        chunk_columns = {column["name"] for column in inspector.get_columns("project_submission_zip_chunks")}
        if not {"submission_id", "sequence", "payload"}.issubset(chunk_columns):
            return "project_submission_zip_chunks schema does not match the migration script.", {}
        return None, {"database_name": database_name, "database_size_bytes": database_size, "revision": revisions[0]}
    except Exception as exc:
        return f"Could not validate Neon schema: {type(exc).__name__}: {str(exc)[:250]}", {}


def run_audit() -> dict[str, Any] | None:
    # Keep per-submission identifiers and ZIP filenames out of the console output.
    print("\n=== Read-only Neon storage audit ===")
    try:
        result = subprocess.run(
            [sys.executable, "scripts/audit_neon_storage.py", "--json"],
            cwd=BACKEND_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        print(f"Could not start the read-only audit: {type(exc).__name__}", file=sys.stderr)
        return None
    if result.returncode != 0:
        print("Read-only audit failed; no migration was started.", file=sys.stderr)
        # Avoid echoing driver error details that may contain connection metadata.
        return None
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("Audit output was not valid JSON; no migration was started.", file=sys.stderr)
        return None
    database = report.get("database") or {}
    print(f"Read-only audit connected to database: {database.get('name', '(unknown)')}")
    print(f"Database size: {int(database.get('size_bytes', 0) or 0):,} bytes")
    return report


def estimate_transfer_bytes() -> tuple[int, int, int]:
    """Return candidate count/bytes and count of empty/invalid source archives."""
    if engine is None:
        raise RuntimeError("Neon database engine is unavailable.")
    source_size = (
        "CASE WHEN ps.zip_bundle IS NOT NULL THEN octet_length(ps.zip_bundle) "
        "ELSE COALESCE(ch.chunk_bytes, 0) END"
    )
    query = text(
        "SELECT COUNT(*), COALESCE(SUM(" + source_size + "), 0), "
        "COUNT(*) FILTER (WHERE (" + source_size + ") <= 0) "
        "FROM project_submissions ps LEFT JOIN ("
        "SELECT submission_id, COUNT(*) AS chunk_count, "
        "SUM(octet_length(payload)) AS chunk_bytes "
        "FROM project_submission_zip_chunks GROUP BY submission_id"
        ") ch ON ch.submission_id = ps.id "
        "WHERE (ps.zip_bundle IS NOT NULL OR COALESCE(ch.chunk_count, 0) > 0) "
        "AND NOT (COALESCE(ps.storage_provider, '') = 'catalyst_stratus' "
        "AND COALESCE(ps.object_status, '') = 'verified')"
    )
    with engine.connect() as connection:
        connection.execute(text("SET TRANSACTION READ ONLY"))
        row = connection.execute(query).one()
    return int(row[0] or 0), int(row[1] or 0), int(row[2] or 0)


def main() -> int:
    print("CodeLeaf: one-run Neon → Catalyst Production archive migration")
    print("Target bucket: codeleaf-project-archives-prod-8392")
    print("Relational database: Neon PostgreSQL (kept active)")
    print("Safety: legacy Neon ZIP bytes will NOT be deleted by this script.")
    print("Scope: portfolio ZIP archives only; user, course, billing and subscription data stay in Neon.\n")

    config_error = validate_configuration()
    if config_error:
        return fail(config_error)

    schema_error, schema = validate_schema()
    if schema_error:
        return fail(schema_error)

    print(f"Neon database: {schema['database_name']}")
    print(f"Neon database size: {schema['database_size_bytes']:,} bytes")
    print(f"Alembic revision: {schema['revision']}")
    print("Production Catalyst credentials: configured (values hidden)")
    print("Portfolio provider: database; Catalyst writes: disabled")

    # Fast, deterministic, local regression checks before touching the live DB.
    for script in (
        "scripts/test_catalyst_stratus_adapter.py",
        "scripts/test_migration_repeatability.py",
        "scripts/test_portfolio_zip_upload.py",
    ):
        code, _ = run_command(f"Regression test: {script}", [sys.executable, script], capture=False)
        if code != 0:
            return fail(f"Regression test failed: {script}. No live archive transfer was started.", code)

    audit = run_audit()
    if audit is None:
        return 2
    archives = audit.get("portfolio_archives") or {}
    print("\nNeon portfolio archive inventory:")
    for key in (
        "archives_with_legacy_payload",
        "archives_with_inline_bytes",
        "inline_payload_bytes",
        "chunk_rows",
        "chunk_payload_bytes",
    ):
        print(f"  {key}: {int(archives.get(key, 0) or 0):,}")
    candidate_count, candidate_bytes, invalid_source_count = estimate_transfer_bytes()
    print(f"\nEstimated archives to copy: {candidate_count:,}")
    print(f"Estimated bytes to copy: {candidate_bytes:,} ({candidate_bytes / (1024 ** 3):.3f} GiB)")
    if invalid_source_count:
        return fail(f"Found {invalid_source_count} empty archive source(s). No transfer was started; review those records first.")

    code, dry_output = run_command(
        "Migration dry-run (read-only)",
        [sys.executable, "scripts/migrate_portfolio_archives_to_stratus.py", "--dry-run"],
        capture=True,
    )
    dry = parse_summary(dry_output)
    if code != 0 or dry.get("failed_transfers", 0) != 0:
        return fail("Dry-run reported failures or returned an error. Review the report; no archive was transferred.", code or 1)
    if dry.get("eligible_for_migration", -1) != candidate_count:
        return fail("Read-only byte estimate and migration dry-run disagree on the number of candidates. No archive was transferred.")

    total = dry.get("total_archives_discovered", 0)
    eligible = dry.get("eligible_for_migration", 0)
    already = dry.get("already_migrated", 0)
    if eligible == 0:
        if total == already:
            print("\nNothing new to transfer. Verifying existing Catalyst references now.")
        elif total == 0:
            print("\nNo legacy portfolio ZIP archives were found. No transfer is necessary.")
            return 0
        else:
            return fail("Dry-run found archive rows that are neither eligible nor already verified. Manual review is required.")
    else:
        print("\nPRE-MIGRATION SAFETY GATES:")
        print("1) CodeLeaf has subscription/advertising features. Do not assume the Zoho student programme applies: its published terms describe free usage for non-commercial student apps.")
        print("   A parent/guardian should review the applicable Zoho plan, commercial-use eligibility and possible usage charges before data is transferred.")
        print("2) Confirm a recent Neon backup/branch snapshot exists and includes project_submissions.zip_bundle and project_submission_zip_chunks.")
        print("3) The standard published Stratus free allowance is limited; usage above included limits may be billable.")
        print("   Estimated transfer size is shown above; ongoing archive downloads and uploads also consume plan quota.")
        billing = input('\nAfter the plan/eligibility review, type BILLING-REVIEWED: ').strip()
        if billing != "BILLING-REVIEWED":
            print("Cancelled. No archive transfer was started.")
            return 0
        backup = input('After confirming the Neon backup/branch snapshot, type BACKUP-READY: ').strip()
        if backup != "BACKUP-READY":
            print("Cancelled. No archive transfer was started.")
            return 0
        typed = input(f'Finally, type MIGRATE {eligible} to copy {eligible} archive(s) to Production Catalyst: ').strip()
        if typed != f"MIGRATE {eligible}":
            print("Cancelled. No archive transfer was started.")
            return 0

        code, _ = run_command(
            "Transfer legacy Neon archives to Catalyst (Neon copies retained)",
            [sys.executable, "scripts/migrate_portfolio_archives_to_stratus.py", "--execute", "--batch-size", "10"],
            capture=False,
        )
        if code != 0:
            print("Transfer command reported failures. Running verification for completed transfers.", file=sys.stderr)

    verify_code, verify_output = run_command(
        "Verify every migrated Production Catalyst archive",
        [sys.executable, "scripts/migrate_portfolio_archives_to_stratus.py", "--verify"],
        capture=True,
    )
    verified = parse_summary(verify_output)
    if verify_code != 0 or verified.get("failed_transfers", 0) != 0:
        return fail("At least one object failed verification. Neon copies were retained; do not run cleanup.", verify_code or 1)
    if verified.get("total_archives_discovered", 0) != verified.get("already_migrated", 0):
        return fail("Not every discovered archive has a verified Catalyst reference. Neon copies were retained.")

    print("\nMIGRATION COPY + VERIFICATION: PASS")
    print(f"Verified archive references: {verified.get('already_migrated', 0):,}")
    print(f"Neon archive bytes still present: {verified.get('bytes_still_stored_in_neon', 0):,}")
    print("Neon ZIP payloads were not deleted.")
    print("PORTFOLIO_STORAGE_PROVIDER remains database; CATALYST_STRATUS_ENABLED remains false.")
    print("Next: test owner-only portfolio upload/download/share/delete on a test account, then decide whether to enable new Catalyst writes.")
    print("Do NOT run --cleanup as part of this one-run operation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
