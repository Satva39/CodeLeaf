"""Add per-course Stratus bundle references for lesson JSON content.

Revision ID: 0011_course_content_bundles
Revises: 0010_catalyst_stratus
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0011_course_content_bundles"
down_revision = "0010_catalyst_stratus"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "course_content_bundles" not in tables:
        op.create_table(
            "course_content_bundles",
            sa.Column(
                "course_id",
                sa.Uuid(as_uuid=True),
                sa.ForeignKey("courses.id", ondelete="CASCADE"),
                primary_key=True,
                nullable=False,
            ),
            sa.Column("storage_provider", sa.String(length=32), nullable=False, server_default="catalyst_stratus"),
            sa.Column("storage_bucket", sa.String(length=120), nullable=False),
            sa.Column("storage_key", sa.String(length=500), nullable=False, unique=True),
            sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
            sa.Column("compressed_size_bytes", sa.BigInteger(), nullable=False),
            sa.Column("raw_size_bytes", sa.BigInteger(), nullable=False),
            sa.Column("lesson_count", sa.Integer(), nullable=False),
            sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("object_status", sa.String(length=24), nullable=False, server_default="pending"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
    indexes = {item["name"] for item in sa.inspect(bind).get_indexes("course_content_bundles")}
    if "ix_course_content_bundles_status" not in indexes:
        op.create_index("ix_course_content_bundles_status", "course_content_bundles", ["object_status"])


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "course_content_bundles" not in tables:
        return
    references = bind.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM course_content_bundles WHERE storage_key IS NOT NULL)")
    ).scalar()
    if references:
        raise RuntimeError(
            "Refusing to drop course_content_bundles while Catalyst lesson bundles are referenced. "
            "Restore lesson content to Neon first, then manually review this downgrade."
        )
    indexes = {item["name"] for item in sa.inspect(bind).get_indexes("course_content_bundles")}
    if "ix_course_content_bundles_status" in indexes:
        op.drop_index("ix_course_content_bundles_status", table_name="course_content_bundles")
    op.drop_table("course_content_bundles")
