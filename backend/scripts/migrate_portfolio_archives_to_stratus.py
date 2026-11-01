"""Resumable Neon <-> Catalyst Stratus migration for learner project ZIP archives.

Default invocation is read-only dry-run. Use --execute to transfer legacy Neon
archives to Stratus. Use --verify before --cleanup --confirm-cleanup. Use
--restore-neon --confirm-restore to reconstruct Neon chunks from verified Stratus
objects without deleting the object reference or remote object.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import engine  # noqa: E402
from app.models import ProjectSubmission, ProjectSubmissionZipChunk  # noqa: E402
from app.storage import StorageError, get_catalyst_storage  # noqa: E402

INLINE_BLOCK_BYTES = 8 * 1024 * 1024
DB_CHUNK_BYTES = 1024 * 1024
DB_FLUSH_BYTES = 8 * 1024 * 1024

SUMMARY_KEYS = (
    "total_archives_discovered",
    "already_migrated",
    "eligible_for_migration",
    "successfully_transferred",
    "failed_transfers",
    "checksum_failures",
    "total_bytes_transferred",
    "bytes_still_stored_in_neon",
    "bytes_eligible_for_cleanup",
)


def database_session_factory():
    if engine is None:
        raise RuntimeError("DATABASE_URL is not configured. Run this from backend/ after setting backend/.env.")
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def archive_rows(db: Session) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            "SELECT ps.id::text AS id, ps.zip_filename, COALESCE(ps.stored_bytes, 0) AS stored_bytes, "
            "ps.storage_provider, ps.storage_bucket, ps.storage_key, ps.file_size_bytes, "
            "ps.checksum_sha256, ps.object_status, (ps.zip_bundle IS NOT NULL) AS has_inline, "
            "COALESCE(ch.chunk_count, 0) AS chunk_count, COALESCE(ch.chunk_bytes, 0) AS chunk_bytes "
            "FROM project_submissions ps LEFT JOIN ("
            "SELECT submission_id, COUNT(*) AS chunk_count, COALESCE(SUM(octet_length(payload)), 0) AS chunk_bytes "
            "FROM project_submission_zip_chunks GROUP BY submission_id"
            ") ch ON ch.submission_id = ps.id "
            "WHERE ps.zip_bundle IS NOT NULL OR COALESCE(ch.chunk_count, 0) > 0 "
            "OR (ps.storage_provider = 'catalyst_stratus' AND ps.storage_key IS NOT NULL) "
            "ORDER BY ps.submitted_at, ps.id"
        )
    ).mappings().all()
    return [dict(row) for row in rows]


def has_legacy_payload(row: dict[str, Any]) -> bool:
    return bool(row.get("has_inline") or int(row.get("chunk_count") or 0) > 0)


def archive_source_size(db: Session, submission_id: str, *, has_inline: bool) -> int:
    if has_inline:
        value = db.execute(
            text("SELECT COALESCE(octet_length(zip_bundle), 0) FROM project_submissions WHERE id = :id"),
            {"id": submission_id},
        ).scalar_one()
        return int(value or 0)
    value = db.execute(
        text(
            "SELECT COALESCE(SUM(octet_length(payload)), 0) "
            "FROM project_submission_zip_chunks WHERE submission_id = :id"
        ),
        {"id": submission_id},
    ).scalar_one()
    return int(value or 0)


def source_to_temporary_file(db: Session, row: dict[str, Any]):
    """Stage one archive to a disk-backed temporary file; never assemble it in RAM."""
    submission_id = row["id"]
    has_inline = bool(row["has_inline"])
    output = tempfile.TemporaryFile(mode="w+b")
    digest = hashlib.sha256()
    total = 0
    if has_inline:
        expected_size = archive_source_size(db, submission_id, has_inline=True)
        offset = 1  # PostgreSQL bytea substring offsets are one-based.
        while offset <= expected_size:
            payload = db.execute(
                text(
                    "SELECT substring(zip_bundle FROM :offset FOR :length) "
                    "FROM project_submissions WHERE id = :id"
                ),
                {"offset": offset, "length": INLINE_BLOCK_BYTES, "id": submission_id},
            ).scalar_one()
            block = bytes(payload or b"")
            if not block:
                break
            output.write(block)
            digest.update(block)
            total += len(block)
            offset += len(block)
    else:
        # Existing chunk table stores ordered 1 MiB pieces.
        statement = text(
            "SELECT sequence, payload FROM project_submission_zip_chunks "
            "WHERE submission_id = :id ORDER BY sequence"
        ).execution_options(stream_results=True)
        result = db.execute(statement, {"id": submission_id})
        expected_sequence = 0
        try:
            for sequence, payload in result.yield_per(4):
                if int(sequence) != expected_sequence:
                    raise RuntimeError(
                        f"Archive {submission_id} has a missing chunk at sequence {expected_sequence}."
                    )
                block = bytes(payload)
                output.write(block)
                digest.update(block)
                total += len(block)
                expected_sequence += 1
        except Exception:
            output.close()
            raise
        finally:
            result.close()

    expected_size = archive_source_size(db, submission_id, has_inline=has_inline)
    if total != expected_size or total <= 0:
        output.close()
        raise RuntimeError(
            f"Archive {submission_id} source size mismatch (read {total}, expected {expected_size})."
        )

    # A row should normally use either legacy inline bytes or chunks. If both exist,
    # prove they are byte-for-byte identical before choosing the inline representation
    # and before any later cleanup is permitted. Never silently discard a second copy.
    if has_inline and int(row.get("chunk_count") or 0) > 0:
        chunk_digest = hashlib.sha256()
        chunk_total = 0
        statement = text(
            "SELECT sequence, payload FROM project_submission_zip_chunks "
            "WHERE submission_id = :id ORDER BY sequence"
        ).execution_options(stream_results=True)
        result = db.execute(statement, {"id": submission_id})
        expected_sequence = 0
        try:
            for sequence, payload in result.yield_per(4):
                if int(sequence) != expected_sequence:
                    raise RuntimeError(
                        f"Archive {submission_id} has a missing secondary chunk at sequence {expected_sequence}."
                    )
                block = bytes(payload)
                chunk_digest.update(block)
                chunk_total += len(block)
                expected_sequence += 1
        except Exception:
            output.close()
            raise
        finally:
            result.close()
        if chunk_total != total or chunk_digest.digest() != digest.digest():
            output.close()
            raise RuntimeError(
                f"Archive {submission_id} contains inline and chunk payloads that do not match; cleanup is blocked."
            )

    output.seek(0)
    return output, total, digest.hexdigest()


def read_legacy_bytes_still_in_neon(db: Session) -> int:
    inline_bytes = db.execute(
        text("SELECT COALESCE(SUM(octet_length(zip_bundle)), 0) FROM project_submissions")
    ).scalar_one()
    chunk_bytes = db.execute(
        text("SELECT COALESCE(SUM(octet_length(payload)), 0) FROM project_submission_zip_chunks")
    ).scalar_one()
    return int(inline_bytes or 0) + int(chunk_bytes or 0)


def verify_row(storage, row: dict[str, Any]) -> tuple[bool, str]:
    key = row.get("storage_key")
    if not key:
        return False, "missing_storage_key"
    try:
        if not storage.object_exists(key):
            # Catalyst's head_object false result can mean missing OR lack of permission.
            return False, "missing_or_inaccessible_object"
        details = storage.object_metadata(key)
        remote_size = int(details.get("size") or 0)
        expected_size = int(row.get("file_size_bytes") or row.get("stored_bytes") or 0)
        if expected_size and remote_size != expected_size:
            return False, "size_mismatch"
        expected_digest = row.get("checksum_sha256")
        if expected_digest:
            actual_digest = storage.checksum_object(key)
            if actual_digest.lower() != str(expected_digest).lower():
                return False, "checksum_mismatch"
        return True, "verified"
    except StorageError as exc:
        message = str(exc).lower()
        if "checksum" in message:
            return False, "checksum_mismatch"
        return False, "storage_error"


def set_migrated_metadata(db: Session, row: dict[str, Any], stored) -> None:
    db.execute(
        text(
            "UPDATE project_submissions SET storage_provider='catalyst_stratus', "
            "storage_bucket=:bucket, storage_key=:key, file_size_bytes=:size, "
            "checksum_sha256=:sha, object_status='verified', uploaded_at=:uploaded_at, "
            "migrated_at=:uploaded_at WHERE id=:id"
        ),
        {
            "bucket": stored.bucket,
            "key": stored.key,
            "size": stored.size_bytes,
            "sha": stored.checksum_sha256,
            "uploaded_at": datetime.now(timezone.utc),
            "id": row["id"],
        },
    )


def record_pending_multipart(SessionFactory, submission_id: str, exc: Exception, key: str) -> None:
    upload_id = getattr(exc, "upload_id", None)
    try:
        with SessionFactory() as db:
            submission = db.get(ProjectSubmission, UUID(submission_id))
            if submission is None:
                return
            metadata = dict(submission.portfolio_metadata or {})
            metadata["stratus_orphan_object_key"] = key
            metadata["stratus_orphan_cleanup_required"] = True
            if upload_id:
                metadata["stratus_pending_multipart_upload_id"] = str(upload_id)
                metadata["stratus_pending_object_key"] = key
                metadata["stratus_pending_multipart_cleanup_required"] = True
            submission.portfolio_metadata = metadata
            db.commit()
    except Exception:
        print(
            f"WARNING: Could not persist multipart upload ID for {submission_id}; "
            "retain the error output and reconcile this upload in Catalyst Console.",
            file=sys.stderr,
        )


def print_summary(summary: dict[str, int]) -> None:
    print("\nMigration summary")
    print("-----------------")
    for key in SUMMARY_KEYS:
        print(f"{key}: {summary.get(key, 0):,}")


def run_dry_run(db: Session, rows: list[dict[str, Any]]) -> dict[str, int]:
    summary = {key: 0 for key in SUMMARY_KEYS}
    summary["total_archives_discovered"] = len(rows)
    for row in rows:
        if row["storage_provider"] == "catalyst_stratus" and row["object_status"] == "verified":
            summary["already_migrated"] += 1
            if has_legacy_payload(row):
                summary["bytes_eligible_for_cleanup"] += archive_source_size(
                    db, row["id"], has_inline=bool(row["has_inline"])
                )
        elif has_legacy_payload(row):
            summary["eligible_for_migration"] += 1
        else:
            # Rows without legacy payload and without a verified object need manual review.
            summary["failed_transfers"] += 1
    summary["bytes_still_stored_in_neon"] = read_legacy_bytes_still_in_neon(db)
    return summary


def run_execute(SessionFactory, rows: list[dict[str, Any]], batch_size: int) -> dict[str, int]:
    storage = get_catalyst_storage()
    if storage is None:
        raise RuntimeError("Catalyst is not configured. Set the CATALYST_* server environment variables before --execute.")
    summary = {key: 0 for key in SUMMARY_KEYS}
    summary["total_archives_discovered"] = len(rows)
    candidates = [
        row for row in rows
        if row["storage_provider"] != "catalyst_stratus" or row["object_status"] != "verified"
        if has_legacy_payload(row)
    ]
    summary["already_migrated"] = sum(
        1 for row in rows
        if row["storage_provider"] == "catalyst_stratus" and row["object_status"] == "verified"
    )
    summary["eligible_for_migration"] = len(candidates)
    summary["failed_transfers"] += sum(1 for row in rows if not has_legacy_payload(row) and row["object_status"] != "verified")

    for batch_start in range(0, len(candidates), batch_size):
        for row in candidates[batch_start : batch_start + batch_size]:
            with SessionFactory() as db:
                source = None
                key = f"projects/{UUID(row['id'])}/archive.zip"
                try:
                    source, size, source_digest = source_to_temporary_file(db, row)
                    # Reuse the deterministic key on every retry. upload_stream overwrites
                    # that exact key; verify both the upload receipt and a fresh remote
                    # checksum before committing the Neon reference.
                    stored = storage.upload_stream(key, source, expected_size=size)
                    if stored.checksum_sha256.lower() != source_digest.lower():
                        raise StorageError("Uploaded archive checksum did not match the Neon source.")
                    remote_digest = storage.checksum_object(key)
                    if remote_digest.lower() != source_digest.lower():
                        raise StorageError("Catalyst object checksum did not match the Neon source after upload.")
                    set_migrated_metadata(db, row, stored)
                    db.commit()
                    summary["successfully_transferred"] += 1
                    summary["total_bytes_transferred"] += size
                    print(f"[OK] {row['id']} — {size:,} bytes — {stored.checksum_sha256}")
                except Exception as exc:
                    db.rollback()
                    if isinstance(exc, StorageError) and "checksum" in str(exc).lower():
                        summary["checksum_failures"] += 1
                    record_pending_multipart(SessionFactory, row["id"], exc, key)
                    summary["failed_transfers"] += 1
                    print(f"[FAILED] {row['id']} — {str(exc).replace(chr(10), ' ')[:220]}", file=sys.stderr)
                finally:
                    if source is not None:
                        source.close()
    with SessionFactory() as db:
        summary["bytes_still_stored_in_neon"] = read_legacy_bytes_still_in_neon(db)
        fresh_rows = archive_rows(db)
        summary["bytes_eligible_for_cleanup"] = sum(
            archive_source_size(db, row["id"], has_inline=bool(row["has_inline"]))
            for row in fresh_rows
            if row["storage_provider"] == "catalyst_stratus"
            and row["object_status"] == "verified"
            and has_legacy_payload(row)
        )
    return summary


def run_verify(SessionFactory, rows: list[dict[str, Any]]) -> dict[str, int]:
    storage = get_catalyst_storage()
    if storage is None:
        raise RuntimeError("Catalyst is not configured. Set CATALYST_* variables before --verify.")
    summary = {key: 0 for key in SUMMARY_KEYS}
    summary["total_archives_discovered"] = len(rows)
    for row in rows:
        if row["storage_provider"] != "catalyst_stratus" or row["object_status"] != "verified":
            continue
        summary["already_migrated"] += 1
        ok, reason = verify_row(storage, row)
        if ok:
            print(f"[VERIFIED] {row['id']} — {row['storage_key']}")
            if has_legacy_payload(row):
                with SessionFactory() as db:
                    summary["bytes_eligible_for_cleanup"] += archive_source_size(
                        db, row["id"], has_inline=bool(row["has_inline"])
                    )
        else:
            summary["failed_transfers"] += 1
            if reason == "checksum_mismatch":
                summary["checksum_failures"] += 1
            print(f"[VERIFY FAILED] {row['id']} — {reason}", file=sys.stderr)
    with SessionFactory() as db:
        summary["bytes_still_stored_in_neon"] = read_legacy_bytes_still_in_neon(db)
    return summary


def run_cleanup(SessionFactory, rows: list[dict[str, Any]]) -> dict[str, int]:
    storage = get_catalyst_storage()
    if storage is None:
        raise RuntimeError("Catalyst is not configured. Set CATALYST_* variables before --cleanup.")
    summary = {key: 0 for key in SUMMARY_KEYS}
    summary["total_archives_discovered"] = len(rows)
    for row in rows:
        if row["storage_provider"] != "catalyst_stratus" or row["object_status"] != "verified" or not has_legacy_payload(row):
            continue
        with SessionFactory() as db:
            try:
                ok, reason = verify_row(storage, row)
                if not ok:
                    summary["failed_transfers"] += 1
                    if reason == "checksum_mismatch":
                        summary["checksum_failures"] += 1
                    print(f"[SKIPPED] {row['id']} — {reason}", file=sys.stderr)
                    continue
                size = archive_source_size(db, row["id"], has_inline=bool(row["has_inline"]))
                db.execute(text("UPDATE project_submissions SET zip_bundle=NULL WHERE id=:id"), {"id": row["id"]})
                db.execute(text("DELETE FROM project_submission_zip_chunks WHERE submission_id=:id"), {"id": row["id"]})
                db.commit()
                summary["successfully_transferred"] += 1  # Count records cleaned after fresh verification.
                summary["bytes_eligible_for_cleanup"] += size
                print(f"[CLEANED] {row['id']} — {size:,} Neon bytes removed")
            except Exception as exc:
                db.rollback()
                summary["failed_transfers"] += 1
                print(f"[CLEANUP FAILED] {row['id']} — {str(exc)[:220]}", file=sys.stderr)
    with SessionFactory() as db:
        summary["bytes_still_stored_in_neon"] = read_legacy_bytes_still_in_neon(db)
    return summary


def run_restore(SessionFactory, rows: list[dict[str, Any]]) -> dict[str, int]:
    """Restore verified objects to ordered Neon chunks; keep Stratus objects as rollback copies."""
    # A retained Neon copy can be reactivated without any Catalyst dependency.
    # Catalyst is required only for rows whose old payloads were explicitly cleaned.
    storage = get_catalyst_storage()
    summary = {key: 0 for key in SUMMARY_KEYS}
    summary["total_archives_discovered"] = len(rows)
    candidates = [
        row for row in rows
        if row["storage_provider"] == "catalyst_stratus" and row["object_status"] == "verified"
    ]
    for row in candidates:
        try:
            if not has_legacy_payload(row) and storage is None:
                raise RuntimeError(
                    "Catalyst is not configured; cleaned archives require Stratus to be downloaded for rollback."
                )
            if not has_legacy_payload(row):
                ok, reason = verify_row(storage, row)
                if not ok:
                    raise StorageError(f"Cannot restore {row['id']}: {reason}.")
            with SessionFactory() as db:
                submission = db.get(ProjectSubmission, UUID(row["id"]))
                if submission is None:
                    raise RuntimeError("Submission row was removed during restore.")
                if has_legacy_payload(row):
                    # Before Neon cleanup, the old payload is already a complete rollback copy.
                    submission.storage_provider = "database"
                    submission.object_status = "restored"
                    db.commit()
                    size = int(row.get("file_size_bytes") or row.get("stored_bytes") or 0)
                    print(f"[ROLLED BACK TO EXISTING NEON COPY] {row['id']} — {size:,} bytes")
                else:
                    # After cleanup, rebuild chunk rows from a disk-backed verified download.
                    staged = tempfile.TemporaryFile(mode="w+b")
                    digest = hashlib.sha256()
                    size = 0
                    try:
                        for block in storage.iter_download(row["storage_key"]):
                            staged.write(block)
                            digest.update(block)
                            size += len(block)
                        expected_size = int(row.get("file_size_bytes") or 0)
                        expected_digest = str(row.get("checksum_sha256") or "")
                        if size != expected_size or (expected_digest and digest.hexdigest().lower() != expected_digest.lower()):
                            raise StorageError(f"Restore checksum or size mismatch for {row['id']}.")
                        staged.seek(0)
                        # Re-fetch inside the write transaction and refuse to overwrite any new payload.
                        submission = db.get(ProjectSubmission, UUID(row["id"]))
                        if db.scalar(
                            text("SELECT EXISTS(SELECT 1 FROM project_submission_zip_chunks WHERE submission_id=:id)"),
                            {"id": row["id"]},
                        ) or submission.zip_bundle is not None:
                            raise RuntimeError("Legacy Neon archive data appeared during restore; refusing to overwrite it.")
                        sequence = 0
                        pending: list[ProjectSubmissionZipChunk] = []
                        pending_bytes = 0
                        while True:
                            payload = staged.read(DB_CHUNK_BYTES)
                            if not payload:
                                break
                            pending.append(ProjectSubmissionZipChunk(
                                submission_id=submission.id, sequence=sequence, payload=payload
                            ))
                            pending_bytes += len(payload)
                            sequence += 1
                            if pending_bytes >= DB_FLUSH_BYTES:
                                db.add_all(pending)
                                db.flush()
                                pending.clear()
                                pending_bytes = 0
                        if pending:
                            db.add_all(pending)
                        submission.storage_provider = "database"
                        submission.object_status = "restored"
                        submission.file_size_bytes = size
                        submission.checksum_sha256 = digest.hexdigest()
                        db.commit()
                        print(f"[RESTORED TO NEON] {row['id']} — {size:,} bytes; Stratus copy retained")
                    finally:
                        staged.close()
            summary["successfully_transferred"] += 1
            summary["total_bytes_transferred"] += size
        except Exception as exc:
            summary["failed_transfers"] += 1
            if "checksum" in str(exc).lower():
                summary["checksum_failures"] += 1
            print(f"[RESTORE FAILED] {row['id']} — {str(exc)[:220]}", file=sys.stderr)
    with SessionFactory() as db:
        summary["bytes_still_stored_in_neon"] = read_legacy_bytes_still_in_neon(db)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate CodeLeaf project ZIPs between Neon and Catalyst Stratus")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="read-only plan (default)")
    mode.add_argument("--execute", action="store_true", help="upload archives and update references; keep original Neon bytes")
    mode.add_argument("--verify", action="store_true", help="verify every Stratus reference, size and SHA-256")
    mode.add_argument("--cleanup", action="store_true", help="remove only verified legacy Neon archive payloads")
    mode.add_argument("--restore-neon", action="store_true", help="restore cleaned archive payloads to Neon chunks; keep Stratus copies")
    parser.add_argument("--confirm-cleanup", action="store_true", help="required together with --cleanup")
    parser.add_argument("--confirm-restore", action="store_true", help="required together with --restore-neon")
    parser.add_argument("--batch-size", type=int, default=20, choices=range(1, 101))
    args = parser.parse_args()

    if args.confirm_cleanup and not args.cleanup:
        parser.error("--confirm-cleanup is valid only with --cleanup")
    if args.cleanup and not args.confirm_cleanup:
        parser.error("--cleanup requires the explicit --confirm-cleanup flag")
    if args.confirm_restore and not args.restore_neon:
        parser.error("--confirm-restore is valid only with --restore-neon")
    if args.restore_neon and not args.confirm_restore:
        parser.error("--restore-neon requires the explicit --confirm-restore flag")

    try:
        SessionFactory = database_session_factory()
        with SessionFactory() as db:
            rows = archive_rows(db)
            if args.execute:
                summary = run_execute(SessionFactory, rows, args.batch_size)
            elif args.verify:
                summary = run_verify(SessionFactory, rows)
            elif args.cleanup:
                summary = run_cleanup(SessionFactory, rows)
            elif args.restore_neon:
                summary = run_restore(SessionFactory, rows)
            else:
                summary = run_dry_run(db, rows)
        print_summary(summary)
        if args.cleanup:
            print("Cleanup retains PostgreSQL submission metadata and Stratus object references.")
        if args.restore_neon:
            print("Restored Neon chunks were committed; Stratus object copies were retained.")
        return 1 if summary["failed_transfers"] else 0
    except (RuntimeError, SQLAlchemyError, StorageError) as exc:
        print(f"Migration operation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
