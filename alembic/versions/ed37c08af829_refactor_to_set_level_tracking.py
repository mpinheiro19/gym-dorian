"""refactor_to_set_level_tracking

Revision ID: ed37c08af829
Revises: aaa71891ebea
Create Date: 2025-12-17 01:48:08.145475+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ed37c08af829'
down_revision = 'aaa71891ebea'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 0: Drop existing views that depend on aggregate columns
    # These will be recreated in the next migration with updated queries
    # Note: CASCADE only works in PostgreSQL, for SQLite we just drop if exists
    bind = op.get_bind()
    if bind.engine.name == 'postgresql':
        op.execute("DROP VIEW IF EXISTS exercise_frequency CASCADE;")
        op.execute("DROP VIEW IF EXISTS user_workout_summary CASCADE;")
        op.execute("DROP VIEW IF EXISTS muscle_group_distribution CASCADE;")
        op.execute("DROP MATERIALIZED VIEW IF EXISTS personal_records CASCADE;")
        op.execute("DROP MATERIALIZED VIEW IF EXISTS workout_volume_by_month CASCADE;")
        op.execute("DROP MATERIALIZED VIEW IF EXISTS workout_volume_by_week CASCADE;")
        op.execute("DROP MATERIALIZED VIEW IF EXISTS user_exercise_progress_weekly CASCADE;")
    else:
        # SQLite doesn't have materialized views, only regular views
        op.execute("DROP VIEW IF EXISTS exercise_frequency;")
        op.execute("DROP VIEW IF EXISTS user_workout_summary;")
        op.execute("DROP VIEW IF EXISTS muscle_group_distribution;")
        op.execute("DROP VIEW IF EXISTS personal_records;")
        op.execute("DROP VIEW IF EXISTS workout_volume_by_month;")
        op.execute("DROP VIEW IF EXISTS workout_volume_by_week;")
        op.execute("DROP VIEW IF EXISTS user_exercise_progress_weekly;")

    # Step 1: Create log_sets table
    op.create_table(
        'log_sets',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('log_exercise_id', sa.Integer(), nullable=False),
        sa.Column('set_number', sa.Integer(), nullable=False),
        sa.Column('reps', sa.Integer(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('rpe', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('rest_time_seconds', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['log_exercise_id'], ['log_exercises.id'], ondelete='CASCADE'),
    )

    # Step 2: Create indexes
    op.create_index('idx_log_sets_log_exercise_id', 'log_sets', ['log_exercise_id'])
    op.create_index('idx_log_sets_composite', 'log_sets', ['log_exercise_id', 'set_number'])

    # Step 3: Create unique constraint
    op.create_unique_constraint('uq_log_sets_exercise_set', 'log_sets', ['log_exercise_id', 'set_number'])

    # Step 4: Migrate existing data - create synthetic sets from aggregates
    # Different approach for PostgreSQL vs SQLite
    if bind.engine.name == 'postgresql':
        # PostgreSQL: Use generate_series for efficient bulk insert
        op.execute("""
            INSERT INTO log_sets (log_exercise_id, set_number, reps, weight, rpe, notes, rest_time_seconds)
            SELECT
                le.id as log_exercise_id,
                s.set_number,
                -- Distribute total_reps evenly across sets
                CASE
                    WHEN s.set_number < le.sets_completed THEN
                        CAST(le.total_reps / le.sets_completed AS INTEGER)
                    ELSE
                        -- Last set gets remainder reps
                        le.total_reps - (CAST(le.total_reps / le.sets_completed AS INTEGER) * (le.sets_completed - 1))
                END as reps,
                -- Use top_weight for all sets (we don't have per-set data)
                le.top_weight as weight,
                NULL as rpe,
                NULL as notes,
                NULL as rest_time_seconds
            FROM log_exercises le
            CROSS JOIN generate_series(1, GREATEST(le.sets_completed, 1)) as s(set_number)
            WHERE le.sets_completed > 0
            ORDER BY le.id, s.set_number;
        """)

        # Handle edge case - exercises with 0 sets or NULL (create 1 synthetic set)
        op.execute("""
            INSERT INTO log_sets (log_exercise_id, set_number, reps, weight, rpe, notes, rest_time_seconds)
            SELECT
                id as log_exercise_id,
                1 as set_number,
                COALESCE(total_reps, 0) as reps,
                COALESCE(top_weight, 0.0) as weight,
                NULL as rpe,
                NULL as notes,
                NULL as rest_time_seconds
            FROM log_exercises
            WHERE sets_completed = 0 OR sets_completed IS NULL;
        """)
    else:
        # SQLite: Use Python loop to insert sets (SQLite doesn't have generate_series)
        from sqlalchemy import text

        # Fetch all log_exercises with their aggregate data
        connection = bind
        result = connection.execute(text("""
            SELECT id, sets_completed, total_reps, top_weight
            FROM log_exercises
        """))

        log_exercises = result.fetchall()

        # Insert sets for each log_exercise
        for log_ex in log_exercises:
            log_ex_id, sets_completed, total_reps, top_weight = log_ex

            # Handle None/NULL values
            sets_completed = sets_completed or 1
            total_reps = total_reps or 0
            top_weight = top_weight or 0.0

            # Calculate reps per set
            if sets_completed > 0 and total_reps > 0:
                reps_per_set = total_reps // sets_completed
                remainder_reps = total_reps % sets_completed
            else:
                reps_per_set = 0
                remainder_reps = 0

            # Insert sets
            for set_num in range(1, sets_completed + 1):
                # Last set gets remainder reps
                reps = reps_per_set + (remainder_reps if set_num == sets_completed else 0)

                connection.execute(text("""
                    INSERT INTO log_sets (log_exercise_id, set_number, reps, weight, rpe, notes, rest_time_seconds)
                    VALUES (:log_ex_id, :set_num, :reps, :weight, NULL, NULL, NULL)
                """), {
                    'log_ex_id': log_ex_id,
                    'set_num': set_num,
                    'reps': reps,
                    'weight': top_weight
                })

    # Step 6: Drop old aggregate columns from log_exercises
    op.drop_column('log_exercises', 'sets_completed')
    op.drop_column('log_exercises', 'top_weight')
    op.drop_column('log_exercises', 'total_reps')


def downgrade() -> None:
    # Step 1: Re-add aggregate columns to log_exercises
    op.add_column('log_exercises', sa.Column('sets_completed', sa.Integer(), nullable=True))
    op.add_column('log_exercises', sa.Column('top_weight', sa.Float(), nullable=True))
    op.add_column('log_exercises', sa.Column('total_reps', sa.Integer(), nullable=True))

    # Step 2: Recalculate aggregates from sets
    op.execute("""
        UPDATE log_exercises le
        SET
            sets_completed = (SELECT COUNT(*) FROM log_sets WHERE log_exercise_id = le.id),
            top_weight = (SELECT COALESCE(MAX(weight), 0.0) FROM log_sets WHERE log_exercise_id = le.id),
            total_reps = (SELECT COALESCE(SUM(reps), 0) FROM log_sets WHERE log_exercise_id = le.id);
    """)

    # Step 3: Make columns non-nullable after populating
    op.alter_column('log_exercises', 'sets_completed', nullable=False)
    op.alter_column('log_exercises', 'top_weight', nullable=False)
    op.alter_column('log_exercises', 'total_reps', nullable=False)

    # Step 4: Drop log_sets table (cascade will handle constraints and indexes)
    op.drop_table('log_sets')
