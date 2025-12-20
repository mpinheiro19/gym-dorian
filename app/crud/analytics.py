"""Analytics CRUD operations for workout progress tracking."""
from typing import Optional, List
from datetime import datetime, timedelta, date
from sqlalchemy import text, func
from sqlalchemy.orm import Session

from app.models.log import WorkoutSession, LogExercise
from app.models.exercise import Exercise
from app.models.user import UserGoal, GoalStatus
from app.schemas.analytics_schema import (
    ExerciseProgressPoint,
    ExerciseProgressResponse,
    UserProgressSummary,
    WorkoutVolumeByWeek,
    WorkoutVolumeByMonth,
    MuscleGroupDistribution,
    WeeklyMuscleVolume,
    PersonalRecord,
    WorkoutInsight,
)


# ===========================
# Exercise Progress Analytics
# ===========================

def get_exercise_progress(
    db: Session,
    user_id: int,
    exercise_id: int,
    days: int = 90
) -> Optional[ExerciseProgressResponse]:
    """
    Get progress data for a specific exercise over time.

    Args:
        db: Database session
        user_id: User ID
        exercise_id: Exercise ID
        days: Number of days to look back (default 90)

    Returns:
        ExerciseProgressResponse: Exercise progress data or None
    """
    # Query from materialized view
    cutoff_date = datetime.utcnow().date() - timedelta(days=days)

    query = text("""
        SELECT
            week_start as workout_date,
            max_weight,
            total_reps,
            total_sets,
            total_volume as volume
        FROM user_exercise_progress_weekly
        WHERE user_id = :user_id
          AND exercise_id = :exercise_id
          AND week_start >= :cutoff_date
        ORDER BY week_start
    """)

    result = db.execute(
        query,
        {"user_id": user_id, "exercise_id": exercise_id, "cutoff_date": cutoff_date}
    ).fetchall()

    if not result:
        return None

    # Get exercise info
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        return None

    data_points = [
        ExerciseProgressPoint(
            workout_date=row.workout_date,
            max_weight=float(row.max_weight),
            total_reps=int(row.total_reps),
            total_sets=int(row.total_sets),
            volume=float(row.volume)
        )
        for row in result
    ]

    # Calculate summary statistics
    first_point = data_points[0]
    last_point = data_points[-1]
    weight_gain = last_point.max_weight - first_point.max_weight
    weight_gain_pct = (weight_gain / first_point.max_weight * 100) if first_point.max_weight > 0 else 0

    return ExerciseProgressResponse(
        exercise_id=exercise_id,
        exercise_name=exercise.name,
        agonist_muscle_group=exercise.agonist_muscle_group,
        data_points=data_points,
        first_workout=first_point.workout_date,
        last_workout=last_point.workout_date,
        total_workouts=len(data_points),
        starting_weight=first_point.max_weight,
        current_weight=last_point.max_weight,
        weight_gain=weight_gain,
        weight_gain_percentage=round(weight_gain_pct, 2)
    )


def get_user_progress_summary(db: Session, user_id: int) -> UserProgressSummary:
    """
    Get overall progress summary for a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        UserProgressSummary: User progress summary
    """
    # Query from user_workout_summary view
    query = text("""
        SELECT
            total_workouts,
            total_unique_exercises,
            total_workout_minutes,
            avg_workout_duration,
            total_volume,
            days_since_last_workout
        FROM user_workout_summary
        WHERE user_id = :user_id
    """)

    result = db.execute(query, {"user_id": user_id}).fetchone()

    if not result:
        return UserProgressSummary(
            user_id=user_id,
            total_workouts=0,
            total_exercises=0,
            total_workout_minutes=0,
            avg_workout_duration=0.0,
            total_volume=0.0,
            exercises_by_muscle_group={},
            most_frequent_exercise=None,
            recent_activity_days=0
        )

    # Get muscle group distribution
    muscle_query = text("""
        SELECT agonist_muscle_group, exercise_count
        FROM muscle_group_distribution
        WHERE user_id = :user_id
    """)

    muscle_result = db.execute(muscle_query, {"user_id": user_id}).fetchall()
    exercises_by_muscle_group = {row.agonist_muscle_group: row.exercise_count for row in muscle_result}

    # Get most frequent exercise
    freq_query = text("""
        SELECT exercise_name
        FROM exercise_frequency
        WHERE user_id = :user_id
        ORDER BY times_performed DESC
        LIMIT 1
    """)

    freq_result = db.execute(freq_query, {"user_id": user_id}).fetchone()
    most_frequent = freq_result.exercise_name if freq_result else None

    return UserProgressSummary(
        user_id=user_id,
        total_workouts=result.total_workouts or 0,
        total_exercises=result.total_unique_exercises or 0,
        total_workout_minutes=result.total_workout_minutes or 0,
        avg_workout_duration=float(result.avg_workout_duration or 0),
        total_volume=float(result.total_volume or 0),
        exercises_by_muscle_group=exercises_by_muscle_group,
        most_frequent_exercise=most_frequent,
        recent_activity_days=result.days_since_last_workout or 0
    )


