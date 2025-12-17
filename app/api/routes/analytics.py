"""Analytics routes for workout progress tracking and insights."""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.dependencies.auth import get_current_active_user, get_current_superuser
from app.models.user import User
from app.crud import analytics as analytics_crud
from app.schemas.analytics_schema import (
    ExerciseProgressResponse,
    UserProgressSummary,
    WorkoutVolumeByWeek,
    WorkoutVolumeByMonth,
    MuscleGroupDistribution,
    PersonalRecord,
    UserInsights,
    WorkoutInsight,
    AnalyticsDashboard,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# ===========================
# User Progress Endpoints
# ===========================

@router.get("/progress/summary", response_model=UserProgressSummary)
def get_progress_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get overall progress summary for the current user.

    Returns aggregate statistics including total workouts, volume,
    muscle group distribution, and activity status.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        UserProgressSummary: Overall progress summary
    """
    return analytics_crud.get_user_progress_summary(db, current_user.id)


@router.get("/progress/exercise/{exercise_id}", response_model=ExerciseProgressResponse)
def get_exercise_progress(
    exercise_id: int,
    days: int = Query(90, ge=7, le=365, description="Number of days to look back"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get progress tracking for a specific exercise.

    Shows how weight, reps, and volume have changed over time.

    Args:
        exercise_id: Exercise ID
        days: Number of days to look back (7-365)
        current_user: Authenticated user
        db: Database session

    Returns:
        ExerciseProgressResponse: Exercise progress data

    Raises:
        HTTPException 404: If no data found for this exercise
    """
    progress = analytics_crud.get_exercise_progress(
        db,
        current_user.id,
        exercise_id,
        days
    )

    if not progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No workout data found for this exercise"
        )

    return progress


# ===========================
# Volume Tracking Endpoints
# ===========================

@router.get("/volume/weekly", response_model=List[WorkoutVolumeByWeek])
def get_weekly_volume(
    weeks: int = Query(12, ge=1, le=52, description="Number of weeks to retrieve"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get workout volume aggregated by week.

    Useful for tracking training volume trends over time.

    Args:
        weeks: Number of weeks to retrieve (1-52)
        current_user: Authenticated user
        db: Database session

    Returns:
        List[WorkoutVolumeByWeek]: Weekly workout volumes
    """
    return analytics_crud.get_workout_volume_by_week(db, current_user.id, weeks)


@router.get("/volume/monthly", response_model=List[WorkoutVolumeByMonth])
def get_monthly_volume(
    months: int = Query(6, ge=1, le=24, description="Number of months to retrieve"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get workout volume aggregated by month.

    Useful for long-term progress tracking.

    Args:
        months: Number of months to retrieve (1-24)
        current_user: Authenticated user
        db: Database session

    Returns:
        List[WorkoutVolumeByMonth]: Monthly workout volumes
    """
    return analytics_crud.get_workout_volume_by_month(db, current_user.id, months)


# ===========================
# Personal Records Endpoints
# ===========================

@router.get("/records", response_model=List[PersonalRecord])
def get_personal_records(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of PRs to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get personal records for the current user.

    Returns the maximum weight achieved for each exercise.

    Args:
        limit: Maximum number of PRs to return (1-100)
        current_user: Authenticated user
        db: Database session

    Returns:
        List[PersonalRecord]: Personal records
    """
    return analytics_crud.get_personal_records(db, current_user.id, limit)


# ===========================
# Muscle Group Analytics
# ===========================

@router.get("/muscle-groups", response_model=List[MuscleGroupDistribution])
def get_muscle_group_distribution(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get muscle group distribution for the current user.

    Shows how training volume is distributed across different muscle groups.
    Useful for identifying imbalances in training.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        List[MuscleGroupDistribution]: Muscle group distribution
    """
    return analytics_crud.get_muscle_group_distribution(db, current_user.id)


# ===========================
# Insights Endpoints
# ===========================

@router.get("/insights", response_model=UserInsights)
def get_user_insights(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized insights and recommendations.

    Analyzes user data to provide actionable insights such as:
    - Recent achievements (new PRs, milestones)
    - Warnings (inactivity, imbalances)
    - Suggestions (exercise variety, consistency)

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        UserInsights: Personalized insights
    """
    insights = analytics_crud.generate_user_insights(db, current_user.id)

    return UserInsights(
        user_id=current_user.id,
        insights=insights,
        generated_at=datetime.utcnow()
    )


# ===========================
# Dashboard Endpoint
# ===========================

@router.get("/dashboard", response_model=AnalyticsDashboard)
def get_analytics_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get complete analytics dashboard for the current user.

    Returns all analytics data in a single response:
    - Progress summary
    - Recent volume trends (12 weeks)
    - Personal records
    - Muscle group distribution
    - Personalized insights

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        AnalyticsDashboard: Complete analytics dashboard
    """
    # Calculate workout streak (simplified version)
    # In production, you might want to create a separate function for this
    summary = analytics_crud.get_user_progress_summary(db, current_user.id)

    # Simple streak calculation
    from app.schemas.analytics_schema import WorkoutStreak
    workout_streak = WorkoutStreak(
        current_streak=0 if summary.recent_activity_days > 1 else 1,
        longest_streak=0,  # Would need separate calculation
        total_workout_days=summary.total_workouts,
        avg_workouts_per_week=0.0,  # Would need separate calculation
        consistency_score=0.0  # Would need separate calculation
    )

    return AnalyticsDashboard(
        user_id=current_user.id,
        progress_summary=summary,
        workout_streak=workout_streak,
        recent_volume_by_week=analytics_crud.get_workout_volume_by_week(db, current_user.id, 12),
        recent_personal_records=analytics_crud.get_personal_records(db, current_user.id, 5),
        muscle_group_distribution=analytics_crud.get_muscle_group_distribution(db, current_user.id),
        insights=analytics_crud.generate_user_insights(db, current_user.id),
        generated_at=datetime.utcnow()
    )


# ===========================
# Admin Endpoints
# ===========================

@router.post("/refresh-views", status_code=status.HTTP_204_NO_CONTENT)
def refresh_analytics_views(
    db: Session = Depends(get_db),
    current_superuser: User = Depends(get_current_superuser)
):
    """
    Refresh all materialized views (admin only).

    Should be called periodically to update analytics data.
    In production, this should be automated via cron job.

    Args:
        db: Database session
        current_superuser: Authenticated superuser

    Returns:
        204 No Content on success
    """
    analytics_crud.refresh_analytics_views(db)
    return None
