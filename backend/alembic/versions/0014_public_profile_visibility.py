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

    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("users")}
    if "uq_users_username_lower" not in indexes:
        op.create_index(
            "uq_users_username_lower",
            "users",
            [sa.text("lower(username)")],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("users")}
    if "uq_users_username_lower" in indexes:
        op.drop_index("uq_users_username_lower", table_name="users")
    existing = {column["name"] for column in sa.inspect(bind).get_columns("users")}
    for name in reversed(PUBLIC_COLUMNS):
        if name in existing:
            op.drop_column("users", name)
