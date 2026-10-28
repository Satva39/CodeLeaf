"""Store project archives in small chunks to support large ZIP uploads.

Revision ID: 0007_portfolio_zip_chunks
Revises: 0006_portfolio_zip
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_portfolio_zip_chunks"
down_revision = "0006_portfolio_zip"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "project_submission_zip_chunks" not in inspector.get_table_names():
        op.create_table(
            "project_submission_zip_chunks",
            sa.Column("submission_id", sa.Uuid(as_uuid=True), nullable=False),
            sa.Column("sequence", sa.Integer(), nullable=False),
            sa.Column("payload", sa.LargeBinary(), nullable=False),
            sa.ForeignKeyConstraint(["submission_id"], ["project_submissions.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("submission_id", "sequence"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    if "project_submission_zip_chunks" in sa.inspect(bind).get_table_names():
        op.drop_table("project_submission_zip_chunks")
