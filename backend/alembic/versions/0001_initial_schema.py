"""Create CodeLeaf tables from the registered SQLAlchemy metadata.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-10-10

This compact baseline migration is suitable for the starter schema. Review and
replace it with explicit operations before long-lived production schema changes.
"""

from alembic import op
from app.db import Base
from app import models  # noqa: F401 - registers all tables
from app.main import PUBLIC_COURSES
from app.models import Course
from sqlalchemy import select
from sqlalchemy.orm import Session

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)
    with Session(bind=bind) as session:
        for index, item in enumerate(PUBLIC_COURSES):
            row = session.scalar(select(Course).where(Course.slug == item["slug"]))
            if row is None:
                session.add(
                    Course(
                        slug=item["slug"],
                        title=item["title"],
                        description=item["description"],
                        category=item["category"],
                        level=item["level"],
                        published=False,
                        sort_order=index,
                    )
                )
        session.commit()


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
