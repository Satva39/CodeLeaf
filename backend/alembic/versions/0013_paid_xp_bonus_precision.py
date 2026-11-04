"""Store awarded XP to two decimal places for paid-plan XP multipliers.

Revision ID: 0013_paid_xp_bonus_precision
Revises: 0012_battles_dog_avatar
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0013_paid_xp_bonus_precision"
down_revision = "0012_battles_dog_avatar"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"]: column for column in sa.inspect(op.get_bind()).get_columns("xp_transactions")}
    if "awarded_points" not in columns:
        raise RuntimeError("xp_transactions.awarded_points is required for the XP precision migration")
    with op.batch_alter_table("xp_transactions", recreate="auto") as batch_op:
        batch_op.alter_column(
            "awarded_points",
            existing_type=sa.Integer(),
            type_=sa.Numeric(12, 2),
            existing_nullable=False,
        )


def downgrade() -> None:
    # Downgrading necessarily discards fractional bonus amounts; existing integer
    # balances and all transaction rows remain present. Round to the nearest point.
    with op.batch_alter_table("xp_transactions", recreate="auto") as batch_op:
        batch_op.alter_column(
            "awarded_points",
            existing_type=sa.Numeric(12, 2),
            type_=sa.Integer(),
            existing_nullable=False,
            postgresql_using="ROUND(awarded_points)::INTEGER",
        )
