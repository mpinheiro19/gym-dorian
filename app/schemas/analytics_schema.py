"""Analytics schemas for workout progress tracking and insights."""
from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict


# ===========================
# Exercise Progress Schemas
# ===========================

class ExerciseProgressPoint(BaseModel):
    """Single data point for exercise progress over time."""
    workout_date: date
    max_weight: float
    total_reps: int
    total_sets: int
    volume: float  # total_reps * max_weight

    model_config = ConfigDict(from_attributes=True)


class ExerciseProgressResponse(BaseModel):
    """Exercise progress tracking over time for a user."""
    exercise_id: int
    exercise_name: str
    muscle_group: Optional[str]
    data_points: List[ExerciseProgressPoint]

    # Summary statistics
    first_workout: date
    last_workout: date
    total_workouts: int
    starting_weight: float
    current_weight: float
    weight_gain: float
    weight_gain_percentage: float


class UserProgressSummary(BaseModel):
    """Summary of user's overall progress."""
    user_id: int
    total_workouts: int
    total_exercises: int
    total_workout_minutes: int
    avg_workout_duration: float
    total_volume: float  # Sum of all reps * weight
    exercises_by_muscle_group: dict[str, int]
    most_frequent_exercise: Optional[str]
    recent_activity_days: int  # Days since last workout


# ===========================
# Workout Analytics Schemas
# ===========================

class WorkoutVolumeByWeek(BaseModel):
    """Weekly workout volume tracking."""
    week_start: date
    workout_count: int
    total_duration_minutes: int
    total_volume: float
    unique_exercises: int
    avg_workout_duration: float

    model_config = ConfigDict(from_attributes=True)


class WorkoutVolumeByMonth(BaseModel):
    """Monthly workout volume tracking."""
    month_start: date
    workout_count: int
    total_duration_minutes: int
    total_volume: float
    unique_exercises: int
    avg_workout_duration: float

    model_config = ConfigDict(from_attributes=True)


class MuscleGroupDistribution(BaseModel):
    """Distribution of workouts by muscle group."""
    muscle_group: str
    exercise_count: int
    total_sets: int
    total_volume: float
    percentage: float


# ===========================
# Personal Records Schemas
# ===========================

class PersonalRecord(BaseModel):
    """Personal record for an exercise."""
    exercise_id: int
    exercise_name: str
    muscle_group: Optional[str]
    max_weight: float
    reps_at_max: int
    achieved_date: date
    days_ago: int

    model_config = ConfigDict(from_attributes=True)


class PersonalRecordHistory(BaseModel):
    """History of PRs for an exercise."""
    exercise_id: int
    exercise_name: str
    records: List[PersonalRecord]


# ===========================
# Consistency & Streaks Schemas
# ===========================

class WorkoutStreak(BaseModel):
    """Workout consistency streak information."""
    current_streak: int  # Days
    longest_streak: int  # Days
    total_workout_days: int
    avg_workouts_per_week: float
    consistency_score: float  # 0-100


class WorkoutFrequency(BaseModel):
    """Workout frequency by day of week."""
    day_of_week: str
    workout_count: int
    percentage: float


# ===========================
# Comparison & Trends Schemas
# ===========================

class ExerciseTrend(BaseModel):
    """Trend analysis for an exercise."""
    exercise_id: int
    exercise_name: str
    period_days: int
    starting_weight: float
    ending_weight: float
    weight_change: float
    weight_change_percentage: float
    volume_change_percentage: float
    trend: str  # "improving", "stable", "declining"


class PeriodComparison(BaseModel):
    """Compare two time periods."""
    period1_start: date
    period1_end: date
    period2_start: date
    period2_end: date

    period1_workouts: int
    period2_workouts: int
    workout_change: int
    workout_change_percentage: float

    period1_volume: float
    period2_volume: float
    volume_change: float
    volume_change_percentage: float

    period1_avg_duration: float
    period2_avg_duration: float


# ===========================
# Goal Progress Schemas
# ===========================

class GoalProgressPoint(BaseModel):
    """Progress point towards a goal."""
    date: date
    current_value: float
    target_value: float
    progress_percentage: float


class GoalProgressTracking(BaseModel):
    """Detailed goal progress tracking."""
    goal_id: int
    goal_type: str
    title: str
    created_date: datetime
    target_date: Optional[datetime]
    target_value: Optional[float]
    current_value: Optional[float]
    progress_percentage: float
    days_remaining: Optional[int]
    on_track: bool
    progress_history: List[GoalProgressPoint]


# ===========================
# Leaderboard Schemas
# ===========================

class LeaderboardEntry(BaseModel):
    """Entry in a leaderboard."""
    rank: int
    user_id: int
    user_name: str
    value: float
    workouts: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class Leaderboard(BaseModel):
    """Leaderboard for various metrics."""
    metric: str  # "total_volume", "workout_count", "consistency", etc.
    period: str  # "all_time", "this_month", "this_week"
    entries: List[LeaderboardEntry]


# ===========================
# Insights & Recommendations
# ===========================

class WorkoutInsight(BaseModel):
    """Actionable insight about workouts."""
    type: str  # "achievement", "warning", "suggestion", "milestone"
    title: str
    description: str
    insight_date: Optional[date] = Field(default=None, description="Date related to this insight")
    priority: int  # 1-5

    model_config = ConfigDict(from_attributes=True)


class UserInsights(BaseModel):
    """Collection of insights for a user."""
    user_id: int
    insights: List[WorkoutInsight]
    generated_at: datetime


# ===========================
# Analytics Dashboard Schema
# ===========================

class AnalyticsDashboard(BaseModel):
    """Complete analytics dashboard for a user."""
    user_id: int

    # Overview
    progress_summary: UserProgressSummary
    workout_streak: WorkoutStreak

    # Recent activity (last 12 weeks)
    recent_volume_by_week: List[WorkoutVolumeByWeek]

    # Personal records (top 5)
    recent_personal_records: List[PersonalRecord]

    # Muscle group distribution
    muscle_group_distribution: List[MuscleGroupDistribution]

    # Insights
    insights: List[WorkoutInsight]

    generated_at: datetime
