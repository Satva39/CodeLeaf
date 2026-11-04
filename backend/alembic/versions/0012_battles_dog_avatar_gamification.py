"""Add coding battles and persistent dog avatar inventory.

Revision ID: 0012_battles_dog_avatar
Revises: 0011_course_content_bundles
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0012_battles_dog_avatar"
down_revision = "0011_course_content_bundles"
branch_labels = None
depends_on = None


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    tables = _tables()
    if "user_avatar_profiles" not in tables:
        op.create_table(
            "user_avatar_profiles",
            sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False),
            sa.Column("breed", sa.String(24), nullable=False, server_default="classic"),
            sa.Column("fur_color", sa.String(24), nullable=False, server_default="golden"),
            sa.Column("eye_color", sa.String(24), nullable=False, server_default="brown"),
            sa.Column("equipment", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
    if "user_achievements" not in tables:
        op.create_table(
            "user_achievements",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("achievement_id", sa.String(80), nullable=False),
            sa.Column("reward_item_id", sa.String(80), nullable=False),
            sa.Column("unlocked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement_once"),
        )
        op.create_index("ix_user_achievements_user_id", "user_achievements", ["user_id"])
        op.create_index("ix_user_achievements_user_unlocked", "user_achievements", ["user_id", "unlocked_at"])
    if "user_avatar_inventory" not in tables:
        op.create_table(
            "user_avatar_inventory",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("item_id", sa.String(80), nullable=False),
            sa.Column("acquired_via", sa.String(30), nullable=False, server_default="achievement"),
            sa.Column("source_achievement_id", sa.String(80), nullable=True),
            sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("user_id", "item_id", name="uq_user_avatar_item_once"),
        )
        op.create_index("ix_user_avatar_inventory_user_id", "user_avatar_inventory", ["user_id"])
    if "coding_battles" not in tables:
        op.create_table(
            "coding_battles",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("challenger_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("opponent_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
            sa.Column("language", sa.String(24), nullable=False),
            sa.Column("difficulty", sa.String(20), nullable=False),
            sa.Column("challenge_id", sa.String(80), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="waiting"),
            sa.Column("winner_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_coding_battles_challenger_id", "coding_battles", ["challenger_id"])
        op.create_index("ix_coding_battles_opponent_id", "coding_battles", ["opponent_id"])
        op.create_index("ix_coding_battles_queue", "coding_battles", ["status", "language", "difficulty", "created_at"])
        op.create_index("ix_coding_battles_players", "coding_battles", ["challenger_id", "opponent_id", "status"])
    if "battle_submissions" not in tables:
        op.create_table(
            "battle_submissions",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("battle_id", sa.Uuid(as_uuid=True), sa.ForeignKey("coding_battles.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("request_key", sa.String(100), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="evaluating"),
            sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("result_summary", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("battle_id", "user_id", "request_key", name="uq_battle_submission_request"),
        )
        op.create_index("ix_battle_submissions_battle_id", "battle_submissions", ["battle_id"])
        op.create_index("ix_battle_submissions_user_id", "battle_submissions", ["user_id"])
        op.create_index("ix_battle_submissions_battle_status", "battle_submissions", ["battle_id", "status"])


def downgrade() -> None:
    bind = op.get_bind()
    tables = _tables()
    if "battle_submissions" in tables:
        op.drop_table("battle_submissions")
    if "coding_battles" in tables:
        op.drop_table("coding_battles")
    if "user_avatar_inventory" in tables:
        op.drop_table("user_avatar_inventory")
    if "user_achievements" in tables:
        op.drop_table("user_achievements")
    if "user_avatar_profiles" in tables:
        op.drop_table("user_avatar_profiles")
