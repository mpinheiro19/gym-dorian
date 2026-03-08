"""Workout template models using SQLAlchemy 2.0 syntax."""
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.exercise import Exercise


class WorkoutTemplate(Base):
    """Represents a reusable workout template.

    Attributes:
        id: Primary key identifier
        user_id: Foreign key to User who owns the template
        name: Template name (e.g., "Treino A - Peito e Tríceps")
        description: Optional description of the template
        created_at: Timestamp when template was created
        updated_at: Timestamp when template was last updated
        user: Relationship to User
        exercises: Relationship to exercises in this template (ordered by order_index)
    """
    __tablename__ = 'workout_templates'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        index=True,
        nullable=False
    )
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text(), default=None)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        default=None,
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="workout_templates")
    exercises: Mapped[list["TemplateExercise"]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="TemplateExercise.order_index"
    )


class TemplateExercise(Base):
    """Represents an exercise within a workout template.

    Attributes:
        id: Primary key identifier
        template_id: Foreign key to WorkoutTemplate
        exercise_id: Foreign key to Exercise
        order_index: Order of this exercise in the template (0, 1, 2, ...)
        target_sets: Suggested number of sets for this exercise
        notes: Optional notes or instructions for this exercise
        template: Relationship to the parent WorkoutTemplate
        exercise: Relationship to the Exercise definition
    """
    __tablename__ = 'template_exercises'

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(
        ForeignKey('workout_templates.id', ondelete='CASCADE'),
        index=True,
        nullable=False
    )
    exercise_id: Mapped[int] = mapped_column(ForeignKey('exercises.id'))
    order_index: Mapped[int] = mapped_column(nullable=False)
    target_sets: Mapped[Optional[int]] = mapped_column(default=None)
    notes: Mapped[Optional[str]] = mapped_column(Text(), default=None)

    # Relationships
    template: Mapped["WorkoutTemplate"] = relationship(back_populates="exercises")
    exercise: Mapped["Exercise"] = relationship()
