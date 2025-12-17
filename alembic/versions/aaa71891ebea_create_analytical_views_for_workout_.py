"""create analytical views for workout progress tracking

Revision ID: aaa71891ebea
Revises: bceb5b523426
Create Date: 2025-12-15 22:56:35.145788+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aaa71891ebea'
down_revision = 'bceb5b523426'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==============================================
    # 1. USER EXERCISE PROGRESS VIEW (Materialized)
    # ==============================================
    # Tracks progress for each user-exercise combination by week
    op.execute("""
        CREATE MATERIALIZED VIEW user_exercise_progress_weekly AS
        SELECT
            ws.user_id,
            le.exercise_id,
            e.name as exercise_name,
            e.muscle_group,
            DATE_TRUNC('week', ws.workout_date)::date as week_start,
            COUNT(DISTINCT ws.id) as workout_count,
            MAX(le.top_weight) as max_weight,
            SUM(le.total_reps) as total_reps,
            SUM(le.sets_completed) as total_sets,
            SUM(le.total_reps * le.top_weight) as total_volume
        FROM workout_sessions ws
        JOIN log_exercises le ON ws.id = le.session_id
        JOIN exercises e ON le.exercise_id = e.id
        GROUP BY ws.user_id, le.exercise_id, e.name, e.muscle_group, week_start
        ORDER BY ws.user_id, le.exercise_id, week_start;
    """)

    # Create index for better query performance
    op.execute("""
        CREATE INDEX idx_user_exercise_progress_user_exercise
        ON user_exercise_progress_weekly(user_id, exercise_id);
    """)

    op.execute("""
        CREATE INDEX idx_user_exercise_progress_week
        ON user_exercise_progress_weekly(week_start);
    """)

    # ==============================================
    # 2. WORKOUT VOLUME BY WEEK VIEW (Materialized)
    # ==============================================
    # Aggregates total workout volume by week for each user
    op.execute("""
        CREATE MATERIALIZED VIEW workout_volume_by_week AS
        SELECT
            ws.user_id,
            DATE_TRUNC('week', ws.workout_date)::date as week_start,
            COUNT(DISTINCT ws.id) as workout_count,
            SUM(ws.duration_minutes) as total_duration_minutes,
            AVG(ws.duration_minutes) as avg_workout_duration,
            SUM(le.total_reps * le.top_weight) as total_volume,
            COUNT(DISTINCT le.exercise_id) as unique_exercises
        FROM workout_sessions ws
        LEFT JOIN log_exercises le ON ws.id = le.session_id
        GROUP BY ws.user_id, week_start
        ORDER BY ws.user_id, week_start;
    """)

    op.execute("""
        CREATE INDEX idx_workout_volume_week_user
        ON workout_volume_by_week(user_id, week_start);
    """)

    # ==============================================
    # 3. WORKOUT VOLUME BY MONTH VIEW (Materialized)
    # ==============================================
    op.execute("""
        CREATE MATERIALIZED VIEW workout_volume_by_month AS
        SELECT
            ws.user_id,
            DATE_TRUNC('month', ws.workout_date)::date as month_start,
            COUNT(DISTINCT ws.id) as workout_count,
            SUM(ws.duration_minutes) as total_duration_minutes,
            AVG(ws.duration_minutes) as avg_workout_duration,
            SUM(le.total_reps * le.top_weight) as total_volume,
            COUNT(DISTINCT le.exercise_id) as unique_exercises
        FROM workout_sessions ws
        LEFT JOIN log_exercises le ON ws.id = le.session_id
        GROUP BY ws.user_id, month_start
        ORDER BY ws.user_id, month_start;
    """)

    op.execute("""
        CREATE INDEX idx_workout_volume_month_user
        ON workout_volume_by_month(user_id, month_start);
    """)

    # ==============================================
    # 4. PERSONAL RECORDS VIEW (Materialized)
    # ==============================================
    # Tracks maximum weight achieved for each user-exercise combination
    op.execute("""
        CREATE MATERIALIZED VIEW personal_records AS
        WITH ranked_lifts AS (
            SELECT
                ws.user_id,
                le.exercise_id,
                e.name as exercise_name,
                e.muscle_group,
                le.top_weight as max_weight,
                le.total_reps as reps_at_max,
                ws.workout_date,
                ROW_NUMBER() OVER (
                    PARTITION BY ws.user_id, le.exercise_id
                    ORDER BY le.top_weight DESC, ws.workout_date DESC
                ) as rank
            FROM workout_sessions ws
            JOIN log_exercises le ON ws.id = le.session_id
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
        WHERE rank = 1;
    """)

    op.execute("""
        CREATE INDEX idx_personal_records_user
        ON personal_records(user_id);
    """)

    # ==============================================
    # 5. MUSCLE GROUP DISTRIBUTION VIEW (Regular)
    # ==============================================
    # Real-time view of muscle group distribution per user
    op.execute("""
        CREATE VIEW muscle_group_distribution AS
        SELECT
            ws.user_id,
            e.muscle_group,
            COUNT(DISTINCT le.exercise_id) as exercise_count,
            SUM(le.sets_completed) as total_sets,
            SUM(le.total_reps * le.top_weight) as total_volume,
            ROUND(
                100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY ws.user_id),
                2
            ) as percentage
        FROM workout_sessions ws
        JOIN log_exercises le ON ws.id = le.session_id
        JOIN exercises e ON le.exercise_id = e.id
        WHERE e.muscle_group IS NOT NULL
        GROUP BY ws.user_id, e.muscle_group
        ORDER BY ws.user_id, total_volume DESC;
    """)

    # ==============================================
    # 6. USER WORKOUT SUMMARY VIEW (Regular)
    # ==============================================
    # Real-time summary of user workout statistics
    op.execute("""
        CREATE VIEW user_workout_summary AS
        SELECT
            ws.user_id,
            COUNT(DISTINCT ws.id) as total_workouts,
            COUNT(DISTINCT le.exercise_id) as total_unique_exercises,
            SUM(ws.duration_minutes) as total_workout_minutes,
            AVG(ws.duration_minutes) as avg_workout_duration,
            SUM(le.total_reps * le.top_weight) as total_volume,
            MIN(ws.workout_date) as first_workout_date,
            MAX(ws.workout_date) as last_workout_date,
            CURRENT_DATE - MAX(ws.workout_date) as days_since_last_workout
        FROM workout_sessions ws
        LEFT JOIN log_exercises le ON ws.id = le.session_id
        GROUP BY ws.user_id;
    """)

    # ==============================================
    # 7. EXERCISE FREQUENCY VIEW (Regular)
    # ==============================================
    # Shows how often each exercise is performed by each user
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
            AVG(le.top_weight) as avg_weight,
            MAX(le.top_weight) as max_weight
        FROM workout_sessions ws
        JOIN log_exercises le ON ws.id = le.session_id
        JOIN exercises e ON le.exercise_id = e.id
        GROUP BY ws.user_id, e.id, e.name, e.muscle_group
        ORDER BY ws.user_id, times_performed DESC;
    """)


def downgrade() -> None:
    # Drop views in reverse order (regular views first, then materialized)
    op.execute("DROP VIEW IF EXISTS exercise_frequency;")
    op.execute("DROP VIEW IF EXISTS user_workout_summary;")
    op.execute("DROP VIEW IF EXISTS muscle_group_distribution;")

    op.execute("DROP MATERIALIZED VIEW IF EXISTS personal_records;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS workout_volume_by_month;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS workout_volume_by_week;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS user_exercise_progress_weekly;")
