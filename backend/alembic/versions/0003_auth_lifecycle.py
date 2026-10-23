"""Add verified-email state, revocable sessions, one-time action tokens and DB rate limits.

Revision ID: 0003_auth_lifecycle
Revises: 0002_dynamic_gamification

The original 0001 baseline calls metadata.create_all(), so a clean database may
already contain objects introduced by this revision. Every operation is guarded
for both fresh and already-migrated installations.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_auth_lifecycle"
down_revision = "0002_dynamic_gamification"
branch_labels = None
depends_on = None


def _table_names(bind):
    return set(sa.inspect(bind).get_table_names())


def _indexes(bind, table_name):
    return {item["name"] for item in sa.inspect(bind).get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    if "is_email_verified" not in {c["name"] for c in sa.inspect(bind).get_columns("users")}:
        # Existing accounts are treated as verified to avoid unexpected lockouts.
        op.add_column("users", sa.Column("is_email_verified", sa.Boolean(), nullable=False, server_default=sa.true()))

    if "auth_sessions" not in _table_names(bind):
        op.create_table(
            "auth_sessions",
            sa.Column("token_hash", sa.String(length=64), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        )
    for name, columns in (
        ("ix_auth_sessions_user_id", ["user_id"]),
        ("ix_auth_sessions_user_revoked", ["user_id", "revoked_at"]),
    ):
        if name not in _indexes(bind, "auth_sessions"):
            op.create_index(name, "auth_sessions", columns)

    if "account_action_tokens" not in _table_names(bind):
        op.create_table(
            "account_action_tokens",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("token_hash", sa.String(length=64), nullable=False, unique=True),
            sa.Column("purpose", sa.String(length=32), nullable=False),
            sa.Column("target_email", sa.String(length=320), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        )
    for name, columns in (
        ("ix_account_action_tokens_user_id", ["user_id"]),
        ("ix_account_action_tokens_purpose", ["purpose"]),
        ("ix_auth_tokens_user_purpose", ["user_id", "purpose"]),
    ):
        if name not in _indexes(bind, "account_action_tokens"):
            op.create_index(name, "account_action_tokens", columns)

    if "auth_rate_limit_events" not in _table_names(bind):
        op.create_table(
            "auth_rate_limit_events",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("action", sa.String(length=40), nullable=False),
            sa.Column("key_hash", sa.String(length=64), nullable=False),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
    for name, columns in (
        ("ix_auth_rate_limit_events_action", ["action"]),
        ("ix_auth_rate_limit_events_key_hash", ["key_hash"]),
        ("ix_auth_rate_events_key_time", ["key_hash", "occurred_at"]),
    ):
        if name not in _indexes(bind, "auth_rate_limit_events"):
            op.create_index(name, "auth_rate_limit_events", columns)


def downgrade() -> None:
    bind = op.get_bind()
    tables = _table_names(bind)
    if "auth_rate_limit_events" in tables:
        for name in ("ix_auth_rate_events_key_time", "ix_auth_rate_limit_events_key_hash", "ix_auth_rate_limit_events_action"):
            if name in _indexes(bind, "auth_rate_limit_events"):
                op.drop_index(name, table_name="auth_rate_limit_events")
        op.drop_table("auth_rate_limit_events")
    if "account_action_tokens" in tables:
        for name in ("ix_auth_tokens_user_purpose", "ix_account_action_tokens_purpose", "ix_account_action_tokens_user_id"):
            if name in _indexes(bind, "account_action_tokens"):
                op.drop_index(name, table_name="account_action_tokens")
        op.drop_table("account_action_tokens")
    if "auth_sessions" in tables:
        for name in ("ix_auth_sessions_user_revoked", "ix_auth_sessions_user_id"):
            if name in _indexes(bind, "auth_sessions"):
                op.drop_index(name, table_name="auth_sessions")
        op.drop_table("auth_sessions")
    if "users" in _table_names(bind) and "is_email_verified" in {c["name"] for c in sa.inspect(bind).get_columns("users")}:
        op.drop_column("users", "is_email_verified")
