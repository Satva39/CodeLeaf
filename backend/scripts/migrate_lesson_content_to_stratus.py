"""Resumable migration of full lesson JSON from Neon to one gzip bundle per course.

Default is read-only. --execute copies and verifies bundles but retains Neon JSON.
--cleanup --confirm-cleanup strips lesson body JSON only after backup and verify.
--restore-neon --confirm-restore restores full JSON from Stratus and retains objects.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Do not depend on the developer's local Development bucket during this migration.
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
}
for _name, _value in PRODUCTION_ENV.items():
    os.environ[_name] = _value

from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.exc import SQLAlchemyError  # noqa: E402
from app.config import settings  # noqa: E402
from app.db import SessionLocal, engine  # noqa: E402
from app.models import Course, Lesson, Module  # noqa: E402
from app.storage import get_catalyst_storage  # noqa: E402
from app.storage.course_content import (  # noqa: E402
    externalize_course_content,
    publish_course_bundle,
    restore_course_content_to_neon,
    verify_course_bundle,
)


def fail(message: str, code: int = 2) -> int:
    print(f"\nSTOP: {message}", file=sys.stderr)
    return code


def validate_environment() -> str | None:
    if engine is None or SessionLocal is None:
        return "DATABASE_URL is not configured in backend/.env."
    if settings.catalyst_environment.strip().casefold() != "production":
        return "Catalyst environment is not Production."
    if settings.catalyst_project_id != PRODUCTION_ENV["CATALYST_PROJECT_ID"]:
        return "Catalyst project ID does not match the verified Production project."
    if settings.catalyst_project_zaid != PRODUCTION_ENV["CATALYST_PROJECT_ZAID"]:
        return "Catalyst Production ZAID does not match the verified Production environment."
    if settings.catalyst_stratus_bucket != PRODUCTION_ENV["CATALYST_STRATUS_BUCKET"]:
        return "Catalyst Production bucket does not match the verified bucket."
    if settings.catalyst_project_domain.rstrip("/") != PRODUCTION_ENV["CATALYST_PROJECT_DOMAIN"]:
        return "Catalyst API domain is not the verified India endpoint."
    if settings.catalyst_accounts_url.rstrip("/") != PRODUCTION_ENV["CATALYST_ACCOUNTS_URL"]:
        return "Catalyst Accounts URL is not the verified India endpoint."
    if settings.catalyst_stratus_resource_suffix != PRODUCTION_ENV["CATALYST_STRATUS_RESOURCE_SUFFIX"]:
        return "Catalyst Stratus suffix is not the verified India suffix."
    if not all((settings.catalyst_client_id, settings.catalyst_client_secret, settings.catalyst_refresh_token)):
        return "Catalyst OAuth credentials are incomplete."
    if settings.portfolio_storage_provider.strip().casefold() != "database" or settings.catalyst_stratus_enabled:
        return "Keep PORTFOLIO_STORAGE_PROVIDER=database and CATALYST_STRATUS_ENABLED=false during migration."
    database_url = settings.sqlalchemy_database_url or ""
    if ".neon.tech" not in database_url.lower():
        return "DATABASE_URL is not a recognized Neon PostgreSQL URL; refusing to continue."
    return None


def course_inventory() -> list[dict[str, Any]]:
    assert SessionLocal is not None
    with SessionLocal() as db:
        rows = db.execute(
            select(
                Course.id,
                Course.slug,
                func.count(Lesson.id).label("lesson_count"),
                func.coalesce(func.sum(func.octet_length(Lesson.content.cast(__import__("sqlalchemy").Text))), 0).label("logical_bytes"),
            )
            .outerjoin(Module, Module.course_id == Course.id)
            .outerjoin(Lesson, Lesson.module_id == Module.id)
            .group_by(Course.id, Course.slug)
            .order_by(Course.slug)
        ).all()
        return [
            {
                "id": row.id,
                "slug": row.slug,
                "lesson_count": int(row.lesson_count or 0),
                "logical_bytes": int(row.logical_bytes or 0),
            }
            for row in rows
            if int(row.lesson_count or 0) > 0
        ]


def run_dry_run() -> int:
    inventory = course_inventory()
    print("Read-only lesson content migration plan")
    print(f"Courses with lessons: {len(inventory):,}")
    print(f"Lessons discovered: {sum(item['lesson_count'] for item in inventory):,}")
    print(f"Logical lesson JSON bytes: {sum(item['logical_bytes'] for item in inventory):,}")
    print(f"Proposed Stratus objects: {len(inventory):,} (one compressed bundle per course)")
    print("Neon lesson JSON will remain intact during --execute.")
    for item in inventory:
        print(f"  {item['slug']}: {item['lesson_count']:,} lessons, {item['logical_bytes']:,} logical bytes")
    return 0


def run_execute(batch_size: int) -> int:
    storage = get_catalyst_storage()
    if storage is None or SessionLocal is None:
        return fail("Catalyst storage or Neon database is unavailable.")
    inventory = course_inventory()
    transferred = 0
    failed = 0
    total_raw = 0
    for start in range(0, len(inventory), batch_size):
        for item in inventory[start : start + batch_size]:
            with SessionLocal() as db:
                course = db.get(Course, item["id"])
                if course is None:
                    failed += 1
                    print(f"[FAILED] Course {item['slug']} disappeared during migration.", file=sys.stderr)
                    continue
                try:
                    record = publish_course_bundle(db, course, storage, externalize=False)
                    db.commit()
                    transferred += 1
                    total_raw += int(record.raw_size_bytes)
                    print(
                        f"[COPIED] {course.slug}: {record.lesson_count:,} lessons, "
                        f"{record.compressed_size_bytes:,} compressed bytes, SHA-256 {record.checksum_sha256}"
                    )
                except Exception as exc:
                    db.rollback()
                    failed += 1
                    print(f"[FAILED] {item['slug']}: {type(exc).__name__}: {str(exc)[:200]}", file=sys.stderr)
    print("\nLesson bundle migration summary")
    print(f"courses_discovered: {len(inventory):,}")
    print(f"courses_copied: {transferred:,}")
    print(f"failed_courses: {failed:,}")
    print(f"raw_bytes_bundled: {total_raw:,}")
    print("Neon lesson JSON retained: yes")
    return 1 if failed else 0


def run_verify() -> int:
    storage = get_catalyst_storage()
    if storage is None or SessionLocal is None:
        return fail("Catalyst storage or Neon database is unavailable.")
    inventory = course_inventory()
    verified = failed = 0
    for item in inventory:
        with SessionLocal() as db:
            course = db.get(Course, item["id"])
            if course is None:
                failed += 1
                continue
            ok, reason = verify_course_bundle(db, course, storage)
            if ok:
                verified += 1
                print(f"[VERIFIED] {course.slug}")
            else:
                failed += 1
                print(f"[VERIFY FAILED] {course.slug}: {reason}", file=sys.stderr)
    print(f"courses_discovered: {len(inventory):,}")
    print(f"courses_verified: {verified:,}")
    print(f"failed_courses: {failed:,}")
    return 1 if failed else 0


def run_cleanup() -> int:
    storage = get_catalyst_storage()
    if storage is None or SessionLocal is None:
        return fail("Catalyst storage or Neon database is unavailable.")
    inventory = course_inventory()
    cleaned = failed = removed_bytes = 0
    # Verify every course first. Never partially clean Neon when any bundle is bad.
    with SessionLocal() as db:
        for item in inventory:
            course = db.get(Course, item["id"])
            ok, reason = verify_course_bundle(db, course, storage) if course else (False, "course_missing")
            if not ok:
                return fail(f"Course {item['slug']} failed verification ({reason}); no Neon content was cleaned.")
    for item in inventory:
        with SessionLocal() as db:
            course = db.get(Course, item["id"])
            try:
                count, size = externalize_course_content(db, course, storage)
                db.commit()
                cleaned += count
                removed_bytes += size
                print(f"[CLEANED] {course.slug}: {count:,} lessons, {size:,} JSON body bytes removed from Neon")
            except Exception as exc:
                db.rollback()
                failed += 1
                print(f"[CLEANUP FAILED] {item['slug']}: {type(exc).__name__}: {str(exc)[:200]}", file=sys.stderr)
    print(f"lessons_externalized: {cleaned:,}")
    print(f"logical_json_bytes_removed: {removed_bytes:,}")
    print("Catalyst course bundles retained: yes")
    return 1 if failed else 0


def run_restore() -> int:
    storage = get_catalyst_storage()
    if storage is None or SessionLocal is None:
        return fail("Catalyst storage or Neon database is unavailable.")
    inventory = course_inventory()
    restored = failed = 0
    for item in inventory:
        with SessionLocal() as db:
            course = db.get(Course, item["id"])
            if course is None:
                failed += 1
                continue
            try:
                count, _size = restore_course_content_to_neon(db, course, storage)
                db.commit()
                restored += count
                print(f"[RESTORED] {course.slug}: {count:,} lessons back in Neon")
            except Exception as exc:
                db.rollback()
                failed += 1
                print(f"[RESTORE FAILED] {item['slug']}: {type(exc).__name__}: {str(exc)[:200]}", file=sys.stderr)
    print(f"lessons_restored: {restored:,}")
    print(f"failed_courses: {failed:,}")
    print("Stratus copies retained: yes")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="read-only inventory (default)")
    mode.add_argument("--execute", action="store_true", help="copy bundles to Catalyst; retain Neon JSON")
    mode.add_argument("--verify", action="store_true", help="verify every course object and lesson reference")
    mode.add_argument("--cleanup", action="store_true", help="remove lesson body JSON from Neon after backup and verification")
    mode.add_argument("--restore-neon", action="store_true", help="restore lesson JSON from Catalyst to Neon")
    parser.add_argument("--confirm-cleanup", action="store_true", help="required with --cleanup")
    parser.add_argument("--confirm-restore", action="store_true", help="required with --restore-neon")
    parser.add_argument("--batch-size", type=int, default=10, choices=range(1, 51))
    parser.add_argument("--billing-reviewed", action="store_true", help="confirms the applicable Catalyst plan/usage has been reviewed")
    parser.add_argument("--backup-ready", action="store_true", help="confirms a recent restorable Neon backup exists")
    args = parser.parse_args()
    if args.cleanup and not args.confirm_cleanup:
        parser.error("--cleanup requires --confirm-cleanup")
    if args.restore_neon and not args.confirm_restore:
        parser.error("--restore-neon requires --confirm-restore")

    config_error = validate_environment()
    if config_error:
        return fail(config_error)
    if engine is None:
        return fail("Neon connection is not configured.")
    try:
        from sqlalchemy import inspect
        tables = set(inspect(engine).get_table_names())
        if "course_content_bundles" not in tables:
            return fail("Missing course_content_bundles table. Deploy the application and run alembic upgrade head first.")
        if args.execute:
            if not args.billing_reviewed:
                return fail("Before upload operations, review student-program eligibility and current Stratus usage; then pass --billing-reviewed.")
            if not args.backup_ready:
                return fail("Confirm a recent restorable Neon backup with --backup-ready before copying.")
            return run_execute(args.batch_size)
        if args.verify:
            return run_verify()
        if args.cleanup:
            if not args.backup_ready:
                return fail("A recent restorable Neon backup is required before cleanup; pass --backup-ready.")
            phrase = input('Type CLEANUP VERIFIED LESSON CONTENT to strip Neon lesson bodies: ').strip()
            if phrase != "CLEANUP VERIFIED LESSON CONTENT":
                print("Cancelled. Neon lesson content was not changed.")
                return 0
            return run_cleanup()
        if args.restore_neon:
            return run_restore()
        return run_dry_run()
    except (SQLAlchemyError, OSError) as exc:
        return fail(f"Migration operation failed: {type(exc).__name__}: {str(exc)[:250]}")


if __name__ == "__main__":
    raise SystemExit(main())
