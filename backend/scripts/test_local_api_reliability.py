"""Contract tests for local-origin handling and bounded PostgreSQL waits."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import Settings
from app.db import STATEMENT_TIMEOUT_SQL, _apply_transaction_statement_timeout, _engine_options


def main() -> None:
    settings = Settings(
        app_env="development",
        frontend_origins="http://127.0.0.1:5173",
    )
    origins = settings.allowed_origins
    assert "http://127.0.0.1:5173" in origins
    assert "http://localhost:5173" in origins
    assert len(origins) == len(set(origins))
    print("PASS development CORS accepts the two explicit Vite loopback origins")

    postgres = _engine_options("postgresql+psycopg://user:password@localhost:5432/codeleaf")
    assert postgres["pool_timeout"] == 5
    assert postgres["connect_args"]["connect_timeout"] == 5
    assert "options" not in postgres["connect_args"]

    class RecordingConnection:
        statement = None

        def exec_driver_sql(self, statement: str) -> None:
            self.statement = statement

    connection = RecordingConnection()
    _apply_transaction_statement_timeout(connection)
    assert connection.statement == STATEMENT_TIMEOUT_SQL
    assert "SET LOCAL statement_timeout" in STATEMENT_TIMEOUT_SQL
    print("PASS Neon-compatible timeout uses transaction-local SET LOCAL, not startup options")
    print("PASS PostgreSQL pool/connect/query waits are bounded")

    non_postgres = _engine_options("sqlite:///./test.db")
    assert non_postgres == {"pool_pre_ping": True}
    print("PASS non-PostgreSQL test engines do not receive psycopg-specific options")


if __name__ == "__main__":
    main()
