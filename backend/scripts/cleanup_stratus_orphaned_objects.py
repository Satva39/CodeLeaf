"""Report and conservatively remove Stratus objects with no PostgreSQL reference.

Default mode is read-only. Deletion requires --delete-orphans --confirm-delete and
an age threshold of at least 30 days. Objects without a parseable last_modified
value are never automatically deleted.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import engine  # noqa: E402
from app.storage import StorageError, get_catalyst_storage  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402


def session_factory():
    if engine is None:
        raise RuntimeError("DATABASE_URL is not configured. Run from backend/ with the correct database.")
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def parse_last_modified(value: str | None) -> datetime | None:
    """Catalyst list output example is 'May 21, 2024 01:00 PM' (no timezone)."""
    if not value or not isinstance(value, str):
        return None
    for format_string in ("%b %d, %Y %I:%M %p", "%B %d, %Y %I:%M %p"):
        try:
            return datetime.strptime(value.strip(), format_string)
        except ValueError:
            continue
    return None


def valid_project_key(key: str) -> bool:
    """Only inspect CodeLeaf's own canonical project archive key layout."""
    parts = key.split("/")
    if len(parts) != 3 or parts[0] != "projects" or parts[2] != "archive.zip":
        return False
    try:
        UUID(parts[1])
    except (ValueError, TypeError):
        return False
    return True


def referenced_keys(db: Session) -> set[str]:
    rows = db.execute(
        text(
            "SELECT storage_key FROM project_submissions "
            "WHERE storage_key IS NOT NULL"
        )
    ).scalars().all()
    return {str(key) for key in rows if key}


def database_storage_health(db: Session) -> dict[str, int]:
    row = db.execute(
        text(
            "SELECT "
            "COALESCE(SUM(octet_length(zip_bundle)), 0) AS inline_bytes, "
            "(SELECT COALESCE(SUM(octet_length(payload)), 0) FROM project_submission_zip_chunks) AS chunk_bytes, "
            "COUNT(*) FILTER (WHERE storage_provider='catalyst_stratus' AND object_status='verified') AS verified_objects, "
            "COUNT(*) FILTER (WHERE storage_provider='catalyst_stratus' AND object_status <> 'verified') AS nonverified_objects "
            "FROM project_submissions"
        )
    ).mappings().one()
    return {
        "neon_archive_bytes": int(row["inline_bytes"] or 0) + int(row["chunk_bytes"] or 0),
        "verified_database_object_refs": int(row["verified_objects"] or 0),
        "nonverified_database_object_refs": int(row["nonverified_objects"] or 0),
    }


def pending_multipart_uploads(db: Session) -> list[dict]:
    rows = db.execute(
        text(
            "SELECT id::text AS id, portfolio_metadata->>'stratus_pending_object_key' AS object_key, "
            "portfolio_metadata->>'stratus_pending_multipart_upload_id' AS upload_id "
            "FROM project_submissions "
            "WHERE COALESCE(portfolio_metadata->>'stratus_pending_multipart_cleanup_required', 'false') = 'true'"
        )
    ).mappings().all()
    return [dict(row) for row in rows]


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit orphaned CodeLeaf Stratus objects")
    parser.add_argument("--delete-orphans", action="store_true", help="delete safe, unreferenced, old project objects")
    parser.add_argument("--confirm-delete", action="store_true", help="explicit destructive-operation confirmation")
    parser.add_argument("--older-than-days", type=int, default=45, help="minimum object age; cannot be less than 30 days")
    args = parser.parse_args()
    if args.confirm_delete and not args.delete_orphans:
        parser.error("--confirm-delete requires --delete-orphans")
    if args.delete_orphans and not args.confirm_delete:
        parser.error("--delete-orphans requires --confirm-delete")
    if args.older_than_days < 30:
        parser.error("--older-than-days must be at least 30")

    try:
        storage = get_catalyst_storage()
        if storage is None:
            raise RuntimeError("Catalyst is not configured. Set the CATALYST_* variables first.")
        SessionFactory = session_factory()
        with SessionFactory() as db:
            refs = referenced_keys(db)
            pending = pending_multipart_uploads(db)
            database_health = database_storage_health(db)

        threshold = datetime.now() - timedelta(days=args.older_than_days)
        discovered = 0
        catalyst_bytes = 0
        orphan_count = 0
        deleted_count = 0
        skipped_unknown_age = 0
        for item in storage.iter_objects(prefix="projects/", page_size=100):
            key = str(item.get("key") or "")
            if not valid_project_key(key):
                continue
            discovered += 1
            catalyst_bytes += int(item.get("size") or 0)
            if key in refs:
                continue
            orphan_count += 1
            modified = parse_last_modified(item.get("last_modified"))
            if modified is None:
                skipped_unknown_age += 1
                print(f"[SKIP: UNKNOWN AGE] {key}")
                continue
            if modified > threshold:
                print(f"[SKIP: TOO RECENT] {key} — {item.get('last_modified')}")
                continue
            print(f"[ORPHAN] {key} — {int(item.get('size') or 0):,} bytes — {item.get('last_modified')}")
            if not args.delete_orphans:
                continue
            # Recheck the reference against the live database immediately before deletion.
            with SessionFactory() as db:
                if key in referenced_keys(db):
                    print(f"[SKIP: RE-REFERENCED] {key}")
                    continue
            try:
                storage.delete_object(key)
                deleted_count += 1
                print(f"[DELETED] {key}")
            except StorageError as exc:
                print(f"[DELETE FAILED] {key} — {str(exc)[:180]}", file=sys.stderr)

        print("\nStratus orphan-object summary")
        print(f"catalyst_objects_discovered: {discovered:,}")
        print(f"catalyst_bytes_listed: {catalyst_bytes:,}")
        for health_key, health_value in database_health.items():
            print(f"{health_key}: {health_value:,}")
        print(f"unreferenced_objects: {orphan_count:,}")
        print(f"deleted_objects: {deleted_count:,}")
        print(f"objects_skipped_unknown_age: {skipped_unknown_age:,}")
        print(f"known_pending_multipart_uploads: {len(pending):,}")
        for row in pending:
            print(
                "[PENDING MULTIPART — MANUAL CONSOLE RECONCILIATION] "
                f"submission={row['id']} object={row['object_key']} upload_id={row['upload_id']}"
            )
        if pending:
            print(
                "The current documented Python SDK does not expose multipart-abort; "
                "use Catalyst Console/support to inspect these exact pending uploads."
            )
        if not args.delete_orphans:
            print("Read-only report only. Add --delete-orphans --confirm-delete to remove old, unreferenced keys.")
        return 0
    except (RuntimeError, SQLAlchemyError, StorageError) as exc:
        print(f"Orphan audit failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
