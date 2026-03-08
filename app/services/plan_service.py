"""Business logic for workout plans — cycle calculation, today's workout, and validations."""
from datetime import date
from typing import Optional, Union

from sqlalchemy.orm import Session

from app.models.plan import WorkoutPlan, PlanWeek, PlanDay
from app.models.enums import PlanStatus
from app.schemas.plan_schema import (
    TodayWorkoutResponse,
    RestDayResponse,
    WorkoutPlanCreate,
)
from app.crud import plan as plan_crud

# ISO 8601 day names aligned with Python datetime.weekday() (0=Monday)
_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ===========================
# Cycle logic
# ===========================

def current_week_number(plan: WorkoutPlan, reference: Optional[date] = None) -> int:
    """Calculate which week of the cycle is current.

    Uses the formula: ``((days_since_start // 7) % total_weeks) + 1``.

    Args:
        plan: An active WorkoutPlan with ``start_date`` set.
        reference: Date to evaluate against (defaults to today).

    Returns:
        1-indexed week number within the cycle.

    Raises:
        ValueError: If ``plan.start_date`` is None.
    """
    if plan.start_date is None:
        raise ValueError("Cannot calculate cycle week: plan has no start_date.")
    if not plan.weeks:
        raise ValueError("Plan has no weeks defined.")

    ref = reference or date.today()
    days_elapsed = (ref - plan.start_date).days
    total_weeks = len(plan.weeks)
    week_index = (days_elapsed // 7) % total_weeks   # 0-indexed
    return week_index + 1  # 1-indexed


def get_today_workout(
    plan: WorkoutPlan,
    reference: Optional[date] = None,
) -> Union[TodayWorkoutResponse, RestDayResponse]:
    """Return the template scheduled for *today* (or ``reference``) in the plan.

    Args:
        plan: An active WorkoutPlan with ``start_date`` set and weeks/days loaded.
        reference: Date to evaluate (defaults to today).

    Returns:
        ``TodayWorkoutResponse`` if a template is scheduled, else ``RestDayResponse``.
    """
    ref = reference or date.today()
    week_num = current_week_number(plan, ref)
    dow = ref.weekday()  # 0=Monday … 6=Sunday
    day_name = _DAY_NAMES[dow]

    # Locate the matching week
    week: Optional[PlanWeek] = next(
        (w for w in plan.weeks if w.week_number == week_num), None
    )

    plan_day: Optional[PlanDay] = None
    if week:
        plan_day = next((d for d in week.days if d.day_of_week == dow), None)

    if plan_day is None:
        return RestDayResponse(
            plan_id=plan.id,
            plan_name=plan.name,
            week_number=week_num,
            day_of_week=dow,
            day_name=day_name,
            is_rest_day=True,
        )

    return TodayWorkoutResponse(
        plan_id=plan.id,
        plan_name=plan.name,
        week_number=week_num,
        day_of_week=dow,
        day_name=day_name,
        template_id=plan_day.template_id,
        template_name=plan_day.template.name if plan_day.template else "",
        template_description=plan_day.template.description if plan_day.template else None,
        is_rest_day=False,
    )


# ===========================
# Validation helpers
# ===========================

def validate_plan_ownership(plan: Optional[WorkoutPlan], user_id: int) -> WorkoutPlan:
    """Raise ValueError if plan is None or owned by a different user.

    Args:
        plan: Queried plan (may be None).
        user_id: Requesting user.

    Returns:
        The same plan if valid.

    Raises:
        ValueError: Plan not found or not owned by this user.
    """
    if plan is None or plan.user_id != user_id:
        raise ValueError("Plan not found.")
    return plan


def validate_templates_belong_to_user(
    plan_in: WorkoutPlanCreate,
    user_template_ids: set[int],
) -> None:
    """Ensure every template_id in the plan belongs to the requesting user.

    Args:
        plan_in: Create payload.
        user_template_ids: Set of template IDs the user owns.

    Raises:
        ValueError: If any template_id is not owned by the user.
    """
    for week in plan_in.weeks:
        for day in week.days:
            if day.template_id not in user_template_ids:
                raise ValueError(
                    f"Template {day.template_id} does not belong to the current user."
                )


# ===========================
# High-level service operations
# ===========================

def create_plan_for_user(
    db: Session,
    user_id: int,
    plan_in: WorkoutPlanCreate,
) -> WorkoutPlan:
    """Create a plan after validating template ownership.

    Args:
        db: Database session
        user_id: Owning user
        plan_in: Validated create payload

    Returns:
        New WorkoutPlan

    Raises:
        ValueError: If any referenced template is not owned by the user.
    """
    from app.models.template import WorkoutTemplate
    owned_templates = {
        t.id
        for t in db.query(WorkoutTemplate.id).filter(WorkoutTemplate.user_id == user_id).all()
    }
    validate_templates_belong_to_user(plan_in, owned_templates)
    return plan_crud.create_plan(db, user_id, plan_in)


def get_active_today_workout(
    db: Session,
    user_id: int,
    reference: Optional[date] = None,
) -> Optional[Union[TodayWorkoutResponse, RestDayResponse]]:
    """Return today's workout from the user's first active plan.

    Returns ``None`` if no active plan exists.

    Args:
        db: Database session
        user_id: Requesting user
        reference: Date to evaluate (defaults to today)
    """
    active_plans = plan_crud.get_active_plans(db, user_id)
    if not active_plans:
        return None
    # Use the first active plan (users typically have one)
    plan = active_plans[0]
    # Reload with eager loading for template names
    full_plan = plan_crud.get_plan_by_id(db, plan.id, user_id)
    if full_plan is None:
        return None
    return get_today_workout(full_plan, reference)
