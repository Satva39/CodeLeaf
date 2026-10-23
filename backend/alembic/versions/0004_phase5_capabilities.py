"""Add Phase 5 learning, portfolio, content-studio and privacy analytics records.

Revision ID: 0004_phase5_capabilities
Revises: 0003_auth_lifecycle

Idempotent because the starter baseline migration creates registered metadata on
fresh installations. Existing databases receive only missing columns/tables.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_phase5_capabilities"
down_revision = "0003_auth_lifecycle"
branch_labels = None
depends_on = None


def _tables(bind):
    return set(sa.inspect(bind).get_table_names())


def _columns(bind, table):
    return {col["name"] for col in sa.inspect(bind).get_columns(table)} if table in _tables(bind) else set()


def _indexes(bind, table):
    return {item["name"] for item in sa.inspect(bind).get_indexes(table)} if table in _tables(bind) else set()


def _index(bind, name, table, columns, unique=False):
    if name not in _indexes(bind, table):
        op.create_index(name, table, columns, unique=unique)


def upgrade() -> None:
    bind = op.get_bind()
    tables = _tables(bind)
    if "role" not in _columns(bind, "users"):
        op.add_column("users", sa.Column("role", sa.String(length=20), nullable=False, server_default="learner"))
    if "portfolio_metadata" not in _columns(bind, "project_submissions"):
        op.add_column("project_submissions", sa.Column("portfolio_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))

    if "learning_preferences" not in tables:
        op.create_table(
            "learning_preferences",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("timezone_name", sa.String(80), nullable=False, server_default="UTC"),
            sa.Column("review_frequency_days", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("daily_review_limit", sa.Integer(), nullable=False, server_default="10"),
            sa.Column("analytics_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
    _index(bind, "ix_learning_preferences_user_id", "learning_preferences", ["user_id"])

    if "review_schedules" not in tables:
        op.create_table(
            "review_schedules",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("course_slug", sa.String(100), nullable=False),
            sa.Column("item_type", sa.String(20), nullable=False),
            sa.Column("item_slug", sa.String(180), nullable=False),
            sa.Column("interval_days", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("ease_factor", sa.Float(), nullable=False, server_default="2.3"),
            sa.Column("repetitions", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_result", sa.String(20), nullable=False, server_default="unknown"),
            sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("due_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("dismissed_until", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("user_id", "course_slug", "item_type", "item_slug", name="uq_review_item_per_user"),
        )
    _index(bind, "ix_review_schedules_user_id", "review_schedules", ["user_id"])
    _index(bind, "ix_review_schedules_due_at", "review_schedules", ["due_at"])

    if "content_revisions" not in tables:
        op.create_table(
            "content_revisions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("course_slug", sa.String(100), nullable=False),
            sa.Column("content_type", sa.String(30), nullable=False),
            sa.Column("content_slug", sa.String(180), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
            sa.Column("content_json", sa.JSON(), nullable=False),
            sa.Column("validation_report", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("review_feedback", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
            sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("published_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
            sa.UniqueConstraint("course_slug", "content_type", "content_slug", "version", name="uq_content_revision_version"),
        )
    _index(bind, "ix_content_revisions_course_slug", "content_revisions", ["course_slug"])
    _index(bind, "ix_content_revisions_status", "content_revisions", ["status"])

    if "audit_logs" not in tables:
        op.create_table(
            "audit_logs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("action", sa.String(80), nullable=False),
            sa.Column("resource_type", sa.String(40), nullable=False),
            sa.Column("resource_id", sa.String(180), nullable=False),
            sa.Column("details", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
    _index(bind, "ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    _index(bind, "ix_audit_logs_action", "audit_logs", ["action"])
    _index(bind, "ix_audit_logs_created_at", "audit_logs", ["created_at"])

    if "product_analytics_events" not in tables:
        op.create_table(
            "product_analytics_events",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("event_type", sa.String(40), nullable=False),
            sa.Column("course_slug", sa.String(100), nullable=True),
            sa.Column("lesson_slug", sa.String(180), nullable=True),
            sa.Column("item_key", sa.String(180), nullable=True),
            sa.Column("outcome", sa.String(30), nullable=True),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
    _index(bind, "ix_product_analytics_events_event_type", "product_analytics_events", ["event_type"])
    _index(bind, "ix_product_analytics_events_course_slug", "product_analytics_events", ["course_slug"])
    _index(bind, "ix_product_analytics_events_occurred_at", "product_analytics_events", ["occurred_at"])

    if "runner_jobs" not in tables:
        op.create_table(
            "runner_jobs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("external_job_id", sa.String(80), nullable=False, unique=True),
            sa.Column("language", sa.String(20), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
            sa.Column("result_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
    _index(bind, "ix_runner_jobs_user_id", "runner_jobs", ["user_id"])


def downgrade() -> None:
    bind = op.get_bind()
    tables = _tables(bind)
    index_tables = {
        "runner_jobs": ["ix_runner_jobs_user_id"],
        "product_analytics_events": ["ix_product_analytics_events_occurred_at", "ix_product_analytics_events_course_slug", "ix_product_analytics_events_event_type"],
        "audit_logs": ["ix_audit_logs_created_at", "ix_audit_logs_action", "ix_audit_logs_actor_user_id"],
        "content_revisions": ["ix_content_revisions_status", "ix_content_revisions_course_slug"],
        "review_schedules": ["ix_review_schedules_due_at", "ix_review_schedules_user_id"],
        "learning_preferences": ["ix_learning_preferences_user_id"],
    }
    for table, indexes in index_tables.items():
        if table in tables:
            existing = _indexes(bind, table)
            for name in indexes:
                if name in existing:
                    op.drop_index(name, table_name=table)
    for table in ("runner_jobs", "product_analytics_events", "audit_logs", "content_revisions", "review_schedules", "learning_preferences"):
        if table in _tables(bind):
            op.drop_table(table)
    if "portfolio_metadata" in _columns(bind, "project_submissions"):
        op.drop_column("project_submissions", "portfolio_metadata")
    if "role" in _columns(bind, "users"):
        op.drop_column("users", "role")
