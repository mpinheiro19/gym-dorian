"""CRUD operations for workout plans."""
from typing import Optional, List
from datetime import date, datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from app.models.plan import WorkoutPlan, PlanWeek, PlanDay
from app.models.enums import PlanStatus
from app.schemas.plan_schema import (
    WorkoutPlanCreate,
    WorkoutPlanUpdate,
    PlanStatusUpdate,
)


# ===========================
# Read helpers
# ===========================

def _plan_with_eager(db: Session, plan_id: int) -> Optional[WorkoutPlan]:
    """Load a plan with all weeks→days→template eagerly."""
    return db.query(WorkoutPlan).options(
        joinedload(WorkoutPlan.weeks)
        .joinedload(PlanWeek.days)
        .joinedload(PlanDay.template)
    ).filter(WorkoutPlan.id == plan_id).first()


def get_plan_by_id(db: Session, plan_id: int, user_id: int) -> Optional[WorkoutPlan]:
    """Get a plan by ID with ownership check and eager-loaded schedule.

    Args:
        db: Database session
        plan_id: Plan primary key
        user_id: Requesting user \u2014 must own the plan

    Returns:
        WorkoutPlan with weeks/days loaded, or None
    """
    return db.query(WorkoutPlan).options(
        joinedload(WorkoutPlan.weeks)
        .joinedload(PlanWeek.days)
        .joinedload(PlanDay.template)
    ).filter(
        WorkoutPlan.id == plan_id,
        WorkoutPlan.user_id == user_id,
    ).first()


def get_user_plans(
    db: Session,
    user_id: int,
    status: Optional[PlanStatus] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[WorkoutPlan]:
    """List plans for a user with optional status filter.

    Args:
        db: Database session
        user_id: Requesting user
        status: Optional status filter
        skip: Pagination offset
        limit: Max records

    Returns:
        List of WorkoutPlan (without eager-loaded weeks to keep it light)
    """
    query = db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user_id)
    if status is not None:
        query = query.filter(WorkoutPlan.status == status)
    return query.order_by(WorkoutPlan.created_at.desc()).offset(skip).limit(limit).all()


def get_active_plans(db: Session, user_id: int) -> List[WorkoutPlan]:
    """Return all active plans for a user (typically 0 or 1)."""
    return db.query(WorkoutPlan).filter(
        WorkoutPlan.user_id == user_id,
        WorkoutPlan.status == PlanStatus.ACTIVE,
    ).all()


# ===========================
# Write helpers
# ===========================

def _build_weeks_days(db: Session, plan: WorkoutPlan, weeks_data: list) -> None:
    """Bulk-create PlanWeek and PlanDay rows for a plan (no commit)."""
    for week_data in weeks_data:
        week = PlanWeek(
            plan_id=plan.id,
            week_number=week_data.week_number,
            name=week_data.name,
        )
        db.add(week)
        db.flush()
        for day_data in week_data.days:
            day = PlanDay(
                week_id=week.id,
                day_of_week=day_data.day_of_week,
                template_id=day_data.template_id,
                notes=day_data.notes,
            )
            db.add(day)


def create_plan(db: Session, user_id: int, plan_in: WorkoutPlanCreate) -> WorkoutPlan:
    """Create a WorkoutPlan with its weeks and days in a single transaction.

    Args:
        db: Database session (caller must commit or use begin())
        user_id: Owning user
        plan_in: Validated creation payload

    Returns:
        Persisted WorkoutPlan with eager-loaded schedule
    """
    plan = WorkoutPlan(
        user_id=user_id,
        name=plan_in.name,
        description=plan_in.description,
        status=PlanStatus.QUEUED,
    )
    db.add(plan)
    db.flush()  # Obtain plan.id

    _build_weeks_days(db, plan, plan_in.weeks)

    db.commit()
    db.refresh(plan)
    # Re-query with eager loading for a clean response
    return _plan_with_eager(db, plan.id)


def update_plan(
    db: Session,
    plan: WorkoutPlan,
    plan_in: WorkoutPlanUpdate,
) -> WorkoutPlan:
    """Update scalar fields and optionally replace the full week/day schedule.

    When ``weeks`` is provided the existing schedule is deleted and rebuilt.

    Args:
        db: Database session
        plan: Existing WorkoutPlan instance (owned by requesting user)
        plan_in: Update payload

    Returns:
        Updated WorkoutPlan with eager-loaded schedule
    """
    update_data = plan_in.model_dump(exclude_unset=True)

    # Handle schedule replacement
    if "weeks" in update_data and plan_in.weeks is not None:
        # Delete all existing weeks (cascade removes days)
        for week in list(plan.weeks):
            db.delete(week)
        db.flush()
        _build_weeks_days(db, plan, plan_in.weeks)
        update_data.pop("weeks")

    for field, value in update_data.items():
        setattr(plan, field, value)

    plan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(plan)
    return _plan_with_eager(db, plan.id)


def delete_plan(db: Session, plan: WorkoutPlan) -> None:
    """Delete a plan (cascade removes all weeks/days).

    Args:
        db: Database session
        plan: Plan to delete
    """
    db.delete(plan)
    db.commit()


def update_plan_status(
    db: Session,
    plan: WorkoutPlan,
    new_status: PlanStatus,
) -> WorkoutPlan:
    """Change the status of a plan and set start_date when activating.

    Allowed transitions:
    - queued → active, archived
    - active → paused, completed, archived
    - paused → active, archived
    - completed → archived
    - archived → (terminal, no transitions)

    Args:
        db: Database session
        plan: Existing plan
        new_status: Target status

    Returns:
        Updated plan

    Raises:
        ValueError: If transition is not allowed
    """
    ALLOWED_TRANSITIONS: dict[PlanStatus, set[PlanStatus]] = {
        PlanStatus.QUEUED: {PlanStatus.ACTIVE, PlanStatus.ARCHIVED},
        PlanStatus.ACTIVE: {PlanStatus.PAUSED, PlanStatus.COMPLETED, PlanStatus.ARCHIVED},
        PlanStatus.PAUSED: {PlanStatus.ACTIVE, PlanStatus.ARCHIVED},
        PlanStatus.COMPLETED: {PlanStatus.ARCHIVED},
        PlanStatus.ARCHIVED: set(),
    }

    allowed = ALLOWED_TRANSITIONS.get(plan.status, set())
    if new_status not in allowed:
        raise ValueError(
            f"Cannot transition plan from '{plan.status.value}' to '{new_status.value}'. "
            f"Allowed: {[s.value for s in allowed] or 'none (terminal state)'}"
        )

    plan.status = new_status

    # Set start_date the first time a plan is activated
    if new_status == PlanStatus.ACTIVE and plan.start_date is None:
        plan.start_date = date.today()

    plan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(plan)
    return plan
