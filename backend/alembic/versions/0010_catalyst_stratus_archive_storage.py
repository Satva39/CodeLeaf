"""Add metadata references for project archives stored outside PostgreSQL.

Revision ID: 0010_catalyst_stratus
Revises: 0009_snippets_support
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0010_catalyst_stratus"
down_revision = "0009_snippets_support"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("project_submissions")}
    additions = [
        sa.Column("storage_provider", sa.String(length=32), nullable=False, server_default="database"),
        sa.Column("storage_bucket", sa.String(length=120), nullable=True),
        sa.Column("storage_key", sa.String(length=500), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=True),
        sa.Column("object_status", sa.String(length=24), nullable=False, server_default="legacy"),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("migrated_at", sa.DateTime(timezone=True), nullable=True),
    ]
    for column in additions:
        if column.name not in columns:
            op.add_column("project_submissions", column)

    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("project_submissions")}
    if "ix_project_submissions_storage_provider_status" not in indexes:
        op.create_index(
            "ix_project_submissions_storage_provider_status",
            "project_submissions",
            ["storage_provider", "object_status"],
        )
    # Existing size metadata is cheap to reuse; don't scan/read every deferred bytea value.
    op.execute(
        sa.text(
            "UPDATE project_submissions SET file_size_bytes = stored_bytes "
            "WHERE file_size_bytes IS NULL AND stored_bytes > 0"
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    if "project_submissions" not in sa.inspect(bind).get_table_names():
        return
    columns = {column["name"] for column in sa.inspect(bind).get_columns("project_submissions")}
    if {"storage_provider", "storage_key"}.issubset(columns):
        external_objects = bind.execute(
            sa.text(
                "SELECT EXISTS (SELECT 1 FROM project_submissions "
                "WHERE storage_provider <> 'database' OR storage_key IS NOT NULL)"
            )
        ).scalar()
        if external_objects:
            raise RuntimeError(
                "Refusing to downgrade Catalyst storage metadata while project rows still reference external objects. "
                "Restore those archives to Neon first, then retry the downgrade."
            )
    indexes = {index["name"] for index in sa.inspect(bind).get_indexes("project_submissions")}
    if "ix_project_submissions_storage_provider_status" in indexes:
        op.drop_index("ix_project_submissions_storage_provider_status", table_name="project_submissions")
    columns = {column["name"] for column in sa.inspect(bind).get_columns("project_submissions")}
    for name in (
        "migrated_at",
        "uploaded_at",
        "object_status",
        "checksum_sha256",
        "file_size_bytes",
        "storage_key",
        "storage_bucket",
        "storage_provider",
    ):
        if name in columns:
            op.drop_column("project_submissions", name)
