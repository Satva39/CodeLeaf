"""Add exercise completion and learner-local daily activity tables.

Revision ID: 0002_dynamic_gamification
Revises: 0001_initial_schema
"""

from alembic import op
from app import models  # noqa: F401 - ensure metadata is registered
from app.models import Exercise, ExerciseProgress, UserActivityDay

revision = "0002_dynamic_gamification"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The starter's original 0001 migration uses metadata.create_all(). checkfirst=True
    # supports both existing installations and brand-new databases consistently.
    bind = op.get_bind()
    Exercise.__table__.create(bind=bind, checkfirst=True)
    ExerciseProgress.__table__.create(bind=bind, checkfirst=True)
    UserActivityDay.__table__.create(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    UserActivityDay.__table__.drop(bind=bind, checkfirst=True)
    ExerciseProgress.__table__.drop(bind=bind, checkfirst=True)
    Exercise.__table__.drop(bind=bind, checkfirst=True)
