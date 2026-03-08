"""Workout logging schemas for API requests and responses."""
from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.models.enums import MuscleGroup


# ===========================
# Exercise Schemas
# ===========================

class ExerciseBase(BaseModel):
    """Base schema for Exercise."""
    name: str = Field(..., min_length=1, max_length=255)
    agonist_muscle_group: Optional[MuscleGroup] = Field(None, description="Primary muscle group")
    synergist_muscle_group: Optional[MuscleGroup] = Field(None, description="Assisting muscle group")
    equipment_type: Optional[str] = Field(None, max_length=100)


class ExerciseCreate(ExerciseBase):
    """Schema for creating an exercise."""
    pass


class ExerciseUpdate(BaseModel):
    """Schema for updating an exercise."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    agonist_muscle_group: Optional[MuscleGroup] = Field(None, description="Primary muscle group")
    synergist_muscle_group: Optional[MuscleGroup] = Field(None, description="Assisting muscle group")
    equipment_type: Optional[str] = Field(None, max_length=100)


class ExerciseResponse(ExerciseBase):
    """Schema for Exercise in API responses."""
    id: int

    model_config = ConfigDict(from_attributes=True)


# ===========================
# Log Exercise Schemas
# ===========================

class LogExerciseCreate(BaseModel):
    """Schema for creating a log exercise entry."""
    exercise_id: int = Field(..., gt=0)
    sets: List['SetDetail'] = Field(..., min_length=1)


class LogExerciseUpdate(BaseModel):
    """Schema for updating a log exercise entry."""
    exercise_id: Optional[int] = Field(None, gt=0)
    sets: Optional[List['SetDetail']] = Field(None, min_length=1)


class LogExerciseResponse(BaseModel):
    """Schema for LogExercise in API responses."""
    id: int
    session_id: int
    exercise: ExerciseResponse
    sets: List['SetDetailResponse'] = []

    # Computed fields (from model properties)
    sets_completed: int
    top_weight: float
    total_reps: int
    total_volume: float

    model_config = ConfigDict(from_attributes=True)


# ===========================
# Set-Level Tracking Schemas
# ===========================

class SetDetail(BaseModel):
    """Individual set details (for more granular tracking)."""
    set_number: int = Field(..., ge=1, le=100)
    reps: int = Field(..., ge=1, le=1000)
    weight: float = Field(..., ge=0, le=10000)
    rpe: Optional[int] = Field(None, ge=1, le=10, description="Rate of Perceived Exertion (1-10)")
    notes: Optional[str] = Field(None, max_length=500)
    rest_time_seconds: Optional[int] = Field(None, ge=0, le=3600, description="Rest time after set in seconds")


class SetDetailResponse(SetDetail):
    """Set detail with database ID for responses."""
    id: int
    log_exercise_id: int

    model_config = ConfigDict(from_attributes=True)


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
    # Optional traceability fields — set when session originates from a template or plan
    template_id: Optional[int] = Field(None, gt=0, description="Template this session was started from")
    plan_id: Optional[int] = Field(None, gt=0, description="Plan this session belongs to")


class WorkoutSessionUpdate(BaseModel):
    """Schema for updating a workout session."""
    workout_date: Optional[date] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=600)
    notes: Optional[str] = Field(None, max_length=2000)
    template_id: Optional[int] = Field(None, gt=0)
    plan_id: Optional[int] = Field(None, gt=0)


class WorkoutSessionResponse(WorkoutSessionBase):
    """Schema for WorkoutSession in API responses."""
    id: int
    user_id: int
    template_id: Optional[int] = None
    plan_id: Optional[int] = None
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
# Template Exercise Schemas
# ===========================

class TemplateExerciseBase(BaseModel):
    """Base schema for exercise in template."""
    exercise_id: int = Field(..., gt=0)
    order_index: int = Field(..., ge=0)
    target_sets: Optional[int] = Field(None, ge=1, le=20)
    notes: Optional[str] = Field(None, max_length=500)


class TemplateExerciseCreate(TemplateExerciseBase):
    """Schema for creating template exercise."""
    pass


class TemplateExerciseResponse(TemplateExerciseBase):
    """Template exercise in responses."""
    id: int
    template_id: int
    exercise: ExerciseResponse

    model_config = ConfigDict(from_attributes=True)


# ===========================
# Workout Template Schemas
# ===========================

class WorkoutTemplateBase(BaseModel):
    """Base schema for workout template."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class WorkoutTemplateCreate(WorkoutTemplateBase):
    """Schema for creating workout template."""
    exercises: List[TemplateExerciseCreate] = Field(..., min_length=1)


class WorkoutTemplateUpdate(BaseModel):
    """Schema for updating workout template."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    exercises: Optional[List[TemplateExerciseCreate]] = None


class WorkoutTemplateResponse(WorkoutTemplateBase):
    """Workout template in responses."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    exercises: List[TemplateExerciseResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ===========================
# Template Execution Schemas
# ===========================

class ExecuteTemplateRequest(BaseModel):
    """Request to execute a template and prepare workout."""
    template_id: int = Field(..., gt=0)
    workout_date: Optional[date] = Field(default_factory=date.today)


# ===========================
# Copy/Clone Schemas
# ===========================

class CopyWorkoutRequest(BaseModel):
    """Request to copy a previous workout."""
    source_workout_id: int
    new_date: Optional[date] = Field(default_factory=date.today)
    copy_notes: bool = False
