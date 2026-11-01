"""Verify Alembic upgrade head can be run twice against a new isolated SQLite DB.

This checks migration graph execution without touching the configured database.
"""
from __future__ import annotations

import os
import subprocess
import sys
from contextlib import closing
import tempfile
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="codeleaf-alembic-repeatability-") as temp:
        database_path = Path(temp) / "alembic-test.sqlite"
        env = os.environ.copy()
        env.update({
            "APP_ENV": "test",
            "JWT_SECRET": "alembic-test-only-secret-not-for-deployment",
            "COOKIE_SECURE": "false",
            "FRONTEND_ORIGINS": "http://localhost:5173",
            "DATABASE_URL": f"sqlite:///{database_path.as_posix()}",
        })
        for pass_number in (1, 2):
            result = subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                cwd=BACKEND_ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode:
                print(result.stdout)
                print(result.stderr, file=sys.stderr)
                raise SystemExit(f"FAIL: alembic upgrade head failed on pass {pass_number}")
            print(f"PASS alembic upgrade head completed on pass {pass_number}")

        # Inspect only the temporary SQLite database, never the user's configured DB.
        import sqlite3
        # sqlite3.Connection.__exit__ commits/rolls back but does not close the
        # underlying file. Explicitly close it before TemporaryDirectory cleanup;
        # Windows cannot unlink an open SQLite file (WinError 32).
        with closing(sqlite3.connect(database_path)) as connection:
            tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            revisions = [row[0] for row in connection.execute("SELECT version_num FROM alembic_version")]
        required = {"courses", "course_modules", "lessons", "exercises", "users", "auth_sessions", "account_action_tokens", "auth_rate_limit_events", "learning_preferences", "review_schedules", "content_revisions", "audit_logs", "product_analytics_events", "runner_jobs", "practical_exam_attempts", "saved_workspaces", "plan_usage", "usage_reservations", "saved_snippets", "support_requests", "project_milestone_progress", "mock_assessment_attempts", "alembic_version", "course_content_bundles"}
        missing = sorted(required - tables)
        if missing:
            raise SystemExit("FAIL: migration left missing tables: " + ", ".join(missing))
        if len(revisions) != 1 or revisions[0] != "0011_course_content_bundles":
            raise SystemExit(f"FAIL: unexpected migration state: {revisions!r}")
        with closing(sqlite3.connect(database_path)) as connection:
            bundle_columns = {
                row[1]: {"type": row[2].upper(), "notnull": bool(row[3]), "pk": int(row[5])}
                for row in connection.execute("PRAGMA table_info(course_content_bundles)")
            }
            expected_bundle_columns = {
                "course_id", "storage_provider", "storage_bucket", "storage_key",
                "checksum_sha256", "compressed_size_bytes", "raw_size_bytes",
                "lesson_count", "schema_version", "object_status", "created_at", "updated_at",
            }
            if set(bundle_columns) != expected_bundle_columns:
                raise SystemExit(
                    "FAIL: course_content_bundles columns differ from revision 0011: "
                    + repr(sorted(set(bundle_columns) ^ expected_bundle_columns))
                )
            if bundle_columns["course_id"]["pk"] != 1 or bundle_columns["course_id"]["notnull"] is not True:
                raise SystemExit("FAIL: course_content_bundles.course_id is not the non-null primary key")
            foreign_keys = list(connection.execute("PRAGMA foreign_key_list(course_content_bundles)"))
            if not any(row[2] == "courses" and row[3] == "course_id" and row[4] == "id" and row[6].upper() == "CASCADE" for row in foreign_keys):
                raise SystemExit("FAIL: course_content_bundles.course_id must cascade to courses.id")
            indexes = list(connection.execute("PRAGMA index_list(course_content_bundles)"))
            index_names = {row[1] for row in indexes}
            if "ix_course_content_bundles_status" not in index_names:
                raise SystemExit("FAIL: course_content_bundles status index is missing")
            unique_storage_key = False
            for index in indexes:
                if index[2]:
                    indexed_columns = [row[2] for row in connection.execute(f'PRAGMA index_info("{index[1]}")')]
                    if indexed_columns == ["storage_key"]:
                        unique_storage_key = True
            if not unique_storage_key:
                raise SystemExit("FAIL: course_content_bundles.storage_key unique constraint is missing")
            print("PASS migration 0011 course_content_bundles columns, UUID course PK/FK, unique key and status index")

        with closing(sqlite3.connect(database_path)) as connection:
            user_columns = {row[1] for row in connection.execute("PRAGMA table_info(users)")}
        if "is_email_verified" not in user_columns:
            raise SystemExit("FAIL: migration left users.is_email_verified missing")
        with closing(sqlite3.connect(database_path)) as connection:
            submission_columns = {row[1] for row in connection.execute("PRAGMA table_info(project_submissions)")}
            runner_columns = {row[1] for row in connection.execute("PRAGMA table_info(runner_jobs)")}
        catalyst_columns = {
            "storage_provider", "storage_bucket", "storage_key", "file_size_bytes",
            "checksum_sha256", "object_status", "uploaded_at", "migrated_at",
        }
        if catalyst_columns - submission_columns:
            raise SystemExit("FAIL: Catalyst archive migration is missing columns: " + ", ".join(sorted(catalyst_columns - submission_columns)))
        if "stored_bytes" not in submission_columns or "request_key" not in runner_columns:
            raise SystemExit("FAIL: plan usage migration did not add storage or runner idempotency columns")
        print("PASS migration state has one 0011 head, Catalyst archive metadata, and all existing auth/review/privacy/practical/plan-usage/snippet/support/mock-assessment tables after repeated upgrades")
    print("Migration repeatability checks passed; only a temporary SQLite database was used.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