# ===========================
# Volume Tracking
# ===========================

def get_workout_volume_by_week(
    db: Session,
    user_id: int,
    weeks: int = 12
) -> List[WorkoutVolumeByWeek]:
    """
    Get workout volume aggregated by week.

    Args:
        db: Database session
        user_id: User ID
        weeks: Number of weeks to retrieve (default 12)

    Returns:
        List[WorkoutVolumeByWeek]: Weekly workout volumes
    """
    cutoff_date = datetime.utcnow().date() - timedelta(weeks=weeks)

    query = text("""
        SELECT
            week_start,
            workout_count,
            total_duration_minutes,
            total_volume,
            unique_exercises,
            avg_workout_duration
        FROM workout_volume_by_week
        WHERE user_id = :user_id
          AND week_start >= :cutoff_date
        ORDER BY week_start
    """)

    result = db.execute(query, {"user_id": user_id, "cutoff_date": cutoff_date}).fetchall()

    return [WorkoutVolumeByWeek.model_validate(dict(row._mapping)) for row in result]


def get_workout_volume_by_month(
    db: Session,
    user_id: int,
    months: int = 6
) -> List[WorkoutVolumeByMonth]:
    """
    Get workout volume aggregated by month.

    Args:
        db: Database session
        user_id: User ID
        months: Number of months to retrieve (default 6)

    Returns:
        List[WorkoutVolumeByMonth]: Monthly workout volumes
    """
    cutoff_date = datetime.utcnow().date() - timedelta(days=months * 30)

    query = text("""
        SELECT
            month_start,
            workout_count,
            total_duration_minutes,
            total_volume,
            unique_exercises,
            avg_workout_duration
        FROM workout_volume_by_month
        WHERE user_id = :user_id
          AND month_start >= :cutoff_date
        ORDER BY month_start
    """)

    result = db.execute(query, {"user_id": user_id, "cutoff_date": cutoff_date}).fetchall()

    return [WorkoutVolumeByMonth.model_validate(dict(row._mapping)) for row in result]


# ===========================
# Personal Records
# ===========================

def get_personal_records(
    db: Session,
    user_id: int,
    limit: int = 10
) -> List[PersonalRecord]:
    """
    Get personal records for a user.

    Args:
        db: Database session
        user_id: User ID
        limit: Maximum number of PRs to return

    Returns:
        List[PersonalRecord]: Personal records
    """
    query = text("""
        SELECT
            exercise_id,
            exercise_name,
            muscle_group,
            max_weight,
            reps_at_max,
            achieved_date,
            days_ago
        FROM personal_records
        WHERE user_id = :user_id
        ORDER BY achieved_date DESC
        LIMIT :limit
    """)

    result = db.execute(query, {"user_id": user_id, "limit": limit}).fetchall()

    return [PersonalRecord.model_validate(dict(row._mapping)) for row in result]


# ===========================
# Muscle Group Distribution
# ===========================

def get_muscle_group_distribution(
    db: Session,
    user_id: int
) -> List[MuscleGroupDistribution]:
    """
    Get muscle group distribution for a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        List[MuscleGroupDistribution]: Muscle group distribution
    """
    query = text("""
        SELECT
            agonist_muscle_group,
            exercise_count,
            total_sets,
            total_volume,
            percentage
        FROM muscle_group_distribution
        WHERE user_id = :user_id
        ORDER BY total_volume DESC
    """)

    result = db.execute(query, {"user_id": user_id}).fetchall()

    return [MuscleGroupDistribution.model_validate(dict(row._mapping)) for row in result]


