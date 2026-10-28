"""Store project ZIP archives for durable portfolio downloads.

Revision ID: 0006_portfolio_zip
Revises: 0005_practical_exam_attempts
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_portfolio_zip"
down_revision = "0005_practical_exam_attempts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("project_submissions")}
    if "zip_bundle" not in columns:
        op.add_column("project_submissions", sa.Column("zip_bundle", sa.LargeBinary(), nullable=True))
    if "zip_filename" not in columns:
        op.add_column("project_submissions", sa.Column("zip_filename", sa.String(length=180), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("project_submissions")}
    if "zip_filename" in columns:
        op.drop_column("project_submissions", "zip_filename")
    if "zip_bundle" in columns:
        op.drop_column("project_submissions", "zip_bundle")
