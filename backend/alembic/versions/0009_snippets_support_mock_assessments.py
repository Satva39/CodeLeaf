"""Add persisted code snippets, support triage, and timed mock assessment attempts.

Revision ID: 0009_snippets_support
Revises: 0008_plan_entitlements_usage
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0009_snippets_support"
down_revision = "0008_plan_entitlements_usage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "saved_snippets" not in tables:
        op.create_table(
            "saved_snippets",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("language", sa.String(length=40), nullable=False, server_default="plain"),
            sa.Column("code", sa.Text(), nullable=False),
            sa.Column("byte_size", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("user_id", "name", name="uq_saved_snippets_user_name"),
        )
        op.create_index("ix_saved_snippets_user_id", "saved_snippets", ["user_id"])
        op.create_index("ix_saved_snippets_user_updated", "saved_snippets", ["user_id", "updated_at"])
    if "support_requests" not in tables:
        op.create_table(
            "support_requests",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("subject", sa.String(length=160), nullable=False),
            sa.Column("category", sa.String(length=40), nullable=False, server_default="general"),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
            sa.Column("priority", sa.String(length=20), nullable=False, server_default="standard"),
            sa.Column("plan_at_submission", sa.String(length=40), nullable=False, server_default="free"),
            sa.Column("staff_reply", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_support_requests_user_id", "support_requests", ["user_id"])
        op.create_index("ix_support_requests_status_priority_created", "support_requests", ["status", "priority", "created_at"])
    if "project_milestone_progress" not in tables:
        op.create_table(
            "project_milestone_progress",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("course_slug", sa.String(length=100), nullable=False),
            sa.Column("project_slug", sa.String(length=120), nullable=False),
            sa.Column("milestone_key", sa.String(length=12), nullable=False),
            sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("user_id", "course_slug", "project_slug", "milestone_key", name="uq_project_milestone_user_project_key"),
        )
        op.create_index("ix_project_milestone_progress_user_id", "project_milestone_progress", ["user_id"])
        op.create_index("ix_project_milestone_user_project", "project_milestone_progress", ["user_id", "course_slug", "project_slug"])
    if "mock_assessment_attempts" not in tables:
        op.create_table(
            "mock_assessment_attempts",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("course_id", sa.Uuid(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
            sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("answers_summary", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_mock_assessment_attempts_user_id", "mock_assessment_attempts", ["user_id"])
        op.create_index("ix_mock_assessment_attempts_course_id", "mock_assessment_attempts", ["course_id"])
        op.create_index("ix_mock_assessment_user_course_started", "mock_assessment_attempts", ["user_id", "course_id", "started_at"])


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "mock_assessment_attempts" in tables:
        for name in ("ix_mock_assessment_user_course_started", "ix_mock_assessment_attempts_course_id", "ix_mock_assessment_attempts_user_id"):
            if name in {idx.get("name") for idx in sa.inspect(bind).get_indexes("mock_assessment_attempts")}:
                op.drop_index(name, table_name="mock_assessment_attempts")
        op.drop_table("mock_assessment_attempts")
    if "project_milestone_progress" in tables:
        indexes = {idx.get("name") for idx in sa.inspect(bind).get_indexes("project_milestone_progress")}
        for name in ("ix_project_milestone_user_project", "ix_project_milestone_progress_user_id"):
            if name in indexes:
                op.drop_index(name, table_name="project_milestone_progress")
        op.drop_table("project_milestone_progress")
    if "support_requests" in tables:
        indexes = {idx.get("name") for idx in sa.inspect(bind).get_indexes("support_requests")}
        for name in ("ix_support_requests_status_priority_created", "ix_support_requests_user_id"):
            if name in indexes:
                op.drop_index(name, table_name="support_requests")
        op.drop_table("support_requests")
    if "saved_snippets" in tables:
        indexes = {idx.get("name") for idx in sa.inspect(bind).get_indexes("saved_snippets")}
        for name in ("ix_saved_snippets_user_updated", "ix_saved_snippets_user_id"):
            if name in indexes:
                op.drop_index(name, table_name="saved_snippets")
        op.drop_table("saved_snippets")
