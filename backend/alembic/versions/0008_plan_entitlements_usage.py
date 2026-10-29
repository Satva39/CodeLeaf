"""Add centralized plan usage, saved workspaces and storage/idempotency metadata.

Revision ID: 0008_plan_entitlements_usage
Revises: 0007_portfolio_zip_chunks
"""
from __future__ import annotations

import json
from alembic import op
import sqlalchemy as sa

revision = "0008_plan_entitlements_usage"
down_revision = "0007_portfolio_zip_chunks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "exercises" in tables:
        columns = {column["name"] for column in inspector.get_columns("exercises")}
        if "is_premium" not in columns:
            op.add_column(
                "exercises",
                sa.Column("is_premium", sa.Boolean(), nullable=False, server_default=sa.false()),
            )

    if "project_submissions" in tables:
        columns = {column["name"] for column in inspector.get_columns("project_submissions")}
        if "stored_bytes" not in columns:
            op.add_column(
                "project_submissions",
                sa.Column("stored_bytes", sa.Integer(), nullable=False, server_default="0"),
            )
        # Account for legacy chunked and inline ZIPs without selecting large binary values.
        tables = set(sa.inspect(bind).get_table_names())
        if "project_submission_zip_chunks" in tables:
            bind.execute(sa.text("""
                UPDATE project_submissions
                SET stored_bytes =
                    COALESCE(length(zip_bundle), 0) +
                    COALESCE((
                        SELECT SUM(length(chunk.payload))
                        FROM project_submission_zip_chunks AS chunk
                        WHERE chunk.submission_id = project_submissions.id
                    ), 0)
            """))
        else:
            bind.execute(sa.text("UPDATE project_submissions SET stored_bytes = COALESCE(length(zip_bundle), 0)"))

        # Existing JSON code bundles are small by the existing request contract. Add their
        # encoded size to the archive total so they count toward the same storage allowance.
        rows = bind.execute(sa.text("SELECT id, code_bundle FROM project_submissions")).mappings().all()
        for row in rows:
            code_bundle = row["code_bundle"]
            if isinstance(code_bundle, str):
                try:
                    code_bundle = json.loads(code_bundle)
                except json.JSONDecodeError:
                    code_bundle = {"legacy_text": code_bundle}
            if code_bundle:
                encoded_size = len(json.dumps(code_bundle, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
                bind.execute(
                    sa.text("UPDATE project_submissions SET stored_bytes = stored_bytes + :size WHERE id = :id"),
                    {"size": encoded_size, "id": row["id"]},
                )

    if "runner_jobs" in tables:
        columns = {column["name"] for column in inspector.get_columns("runner_jobs")}
        if "request_key" not in columns:
            op.add_column("runner_jobs", sa.Column("request_key", sa.String(length=100), nullable=True))
        constraints = {item.get("name") for item in sa.inspect(bind).get_unique_constraints("runner_jobs")}
        indexes = {item.get("name") for item in sa.inspect(bind).get_indexes("runner_jobs")}
        if "uq_runner_user_request_key" not in constraints and "uq_runner_user_request_key" not in indexes:
            op.create_unique_constraint("uq_runner_user_request_key", "runner_jobs", ["user_id", "request_key"])

    if "saved_workspaces" not in tables:
        op.create_table(
            "saved_workspaces",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("language", sa.String(length=40), nullable=False, server_default="plain"),
            sa.Column("files", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
            sa.Column("byte_size", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_saved_workspaces_user_id", "saved_workspaces", ["user_id"])

    if "plan_usage" not in tables:
        op.create_table(
            "plan_usage",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("metric", sa.String(length=60), nullable=False),
            sa.Column("window_start", sa.Date(), nullable=False),
            sa.Column("used_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("user_id", "metric", "window_start", name="uq_plan_usage_user_metric_day"),
        )
        op.create_index("ix_plan_usage_user_id", "plan_usage", ["user_id"])
        op.create_index("ix_plan_usage_metric_day", "plan_usage", ["metric", "window_start"])

    if "usage_reservations" not in tables:
        op.create_table(
            "usage_reservations",
            sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Uuid(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("metric", sa.String(length=60), nullable=False),
            sa.Column("window_start", sa.Date(), nullable=False),
            sa.Column("idempotency_key", sa.String(length=140), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="reserved"),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint("user_id", "metric", "idempotency_key", name="uq_usage_reservation_idempotency"),
        )
        op.create_index("ix_usage_reservations_user_id", "usage_reservations", ["user_id"])
        op.create_index("ix_usage_reservations_window", "usage_reservations", ["user_id", "metric", "window_start", "status"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "usage_reservations" in tables:
        indexes = {item.get("name") for item in inspector.get_indexes("usage_reservations")}
        if "ix_usage_reservations_window" in indexes:
            op.drop_index("ix_usage_reservations_window", table_name="usage_reservations")
        if "ix_usage_reservations_user_id" in indexes:
            op.drop_index("ix_usage_reservations_user_id", table_name="usage_reservations")
        op.drop_table("usage_reservations")
    if "plan_usage" in tables:
        indexes = {item.get("name") for item in inspector.get_indexes("plan_usage")}
        if "ix_plan_usage_metric_day" in indexes:
            op.drop_index("ix_plan_usage_metric_day", table_name="plan_usage")
        if "ix_plan_usage_user_id" in indexes:
            op.drop_index("ix_plan_usage_user_id", table_name="plan_usage")
        op.drop_table("plan_usage")
    if "saved_workspaces" in tables:
        indexes = {item.get("name") for item in inspector.get_indexes("saved_workspaces")}
        if "ix_saved_workspaces_user_id" in indexes:
            op.drop_index("ix_saved_workspaces_user_id", table_name="saved_workspaces")
        op.drop_table("saved_workspaces")
    if "runner_jobs" in tables:
        constraints = {item.get("name") for item in sa.inspect(bind).get_unique_constraints("runner_jobs")}
        if "uq_runner_user_request_key" in constraints:
            op.drop_constraint("uq_runner_user_request_key", "runner_jobs", type_="unique")
        columns = {column["name"] for column in sa.inspect(bind).get_columns("runner_jobs")}
        if "request_key" in columns:
            op.drop_column("runner_jobs", "request_key")
    if "project_submissions" in tables:
        columns = {column["name"] for column in sa.inspect(bind).get_columns("project_submissions")}
        if "stored_bytes" in columns:
            op.drop_column("project_submissions", "stored_bytes")
    if "exercises" in tables:
        columns = {column["name"] for column in sa.inspect(bind).get_columns("exercises")}
        if "is_premium" in columns:
            op.drop_column("exercises", "is_premium")
