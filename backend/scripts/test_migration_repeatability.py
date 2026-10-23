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
        required = {"courses", "course_modules", "lessons", "exercises", "users", "auth_sessions", "account_action_tokens", "auth_rate_limit_events", "alembic_version"}
        missing = sorted(required - tables)
        if missing:
            raise SystemExit("FAIL: migration left missing tables: " + ", ".join(missing))
        if len(revisions) != 1 or revisions[0] != "0003_auth_lifecycle":
            raise SystemExit(f"FAIL: unexpected migration state: {revisions!r}")
        with closing(sqlite3.connect(database_path)) as connection:
            user_columns = {row[1] for row in connection.execute("PRAGMA table_info(users)")}
        if "is_email_verified" not in user_columns:
            raise SystemExit("FAIL: migration left users.is_email_verified missing")
        print("PASS migration state has one head and all auth lifecycle tables/columns after repeated upgrades")
    print("Migration repeatability checks passed; only a temporary SQLite database was used.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
