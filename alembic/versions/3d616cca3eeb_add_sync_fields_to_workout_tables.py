"""add_sync_fields_to_workout_tables

Adds client_uuid (for offline-first sync) plus created_at/updated_at
timestamps to workout_sessions, log_exercises and log_sets.

Migration strategy (safe for tables with existing data):
  1. Add columns as NULLABLE
  2. Backfill existing rows with generated UUIDs and NOW()
  3. Alter columns to NOT NULL
  4. Create UNIQUE index on client_uuid columns

Revision ID: 3d616cca3eeb
Revises: 5ea4d898b3f0
Create Date: 2026-03-08 22:11:23.783110+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


# revision identifiers, used by Alembic.
revision = '3d616cca3eeb'
down_revision = '5ea4d898b3f0'
branch_labels = None
depends_on = None

_TABLES = ['workout_sessions', 'log_exercises', 'log_sets']


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # Step 1 – Add columns as nullable so ALTER succeeds on non-empty tables
    # ------------------------------------------------------------------ #
    for table in _TABLES:
        op.add_column(table, sa.Column('created_at', sa.DateTime(timezone=True), nullable=True))
        op.add_column(table, sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
        op.add_column(table, sa.Column('client_uuid', sa.Uuid(as_uuid=False), nullable=True))

    # ------------------------------------------------------------------ #
    # Step 2 – Backfill existing rows
    #   - timestamps: set to NOW()
    #   - client_uuid: generate a v4 UUID per row using gen_random_uuid()
    #     (available in PostgreSQL 9.4+ via pgcrypto / core)
    # ------------------------------------------------------------------ #
    conn = op.get_bind()
    for table in _TABLES:
        conn.execute(
            sa.text(
                f"UPDATE {table} "
                f"SET created_at = NOW(), "
                f"    updated_at = NOW(), "
                f"    client_uuid = gen_random_uuid() "
                f"WHERE created_at IS NULL"
            )
        )

    # ------------------------------------------------------------------ #
    # Step 3 – Alter columns to NOT NULL now that every row has a value
    # ------------------------------------------------------------------ #
    for table in _TABLES:
        op.alter_column(table, 'created_at',
                        existing_type=sa.DateTime(timezone=True),
                        server_default=sa.text('now()'),
                        nullable=False)
        op.alter_column(table, 'updated_at',
                        existing_type=sa.DateTime(timezone=True),
                        server_default=sa.text('now()'),
                        nullable=False)
        op.alter_column(table, 'client_uuid',
                        existing_type=sa.Uuid(as_uuid=False),
                        nullable=False)

    # ------------------------------------------------------------------ #
    # Step 4 – Create UNIQUE indexes on client_uuid
    # ------------------------------------------------------------------ #
    op.create_index(op.f('ix_log_exercises_client_uuid'), 'log_exercises', ['client_uuid'], unique=True)
    op.create_index(op.f('ix_log_sets_client_uuid'), 'log_sets', ['client_uuid'], unique=True)
    op.create_index(op.f('ix_workout_sessions_client_uuid'), 'workout_sessions', ['client_uuid'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_workout_sessions_client_uuid'), table_name='workout_sessions')
    op.drop_index(op.f('ix_log_sets_client_uuid'), table_name='log_sets')
    op.drop_index(op.f('ix_log_exercises_client_uuid'), table_name='log_exercises')

    for table in _TABLES:
        op.drop_column(table, 'client_uuid')
        op.drop_column(table, 'updated_at')
        op.drop_column(table, 'created_at')
