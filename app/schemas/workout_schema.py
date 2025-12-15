"""Workout logging schemas for API requests and responses."""
from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict


# ===========================
# Exercise Schemas
# ===========================

class ExerciseBase(BaseModel):
    """Base schema for Exercise."""
    name: str = Field(..., min_length=1, max_length=255)
    muscle_group: Optional[str] = Field(None, max_length=100)
    equipment_type: Optional[str] = Field(None, max_length=100)


class ExerciseCreate(ExerciseBase):
    """Schema for creating an exercise."""
    pass


class ExerciseUpdate(BaseModel):
    """Schema for updating an exercise."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    muscle_group: Optional[str] = Field(None, max_length=100)
    equipment_type: Optional[str] = Field(None, max_length=100)


class ExerciseResponse(ExerciseBase):
    """Schema for Exercise in API responses."""
    id: int

    model_config = ConfigDict(from_attributes=True)


# ===========================
# Log Exercise Schemas
# ===========================

class LogExerciseBase(BaseModel):
    """Base schema for LogExercise."""
    exercise_id: int = Field(..., gt=0)
    sets_completed: int = Field(..., ge=1, le=100, description="Number of sets")
    top_weight: float = Field(..., ge=0, description="Maximum weight used (kg)")
    total_reps: int = Field(..., ge=1, description="Total reps across all sets")


class LogExerciseCreate(LogExerciseBase):
    """Schema for creating a log exercise entry."""
    pass


class LogExerciseUpdate(BaseModel):
    """Schema for updating a log exercise entry."""
    exercise_id: Optional[int] = Field(None, gt=0)
    sets_completed: Optional[int] = Field(None, ge=1, le=100)
    top_weight: Optional[float] = Field(None, ge=0)
    total_reps: Optional[int] = Field(None, ge=1)


class LogExerciseResponse(LogExerciseBase):
    """Schema for LogExercise in API responses."""
    id: int
    session_id: int
    exercise: ExerciseResponse

    model_config = ConfigDict(from_attributes=True)


# ===========================
# Set-Level Tracking Schemas
# ===========================

class SetDetail(BaseModel):
    """Individual set details (for more granular tracking)."""
    set_number: int = Field(..., ge=1)
    reps: int = Field(..., ge=1)
    weight: float = Field(..., ge=0)
    rpe: Optional[int] = Field(None, ge=1, le=10, description="Rate of Perceived Exertion (1-10)")
    notes: Optional[str] = Field(None, max_length=500)


class LogExerciseWithSets(LogExerciseCreate):
    """Log exercise with individual set details."""
    sets: List[SetDetail] = Field(..., min_length=1)


# ===========================
# Workout Session Schemas
# ===========================

class WorkoutSessionBase(BaseModel):
    """Base schema for WorkoutSession."""
    workout_date: date = Field(default_factory=date.today)
    duration_minutes: Optional[int] = Field(None, ge=1, le=600, description="Duration in minutes")
    notes: Optional[str] = Field(None, max_length=2000)


class WorkoutSessionCreate(WorkoutSessionBase):
    """Schema for creating a workout session."""
    exercises: List[LogExerciseCreate] = Field(default_factory=list, description="Exercises logged in this session")


class WorkoutSessionUpdate(BaseModel):
    """Schema for updating a workout session."""
    workout_date: Optional[date] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=600)
    notes: Optional[str] = Field(None, max_length=2000)


class WorkoutSessionResponse(WorkoutSessionBase):
    """Schema for WorkoutSession in API responses."""
    id: int
    user_id: int
    exercises_done: List[LogExerciseResponse] = []

    model_config = ConfigDict(from_attributes=True)


class WorkoutSessionSummary(BaseModel):
    """Summary view of a workout session (without exercises)."""
    id: int
    user_id: int
    workout_date: date
    duration_minutes: Optional[int]
    notes: Optional[str]
    exercise_count: int
    total_volume: float

    model_config = ConfigDict(from_attributes=True)


# ===========================
# Quick Log Schemas
# ===========================

class QuickLogExercise(BaseModel):
    """Quick logging format - just exercise and sets."""
    exercise_id: int
    sets: List[SetDetail]


class QuickWorkoutLog(BaseModel):
    """Quick workout logging - minimal fields."""
    workout_date: Optional[date] = Field(default_factory=date.today)
    exercises: List[QuickLogExercise] = Field(..., min_length=1)
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None


# ===========================
# Workout History Schemas
# ===========================

class WorkoutHistoryFilters(BaseModel):
    """Filters for workout history."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    exercise_id: Optional[int] = None
    muscle_group: Optional[str] = None


class WorkoutStats(BaseModel):
    """Statistics for a workout or period."""
    total_workouts: int
    total_duration_minutes: int
    total_exercises_logged: int
    total_volume: float
    unique_exercises: int
    avg_workout_duration: float


# ===========================
# Template Schemas
# ===========================

class WorkoutTemplate(BaseModel):
    """Workout template for reusable routines."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    exercises: List[LogExerciseBase]


class WorkoutTemplateResponse(WorkoutTemplate):
    """Workout template in responses."""
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===========================
# Copy/Clone Schemas
# ===========================

class CopyWorkoutRequest(BaseModel):
    """Request to copy a previous workout."""
    source_workout_id: int
    new_date: Optional[date] = Field(default_factory=date.today)
    copy_notes: bool = False
