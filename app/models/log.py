"""Workout logging models using SQLAlchemy 2.0 syntax."""
from typing import Optional, TYPE_CHECKING
from datetime import date as date_type, datetime
from sqlalchemy import ForeignKey, Text, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, SyncMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.template import WorkoutTemplate
    from app.models.plan import WorkoutPlan


class WorkoutSession(TimestampMixin, SyncMixin, Base):
    """Represents a complete workout session.

    Attributes:
        id: Primary key identifier
        user_id: Foreign key to User who performed the workout
        workout_date: Date when workout was performed
        duration_minutes: Total workout duration in minutes
        notes: Additional notes about the workout
        client_uuid: Client-generated UUID for offline sync
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
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

    # Traceability — nullable FK to template and plan that originated this session
    template_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('workout_templates.id', ondelete='SET NULL'),
        default=None,
        index=True
    )
    plan_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('workout_plans.id', ondelete='SET NULL'),
        default=None,
        index=True
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="workout_sessions")
    template: Mapped[Optional["WorkoutTemplate"]] = relationship(foreign_keys=[template_id])
    plan: Mapped[Optional["WorkoutPlan"]] = relationship(foreign_keys=[plan_id])
    exercises_done: Mapped[list["LogExercise"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan"
    )

    # Computed properties used by WorkoutSessionSummary schema
    @property
    def exercise_count(self) -> int:
        """Number of distinct exercises logged in this session."""
        return len(self.exercises_done)

    @property
    def total_volume(self) -> float:
        """Total volume (sum of reps * weight across all exercises and sets)."""
        return sum(
            s.reps * s.weight
            for le in self.exercises_done
            for s in le.sets
        )


class LogExercise(TimestampMixin, SyncMixin, Base):
    """Represents a logged exercise within a workout session.

    Attributes:
        id: Primary key identifier
        session_id: Foreign key to WorkoutSession
        exercise_id: Foreign key to Exercise
        client_uuid: Client-generated UUID for offline sync
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
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


class LogSet(TimestampMixin, SyncMixin, Base):
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
        client_uuid: Client-generated UUID for offline sync
        created_at: Timestamp when record was created
        updated_at: Timestamp when record was last updated
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