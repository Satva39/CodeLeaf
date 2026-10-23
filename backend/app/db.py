from collections.abc import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from fastapi import HTTPException
from .config import settings


class Base(DeclarativeBase):
    pass


STATEMENT_TIMEOUT_SQL = "SET LOCAL statement_timeout = '8000ms'"


def _engine_options(database_url: str) -> dict:
    """Bound pool/connection waits without sending unsupported options to Neon PgBouncer."""
    options = {"pool_pre_ping": True}
    if database_url.startswith("postgresql+psycopg://"):
        options.update(
            pool_timeout=5,
            connect_args={"connect_timeout": 5},
        )
    return options


def _apply_transaction_statement_timeout(connection) -> None:
    """Bound SQL execution inside each transaction; works with Neon pooled connections.

    Do not pass statement_timeout in libpq's startup `options`: Neon/PgBouncer rejects
    that startup parameter. SET LOCAL is transaction-scoped and is reset automatically
    at transaction end, so it does not leak into another transaction on a pooled socket.
    """
    connection.exec_driver_sql(STATEMENT_TIMEOUT_SQL)


engine = None
SessionLocal = None
if settings.sqlalchemy_database_url and settings.sqlalchemy_database_url.strip():
    engine = create_engine(
        settings.sqlalchemy_database_url,
        **_engine_options(settings.sqlalchemy_database_url),
    )
    if settings.sqlalchemy_database_url.startswith("postgresql+psycopg://"):
        event.listen(engine, "begin", _apply_transaction_statement_timeout)
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, expire_on_commit=False, class_=Session
    )


def get_db() -> Generator[Session, None, None]:
    if SessionLocal is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured. Set DATABASE_URL in backend/.env.",
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
