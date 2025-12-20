"""add_muscle_group_specificity

Revision ID: 6d038ccb729f
Revises: 03be130783e6
Create Date: 2025-12-20 22:35:55.122869+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6d038ccb729f'
down_revision = '03be130783e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop views that depend on muscle_group column
    op.execute("DROP VIEW IF EXISTS exercise_frequency CASCADE;")
    op.execute("DROP VIEW IF EXISTS user_workout_summary CASCADE;")
    op.execute("DROP VIEW IF EXISTS muscle_group_distribution CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS personal_records CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS workout_volume_by_month CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS user_exercise_progress_weekly CASCADE;")

    # Rename muscle_group to agonist_muscle_group
    op.alter_column('exercises', 'muscle_group',
                    new_column_name='agonist_muscle_group',
                    existing_type=sa.String(),
                    existing_nullable=True)

    # Add synergist_muscle_group column
    op.add_column('exercises',
                  sa.Column('synergist_muscle_group', sa.String(), nullable=True))

    # Recreate views using agonist_muscle_group
    # 1. USER EXERCISE PROGRESS WEEKLY (Materialized View)
    op.execute("""
        CREATE MATERIALIZED VIEW user_exercise_progress_weekly AS
        SELECT
            ws.user_id,
            le.exercise_id,
            e.name as exercise_name,
            e.agonist_muscle_group,
            DATE_TRUNC('week', ws.workout_date)::date as week_start,
            COUNT(DISTINCT ws.id) as workout_count,
            MAX(ls.weight) as max_weight,
            SUM(ls.reps) as total_reps,
            COUNT(ls.id) as total_sets,
            SUM(ls.reps * ls.weight) as total_volume
        FROM workout_sessions ws
        JOIN log_exercises le ON ws.id = le.session_id
        JOIN log_sets ls ON le.id = ls.log_exercise_id
        JOIN exercises e ON le.exercise_id = e.id
        GROUP BY ws.user_id, le.exercise_id, e.name, e.agonist_muscle_group, week_start
        ORDER BY ws.user_id, le.exercise_id, week_start;
    """)

    op.execute("""
        CREATE INDEX idx_user_exercise_progress_weekly
        ON user_exercise_progress_weekly(user_id, exercise_id, week_start);
    """)

    # 2. WORKOUT VOLUME BY MONTH (Materialized View)
    op.execute("""
        CREATE MATERIALIZED VIEW workout_volume_by_month AS
        SELECT
            ws.user_id,
            DATE_TRUNC('month', ws.workout_date)::date as month_start,
            COUNT(DISTINCT ws.id) as workout_count,
            SUM(ws.duration_minutes) as total_duration_minutes,
            AVG(ws.duration_minutes) as avg_workout_duration,
            COALESCE(SUM(ls.reps * ls.weight), 0) as total_volume,
            COUNT(DISTINCT le.exercise_id) as unique_exercises
        FROM workout_sessions ws
        LEFT JOIN log_exercises le ON ws.id = le.session_id
        LEFT JOIN log_sets ls ON le.id = ls.log_exercise_id
        GROUP BY ws.user_id, month_start
        ORDER BY ws.user_id, month_start;
    """)

    op.execute("""
        CREATE INDEX idx_workout_volume_month_user
        ON workout_volume_by_month(user_id, month_start);
    """)

    # 3. PERSONAL RECORDS (Materialized View)
    op.execute("""
        CREATE MATERIALIZED VIEW personal_records AS
        WITH ranked_lifts AS (
            SELECT
                ws.user_id,
                le.exercise_id,
                e.name as exercise_name,
                e.agonist_muscle_group,
                ls.weight as max_weight,
                ls.reps as reps_at_max,
                ws.workout_date,
                ROW_NUMBER() OVER (
                    PARTITION BY ws.user_id, le.exercise_id
                    ORDER BY ls.weight DESC, ws.workout_date DESC
                ) as rn
            FROM workout_sessions ws
            JOIN log_exercises le ON ws.id = le.session_id
            JOIN log_sets ls ON le.id = ls.log_exercise_id
            JOIN exercises e ON le.exercise_id = e.id
        )
        SELECT
            user_id,
            exercise_id,
            exercise_name,
            agonist_muscle_group,
            max_weight,
            reps_at_max,
            workout_date as achieved_date,
            CURRENT_DATE - workout_date as days_ago
        FROM ranked_lifts
        WHERE rn = 1
        ORDER BY user_id, max_weight DESC;
    """)

    op.execute("""
        CREATE INDEX idx_personal_records_user
        ON personal_records(user_id, max_weight DESC);
    """)

    # 4. MUSCLE GROUP DISTRIBUTION (View)
    op.execute("""
        CREATE VIEW muscle_group_distribution AS
        SELECT
            ws.user_id,
            e.agonist_muscle_group,
            COUNT(DISTINCT le.exercise_id) as exercise_count,
            COUNT(ls.id) as total_sets,
            SUM(ls.reps * ls.weight) as total_volume,
            ROUND(
                100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY ws.user_id),
                2
            ) as percentage
        FROM workout_sessions ws
        JOIN log_exercises le ON ws.id = le.session_id
        JOIN log_sets ls ON le.id = ls.log_exercise_id
        JOIN exercises e ON le.exercise_id = e.id
        WHERE e.agonist_muscle_group IS NOT NULL
        GROUP BY ws.user_id, e.agonist_muscle_group
        ORDER BY ws.user_id, total_volume DESC;
    """)

    # 5. USER WORKOUT SUMMARY (View)
    op.execute("""
        CREATE VIEW user_workout_summary AS
        SELECT
            ws.user_id,
            COUNT(DISTINCT ws.id) as total_workouts,
            COUNT(DISTINCT le.exercise_id) as total_unique_exercises,
            SUM(ws.duration_minutes) as total_workout_minutes,
            AVG(ws.duration_minutes) as avg_workout_duration,
            COALESCE(SUM(ls.reps * ls.weight), 0) as total_volume,
            CURRENT_DATE - MAX(ws.workout_date) as days_since_last_workout
        FROM workout_sessions ws
        LEFT JOIN log_exercises le ON ws.id = le.session_id
        LEFT JOIN log_sets ls ON le.id = ls.log_exercise_id
        GROUP BY ws.user_id;
    """)

    # 6. EXERCISE FREQUENCY (View)
    op.execute("""
        CREATE VIEW exercise_frequency AS
        SELECT
            ws.user_id,
            e.id as exercise_id,
            e.name as exercise_name,
            e.agonist_muscle_group,
            COUNT(DISTINCT ws.id) as times_performed,
            MIN(ws.workout_date) as first_performed,
            MAX(ws.workout_date) as last_performed,
            AVG(ls.weight) as avg_weight,
            MAX(ls.weight) as max_weight
        FROM workout_sessions ws
        JOIN log_exercises le ON ws.id = le.session_id
        JOIN log_sets ls ON le.id = ls.log_exercise_id
        JOIN exercises e ON le.exercise_id = e.id
        GROUP BY ws.user_id, e.id, e.name, e.agonist_muscle_group
        ORDER BY ws.user_id, times_performed DESC;
    """)

    # 7. WEEKLY MUSCLE VOLUME (View)
    # Tracks weekly set volume per muscle group (agonist + synergist)
    # Ideal range: 10-20 sets per muscle per week
    op.execute("""
        CREATE VIEW weekly_muscle_volume AS
        WITH muscle_sets AS (
            -- Count sets where muscle is the agonist
            SELECT
                ws.user_id,
                DATE_TRUNC('week', ws.workout_date)::date as week_start,
                e.agonist_muscle_group as muscle_group,
                COUNT(ls.id) as total_sets
            FROM workout_sessions ws
            JOIN log_exercises le ON ws.id = le.session_id
            JOIN log_sets ls ON le.id = ls.log_exercise_id
            JOIN exercises e ON le.exercise_id = e.id
            WHERE e.agonist_muscle_group IS NOT NULL
            GROUP BY ws.user_id, week_start, e.agonist_muscle_group

            UNION ALL

            -- Count sets where muscle is the synergist
            SELECT
                ws.user_id,
                DATE_TRUNC('week', ws.workout_date)::date as week_start,
                e.synergist_muscle_group as muscle_group,
                COUNT(ls.id) as total_sets
            FROM workout_sessions ws
            JOIN log_exercises le ON ws.id = le.session_id
            JOIN log_sets ls ON le.id = ls.log_exercise_id
            JOIN exercises e ON le.exercise_id = e.id
            WHERE e.synergist_muscle_group IS NOT NULL
            GROUP BY ws.user_id, week_start, e.synergist_muscle_group
        )
        SELECT
            user_id,
            week_start,
            muscle_group,
            SUM(total_sets) as weekly_sets,
            CASE
                WHEN SUM(total_sets) < 10 THEN 'under_trained'
                WHEN SUM(total_sets) BETWEEN 10 AND 20 THEN 'optimal'
                ELSE 'over_trained'
            END as volume_status,
            ROUND((SUM(total_sets)::numeric / 15.0) * 100, 2) as percentage_of_optimal
        FROM muscle_sets
        GROUP BY user_id, week_start, muscle_group
        ORDER BY user_id, week_start DESC, muscle_group;
    """)


def downgrade() -> None:
    # Drop views that use agonist_muscle_group
    op.execute("DROP VIEW IF EXISTS weekly_muscle_volume CASCADE;")
    op.execute("DROP VIEW IF EXISTS exercise_frequency CASCADE;")
    op.execute("DROP VIEW IF EXISTS user_workout_summary CASCADE;")
    op.execute("DROP VIEW IF EXISTS muscle_group_distribution CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS personal_records CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS workout_volume_by_month CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS user_exercise_progress_weekly CASCADE;")

    # Remove synergist_muscle_group column
    op.drop_column('exercises', 'synergist_muscle_group')

    # Rename agonist_muscle_group back to muscle_group
    op.alter_column('exercises', 'agonist_muscle_group',
                    new_column_name='muscle_group',
                    existing_type=sa.String(),
                    existing_nullable=True)

    # Recreate views using muscle_group
    # 1. USER EXERCISE PROGRESS WEEKLY (Materialized View)
    op.execute("""
        CREATE MATERIALIZED VIEW user_exercise_progress_weekly AS
        SELECT
            ws.user_id,
            le.exercise_id,
            e.name as exercise_name,
            e.muscle_group,
            DATE_TRUNC('week', ws.workout_date)::date as week_start,
            COUNT(DISTINCT ws.id) as workout_count,
            MAX(ls.weight) as max_weight,
            SUM(ls.reps) as total_reps,
            COUNT(ls.id) as total_sets,
            SUM(ls.reps * ls.weight) as total_volume
        FROM workout_sessions ws
        JOIN log_exercises le ON ws.id = le.session_id
        JOIN log_sets ls ON le.id = ls.log_exercise_id
        JOIN exercises e ON le.exercise_id = e.id
        GROUP BY ws.user_id, le.exercise_id, e.name, e.muscle_group, week_start
        ORDER BY ws.user_id, le.exercise_id, week_start;
    """)

    op.execute("""
        CREATE INDEX idx_user_exercise_progress_weekly
        ON user_exercise_progress_weekly(user_id, exercise_id, week_start);
    """)

    # 2. WORKOUT VOLUME BY MONTH (Materialized View)
    op.execute("""
        CREATE MATERIALIZED VIEW workout_volume_by_month AS
        SELECT
            ws.user_id,
            DATE_TRUNC('month', ws.workout_date)::date as month_start,
            COUNT(DISTINCT ws.id) as workout_count,
            SUM(ws.duration_minutes) as total_duration_minutes,
            AVG(ws.duration_minutes) as avg_workout_duration,
            COALESCE(SUM(ls.reps * ls.weight), 0) as total_volume,
            COUNT(DISTINCT le.exercise_id) as unique_exercises
        FROM workout_sessions ws
        LEFT JOIN log_exercises le ON ws.id = le.session_id
        LEFT JOIN log_sets ls ON le.id = ls.log_exercise_id
        GROUP BY ws.user_id, month_start
        ORDER BY ws.user_id, month_start;
    """)

    op.execute("""
        CREATE INDEX idx_workout_volume_month_user
        ON workout_volume_by_month(user_id, month_start);
    """)

    # 3. PERSONAL RECORDS (Materialized View)
    op.execute("""
        CREATE MATERIALIZED VIEW personal_records AS
        WITH ranked_lifts AS (
            SELECT
                ws.user_id,
                le.exercise_id,
                e.name as exercise_name,
                e.muscle_group,
                ls.weight as max_weight,
                ls.reps as reps_at_max,
                ws.workout_date,
                ROW_NUMBER() OVER (
                    PARTITION BY ws.user_id, le.exercise_id
                    ORDER BY ls.weight DESC, ws.workout_date DESC
                ) as rn
            FROM workout_sessions ws
            JOIN log_exercises le ON ws.id = le.session_id
            JOIN log_sets ls ON le.id = ls.log_exercise_id
            JOIN exercises e ON le.exercise_id = e.id
        )
        SELECT
            user_id,
            exercise_id,
            exercise_name,
            muscle_group,
            max_weight,
            reps_at_max,
            workout_date as achieved_date,
            CURRENT_DATE - workout_date as days_ago
        FROM ranked_lifts
        WHERE rn = 1
        ORDER BY user_id, max_weight DESC;
    """)

    op.execute("""
        CREATE INDEX idx_personal_records_user
        ON personal_records(user_id, max_weight DESC);
    """)

    # 4. MUSCLE GROUP DISTRIBUTION (View)
    op.execute("""
        CREATE VIEW muscle_group_distribution AS
        SELECT
            ws.user_id,
            e.muscle_group,
            COUNT(DISTINCT le.exercise_id) as exercise_count,
            COUNT(ls.id) as total_sets,
            SUM(ls.reps * ls.weight) as total_volume,
            ROUND(
                100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY ws.user_id),
                2
            ) as percentage
        FROM workout_sessions ws
        JOIN log_exercises le ON ws.id = le.session_id
        JOIN log_sets ls ON le.id = ls.log_exercise_id
        JOIN exercises e ON le.exercise_id = e.id
        WHERE e.muscle_group IS NOT NULL
        GROUP BY ws.user_id, e.muscle_group
        ORDER BY ws.user_id, total_volume DESC;
    """)

    # 5. USER WORKOUT SUMMARY (View)
    op.execute("""
        CREATE VIEW user_workout_summary AS
        SELECT
            ws.user_id,
            COUNT(DISTINCT ws.id) as total_workouts,
            COUNT(DISTINCT le.exercise_id) as total_unique_exercises,
            SUM(ws.duration_minutes) as total_workout_minutes,
            AVG(ws.duration_minutes) as avg_workout_duration,
            COALESCE(SUM(ls.reps * ls.weight), 0) as total_volume,
            CURRENT_DATE - MAX(ws.workout_date) as days_since_last_workout
        FROM workout_sessions ws
        LEFT JOIN log_exercises le ON ws.id = le.session_id
        LEFT JOIN log_sets ls ON le.id = ls.log_exercise_id
        GROUP BY ws.user_id;
    """)

    # 6. EXERCISE FREQUENCY (View)
    op.execute("""
        CREATE VIEW exercise_frequency AS
        SELECT
            ws.user_id,
            e.id as exercise_id,
            e.name as exercise_name,
            e.muscle_group,
            COUNT(DISTINCT ws.id) as times_performed,
            MIN(ws.workout_date) as first_performed,
            MAX(ws.workout_date) as last_performed,
            AVG(ls.weight) as avg_weight,
            MAX(ls.weight) as max_weight
        FROM workout_sessions ws
        JOIN log_exercises le ON ws.id = le.session_id
        JOIN log_sets ls ON le.id = ls.log_exercise_id
        JOIN exercises e ON le.exercise_id = e.id
        GROUP BY ws.user_id, e.id, e.name, e.muscle_group
        ORDER BY ws.user_id, times_performed DESC;
    """)
