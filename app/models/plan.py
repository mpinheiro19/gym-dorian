"""Workout plan models using SQLAlchemy 2.0 syntax."""
from typing import Optional, TYPE_CHECKING
from datetime import date as date_type, datetime, timezone
from sqlalchemy import ForeignKey, Text, Date, UniqueConstraint, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from app.models.enums import PlanStatus

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.template import WorkoutTemplate


class WorkoutPlan(Base):
    """Represents a workout plan with rotating weekly cycles.

    A plan organises templates into weekly cycles that repeat indefinitely
    from ``start_date``. The current week in the cycle is calculated as:
    ``((days_since_start // 7) % total_weeks) + 1``.

    Attributes:
        id: Primary key identifier
        user_id: Foreign key to the owning User
        name: Plan name (e.g., "PPL 6-day — Volume Block")
        description: Optional longer description
        status: Current lifecycle status (active / queued / paused / completed / archived)
        start_date: Date the plan was activated; used to calculate the current cycle week
        created_at: Creation timestamp
        updated_at: Last-update timestamp
        user: Relationship to User
        weeks: Ordered list of PlanWeek rows
    """
    __tablename__ = "workout_plans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text(), default=None)
    status: Mapped[PlanStatus] = mapped_column(
        SQLEnum(PlanStatus, name="planstatus"),
        nullable=False,
        default=PlanStatus.QUEUED,
    )
    start_date: Mapped[Optional[date_type]] = mapped_column(Date(), default=None)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        default=None,
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="workout_plans")
    weeks: Mapped[list["PlanWeek"]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="PlanWeek.week_number",
    )


class PlanWeek(Base):
    """Represents one week within a WorkoutPlan cycle.

    Attributes:
        id: Primary key identifier
        plan_id: Foreign key to the parent WorkoutPlan (cascade delete)
        week_number: 1-indexed position within the cycle
        name: Optional label (e.g., "Heavy Week")
        plan: Relationship to the parent WorkoutPlan
        days: List of PlanDay rows for this week
    """
    __tablename__ = "plan_weeks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("workout_plans.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    week_number: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[Optional[str]] = mapped_column(default=None)

    # Relationships
    plan: Mapped["WorkoutPlan"] = relationship(back_populates="weeks")
    days: Mapped[list["PlanDay"]] = relationship(
        back_populates="week",
        cascade="all, delete-orphan",
        order_by="PlanDay.day_of_week",
    )


class PlanDay(Base):
    """Maps a day of the week to a WorkoutTemplate within a PlanWeek.

    ``day_of_week`` follows ISO 8601 / Python ``datetime.weekday()``:
    0 = Monday, 1 = Tuesday, …, 6 = Sunday.

    Days not present in a week are implicit rest days.

    A unique constraint on ``(week_id, day_of_week)`` enforces at most one
    template per calendar day per week.

    Attributes:
        id: Primary key identifier
        week_id: Foreign key to the parent PlanWeek (cascade delete)
        day_of_week: 0 (Monday) … 6 (Sunday)
        template_id: Foreign key to the WorkoutTemplate assigned to this day
        notes: Optional per-day notes
        week: Relationship to the parent PlanWeek
        template: Relationship to the WorkoutTemplate
    """
    __tablename__ = "plan_days"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    week_id: Mapped[int] = mapped_column(
        ForeignKey("plan_weeks.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    day_of_week: Mapped[int] = mapped_column(nullable=False)  # 0=Mon … 6=Sun
    template_id: Mapped[int] = mapped_column(
        ForeignKey("workout_templates.id", ondelete="CASCADE"),
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text(), default=None)

    # Unique: one template per day per week
    __table_args__ = (
        UniqueConstraint("week_id", "day_of_week", name="uq_plan_day_week_dow"),
    )

    # Relationships
    week: Mapped["PlanWeek"] = relationship(back_populates="days")
    template: Mapped["WorkoutTemplate"] = relationship()
