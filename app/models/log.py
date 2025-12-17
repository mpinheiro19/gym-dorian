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
    user: Mapped["User"] = relationship(back_populates="workout_sessions")
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
        session: Relationship to the parent WorkoutSession
        exercise: Relationship to the Exercise definition
        sets: Relationship to individual sets performed
    """
    __tablename__ = 'log_exercises'

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey('workout_sessions.id'))
    exercise_id: Mapped[int] = mapped_column(ForeignKey('exercises.id'))

    session: Mapped["WorkoutSession"] = relationship(back_populates="exercises_done")
    exercise: Mapped["Exercise"] = relationship()
    sets: Mapped[list["LogSet"]] = relationship(
        back_populates="log_exercise",
        cascade="all, delete-orphan",
        order_by="LogSet.set_number"
    )

    # Computed properties for backward compatibility
    @property
    def sets_completed(self) -> int:
        """Calculate number of sets from sets relationship."""
        return len(self.sets)

    @property
    def top_weight(self) -> float:
        """Calculate maximum weight from sets."""
        return max((s.weight for s in self.sets), default=0.0)

    @property
    def total_reps(self) -> int:
        """Calculate total reps from sets."""
        return sum(s.reps for s in self.sets)

    @property
    def total_volume(self) -> float:
        """Calculate total volume (reps * weight summed across sets)."""
        return sum(s.reps * s.weight for s in self.sets)


class LogSet(Base):
    """Represents a single set within a logged exercise.

    Attributes:
        id: Primary key identifier
        log_exercise_id: Foreign key to LogExercise
        set_number: The sequence number of this set (1, 2, 3, ...)
        reps: Number of repetitions performed
        weight: Weight used in this set (kg or lbs)
        rpe: Optional Rate of Perceived Exertion (1-10 scale)
        notes: Optional notes about this specific set
        rest_time_seconds: Optional rest time after this set in seconds
        log_exercise: Relationship to the parent LogExercise
    """
    __tablename__ = 'log_sets'

    id: Mapped[int] = mapped_column(primary_key=True)
    log_exercise_id: Mapped[int] = mapped_column(
        ForeignKey('log_exercises.id', ondelete='CASCADE'),
        index=True,
        nullable=False
    )

    # Required fields
    set_number: Mapped[int] = mapped_column(nullable=False)
    reps: Mapped[int] = mapped_column(nullable=False)
    weight: Mapped[float] = mapped_column(nullable=False)

    # Optional fields
    rpe: Mapped[Optional[int]] = mapped_column(default=None)
    notes: Mapped[Optional[str]] = mapped_column(Text(), default=None)
    rest_time_seconds: Mapped[Optional[int]] = mapped_column(default=None)

    # Relationships
    log_exercise: Mapped["LogExercise"] = relationship(back_populates="sets")