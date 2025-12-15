"""Workout logging models using SQLAlchemy 2.0 syntax."""
from typing import Optional, TYPE_CHECKING
from datetime import date as date_type, datetime
from sqlalchemy import ForeignKey, Text, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class WorkoutSession(Base):
    """Represents a complete workout session.

    Attributes:
        id: Primary key identifier
        user_id: Foreign key to User who performed the workout
        workout_date: Date when workout was performed
        duration_minutes: Total workout duration in minutes
        notes: Additional notes about the workout
        user: Relationship to User
        exercises_done: Relationship to logged exercises in this session
    """
    __tablename__ = 'workout_sessions'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        index=True,
        nullable=False
    )
    workout_date: Mapped[date_type] = mapped_column(Date, default=lambda: datetime.utcnow().date())
    duration_minutes: Mapped[Optional[int]] = mapped_column(default=None)
    notes: Mapped[Optional[str]] = mapped_column(Text(), default=None)

    # Relationships
    user: Mapped["User"] = relationship()
    exercises_done: Mapped[list["LogExercise"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan"
    )


class LogExercise(Base):
    """Represents a logged exercise within a workout session.
    
    Attributes:
        id: Primary key identifier
        session_id: Foreign key to WorkoutSession
        exercise_id: Foreign key to Exercise
        sets_completed: Number of sets completed
        top_weight: Maximum weight used (in kg or lbs)
        total_reps: Total repetitions across all sets
        session: Relationship to the parent WorkoutSession
        exercise: Relationship to the Exercise definition
    """
    __tablename__ = 'log_exercises'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey('workout_sessions.id'))
    exercise_id: Mapped[int] = mapped_column(ForeignKey('exercises.id'))
    
    sets_completed: Mapped[int]
    top_weight: Mapped[float]
    total_reps: Mapped[int]
    
    session: Mapped["WorkoutSession"] = relationship(back_populates="exercises_done")
    exercise: Mapped["Exercise"] = relationship()