def get_weekly_muscle_volume(
    db: Session,
    user_id: int,
    weeks: int = 12
) -> List[WeeklyMuscleVolume]:
    """
    Get weekly muscle volume (agonist + synergist sets combined).

    Tracks total weekly sets per muscle group to ensure optimal training volume
    (ideal range: 10-20 sets per muscle per week).

    Args:
        db: Database session
        user_id: User ID
        weeks: Number of weeks to retrieve (default: 12)

    Returns:
        List[WeeklyMuscleVolume]: Weekly muscle volume data
    """
    query = text("""
        SELECT
            week_start,
            muscle_group,
            weekly_sets,
            volume_status,
            percentage_of_optimal
        FROM weekly_muscle_volume
        WHERE user_id = :user_id
            AND week_start >= CURRENT_DATE - INTERVAL ':weeks weeks'
        ORDER BY week_start DESC, muscle_group
    """)

    result = db.execute(query, {"user_id": user_id, "weeks": weeks}).fetchall()

    return [WeeklyMuscleVolume.model_validate(dict(row._mapping)) for row in result]


# ===========================
# Insights Generation
# ===========================

def generate_user_insights(db: Session, user_id: int) -> List[WorkoutInsight]:
    """
    Generate actionable insights for a user based on their data.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        List[WorkoutInsight]: Generated insights
    """
    insights = []

    # Get user summary
    summary = get_user_progress_summary(db, user_id)

    # Insight 1: Recent activity
    if summary.recent_activity_days == 0:
        insights.append(WorkoutInsight(
            type="achievement",
            title="Workout Today!",
            description="You logged a workout today. Keep up the great work!",
            insight_date=datetime.utcnow().date(),
            priority=5
        ))
    elif summary.recent_activity_days >= 7:
        insights.append(WorkoutInsight(
            type="warning",
            title="Time to Get Back!",
            description=f"It's been {summary.recent_activity_days} days since your last workout. Let's get moving!",
            priority=5
        ))
    elif summary.recent_activity_days >= 3:
        insights.append(WorkoutInsight(
            type="suggestion",
            title="Stay Consistent",
            description=f"You haven't worked out in {summary.recent_activity_days} days. Try to maintain your routine!",
            priority=3
        ))

    # Insight 2: Check for new PRs (last 7 days)
    recent_prs = db.execute(
        text("""
            SELECT exercise_name, max_weight, achieved_date
            FROM personal_records
            WHERE user_id = :user_id AND days_ago <= 7
        """),
        {"user_id": user_id}
    ).fetchall()

    for pr in recent_prs:
        insights.append(WorkoutInsight(
            type="achievement",
            title=f"New PR: {pr.exercise_name}!",
            description=f"You hit a new personal record of {pr.max_weight}kg on {pr.exercise_name}!",
            insight_date=pr.achieved_date,
            priority=5
        ))

    # Insight 3: Muscle group imbalance
    muscle_dist = get_muscle_group_distribution(db, user_id)
    if muscle_dist:
        total_volume = sum(m.total_volume for m in muscle_dist)
        for muscle in muscle_dist:
            percentage = (muscle.total_volume / total_volume * 100) if total_volume > 0 else 0
            if percentage < 10 and muscle.agonist_muscle_group:
                insights.append(WorkoutInsight(
                    type="suggestion",
                    title=f"Balance Your {muscle.agonist_muscle_group} Training",
                    description=f"Only {percentage:.1f}% of your volume goes to {muscle.agonist_muscle_group}. Consider adding more exercises!",
                    priority=2
                ))

    # Insight 4: Milestone achievements
    if summary.total_workouts == 50:
        insights.append(WorkoutInsight(
            type="milestone",
            title="50 Workouts Milestone!",
            description="Congratulations! You've completed 50 workouts. Amazing dedication!",
            priority=5
        ))
    elif summary.total_workouts == 100:
        insights.append(WorkoutInsight(
            type="milestone",
            title="Century Club!",
            description="100 workouts completed! You're a fitness champion!",
            priority=5
        ))

    return insights


# ===========================
# Materialized View Refresh
# ===========================

def refresh_analytics_views(db: Session) -> None:
    """
    Refresh all materialized views.

    Should be called periodically (e.g., daily via cron job).

    Args:
        db: Database session
    """
    db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY user_exercise_progress_weekly;"))
    db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY workout_volume_by_week;"))
    db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY workout_volume_by_month;"))
    db.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY personal_records;"))
    db.commit()
