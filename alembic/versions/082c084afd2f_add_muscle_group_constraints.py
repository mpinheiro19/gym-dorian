"""add_muscle_group_constraints

Revision ID: 082c084afd2f
Revises: 6d038ccb729f
Create Date: 2025-12-20 22:54:09.704967+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '082c084afd2f'
down_revision = '6d038ccb729f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Valid muscle groups
    valid_muscles = [
        'Chest', 'Back', 'Shoulders', 'Biceps', 'Triceps', 'Forearms',
        'Quadriceps', 'Hamstrings', 'Glutes', 'Calves', 'Abdominals', 'Lower Back'
    ]

    # Migrate existing data to use valid muscle groups
    # Map old values to new valid values
    muscle_mapping = {
        'Legs': 'Quadriceps',  # Default legs exercises to Quadriceps
        'Arms': 'Biceps',      # Default arms to Biceps
        'Core': 'Abdominals',  # Default core to Abdominals
    }

    # Update agonist_muscle_group
    for old_value, new_value in muscle_mapping.items():
        op.execute(f"""
            UPDATE exercises
            SET agonist_muscle_group = '{new_value}'
            WHERE agonist_muscle_group = '{old_value}';
        """)

    # Update synergist_muscle_group
    for old_value, new_value in muscle_mapping.items():
        op.execute(f"""
            UPDATE exercises
            SET synergist_muscle_group = '{new_value}'
            WHERE synergist_muscle_group = '{old_value}';
        """)

    # Add CHECK constraint for agonist_muscle_group
    op.execute(f"""
        ALTER TABLE exercises
        ADD CONSTRAINT check_agonist_muscle_group
        CHECK (
            agonist_muscle_group IS NULL OR
            agonist_muscle_group IN ({', '.join(f"'{m}'" for m in valid_muscles)})
        );
    """)

    # Add CHECK constraint for synergist_muscle_group
    # Note: synergist can be NULL or a comma-separated list of valid muscle groups
    op.execute(f"""
        ALTER TABLE exercises
        ADD CONSTRAINT check_synergist_muscle_group
        CHECK (
            synergist_muscle_group IS NULL OR
            synergist_muscle_group IN ({', '.join(f"'{m}'" for m in valid_muscles)})
        );
    """)


def downgrade() -> None:
    # Remove CHECK constraints
    op.execute("ALTER TABLE exercises DROP CONSTRAINT IF EXISTS check_synergist_muscle_group;")
    op.execute("ALTER TABLE exercises DROP CONSTRAINT IF EXISTS check_agonist_muscle_group;")
