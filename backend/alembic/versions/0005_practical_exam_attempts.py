"""Add persisted practical-exam attempts tied to MCQ attempts.

Revision ID: 0005_practical_exam_attempts
Revises: 0004_phase5_capabilities
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_practical_exam_attempts"
down_revision = "0004_phase5_capabilities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "practical_exam_attempts" not in tables:
        op.create_table(
            "practical_exam_attempts",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
            sa.Column("mcq_attempt_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exam_attempts.id", ondelete="CASCADE"), nullable=False),
            sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("answers_summary", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        )
        inspector = sa.inspect(bind)
        tables = set(inspector.get_table_names())
    indexes = {idx["name"] for idx in sa.inspect(bind).get_indexes("practical_exam_attempts")} if "practical_exam_attempts" in tables else set()
    for name, column in (
        ("ix_practical_exam_attempts_user_id", "user_id"),
        ("ix_practical_exam_attempts_course_id", "course_id"),
        ("ix_practical_exam_attempts_mcq_attempt_id", "mcq_attempt_id"),
    ):
        if name not in indexes:
            op.create_index(name, "practical_exam_attempts", [column])


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "practical_exam_attempts" in tables:
        indexes = {idx["name"] for idx in sa.inspect(bind).get_indexes("practical_exam_attempts")}
        for name in (
            "ix_practical_exam_attempts_user_id",
            "ix_practical_exam_attempts_course_id",
            "ix_practical_exam_attempts_mcq_attempt_id",
        ):
            if name in indexes:
                op.drop_index(name, table_name="practical_exam_attempts")
        op.drop_table("practical_exam_attempts")
