"""Add opt-in public-profile visibility settings.

Revision ID: 0014_public_profile_visibility
Revises: 0013_paid_xp_bonus_precision
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0014_public_profile_visibility"
down_revision = "0013_paid_xp_bonus_precision"
branch_labels = None
depends_on = None


PUBLIC_COLUMNS = (
    "public_profile_enabled",
    "public_show_xp",
    "public_show_streak",
    "public_show_certificates",
    "public_show_achievements",
    "public_show_progress",
)


USERNAME_INDEX = "uq_users_username_lower"


def _username_index_exists(bind: sa.engine.Connection) -> bool:
    """Check expression indexes without relying on SQLite's incomplete reflection."""
    dialect = bind.dialect.name
    if dialect == "sqlite":
        return bind.execute(
            sa.text("SELECT 1 FROM sqlite_master WHERE type = 'index' AND name = :name LIMIT 1"),
            {"name": USERNAME_INDEX},
        ).first() is not None
    if dialect == "postgresql":
        return bind.execute(
            sa.text(
                "SELECT 1 FROM pg_indexes "
                "WHERE schemaname = ANY (current_schemas(false)) AND indexname = :name LIMIT 1"
            ),
            {"name": USERNAME_INDEX},
        ).first() is not None
    return any(
        index.get("name") == USERNAME_INDEX
        for index in sa.inspect(bind).get_indexes("users")
    )


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "users" not in inspector.get_table_names():
        raise RuntimeError("The users table is required before public-profile settings can be added.")

    existing = {column["name"] for column in inspector.get_columns("users")}
    for name in PUBLIC_COLUMNS:
        if name not in existing:
            op.add_column(
                "users",
                sa.Column(name, sa.Boolean(), nullable=False, server_default=sa.false()),
            )

    # Preserve every existing username. If historical data contains case-only
    # duplicates, stop with a useful message rather than silently renaming accounts.
    duplicate = bind.execute(sa.text(
        "SELECT lower(username) FROM users GROUP BY lower(username) HAVING COUNT(*) > 1 LIMIT 1"
    )).first()
    if duplicate:
        raise RuntimeError(
            "Cannot create case-insensitive username uniqueness: existing accounts contain "
            f"case-only duplicate username '{duplicate[0]}'. Resolve that collision without "
            "deleting accounts, then rerun this migration."
        )

    # The baseline migration creates this model-level expression index as part of
    # Base.metadata.create_all(). SQLite does not report expression indexes from
    # Inspector.get_indexes(), so a plain inspector check would try to create the
    # already-existing index and fail every fresh CI migration.
    if not _username_index_exists(bind):
        op.create_index(
            USERNAME_INDEX,
            "users",
            [sa.text("lower(username)")],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    # Keep the case-insensitive username index: it is also part of the canonical
    # User SQLAlchemy metadata and may have been created by revision 0001. This
    # visibility migration must not remove a pre-existing account uniqueness rule.
    existing = {column["name"] for column in sa.inspect(bind).get_columns("users")}
    for name in reversed(PUBLIC_COLUMNS):
        if name in existing:
            op.drop_column("users", name)
