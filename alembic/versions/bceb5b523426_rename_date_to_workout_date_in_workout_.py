"""rename_date_to_workout_date_in_workout_sessions

Revision ID: bceb5b523426
Revises: deb920fb8919
Create Date: 2025-12-15 23:12:29.999991+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bceb5b523426'
down_revision = 'deb920fb8919'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename the 'date' column to 'workout_date' in workout_sessions table
    op.alter_column('workout_sessions', 'date', new_column_name='workout_date')


def downgrade() -> None:
    # Rename back to 'date'
    op.alter_column('workout_sessions', 'workout_date', new_column_name='date')
