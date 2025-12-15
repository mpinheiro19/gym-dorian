"""
SQLAlchemy models package.

All models must be imported here to ensure they are registered
with SQLAlchemy's Base class and discovered by Alembic migrations.
"""
from app.models.base import Base
from app.models.user import (
    User,
    UserSettings,
    UserGoal,
    WeightUnit,
    DistanceUnit,
    GoalType,
    GoalStatus,
)
from app.models.exercise import Exercise
from app.models.log import WorkoutSession, LogExercise

__all__ = [
    # Base
    "Base",
    # User models
    "User",
    "UserSettings",
    "UserGoal",
    # User enums
    "WeightUnit",
    "DistanceUnit",
    "GoalType",
    "GoalStatus",
    # Exercise models
    "Exercise",
    # Workout logging models
    "WorkoutSession",
    "LogExercise",
]
