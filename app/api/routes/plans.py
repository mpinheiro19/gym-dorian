"""Workout plan routes — CRUD, status transitions, and today's workout."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.dependencies.auth import get_current_active_user
from app.models.user import User
from app.models.enums import PlanStatus
from app.crud import plan as plan_crud
from app.crud import workout as workout_crud
from app.services import plan_service
from app.schemas.plan_schema import (
    WorkoutPlanCreate,
    WorkoutPlanUpdate,
    WorkoutPlanResponse,
    WorkoutPlanSummary,
    PlanStatusUpdate,
    TodayWorkoutResponse,
    RestDayResponse,
)
from app.schemas.workout_schema import WorkoutSessionResponse, WorkoutSessionCreate

router = APIRouter(prefix="/plans", tags=["Workout Plans"])


# ===========================
# List & Detail
# ===========================

@router.get("", response_model=List[WorkoutPlanSummary])
def list_plans(
    status: Optional[PlanStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all workout plans for the current user.

    Supports optional filtering by ``status`` and pagination.
    Returns lightweight summaries without the full week/day tree.
    """
    plans = plan_crud.get_user_plans(db, current_user.id, status, skip, limit)
    # Enrich summaries with total_weeks count
    summaries = []
    for p in plans:
        summaries.append(
            WorkoutPlanSummary(
                id=p.id,
                name=p.name,
                description=p.description,
                status=p.status,
                start_date=p.start_date,
                total_weeks=len(p.weeks) if p.weeks else 0,
                created_at=p.created_at,
            )
        )
    return summaries


@router.get("/active/today")
def get_active_plan_today(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return today's scheduled workout from the user's active plan.

    Intended for the dashboard widget. Returns a ``TodayWorkoutResponse``
    when a template is scheduled or a ``RestDayResponse`` on rest days.
    Returns ``null`` (HTTP 204) when no active plan exists.
    """
    result = plan_service.get_active_today_workout(db, current_user.id)
    if result is None:
        return None
    return result


@router.get("/{plan_id}", response_model=WorkoutPlanResponse)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get full plan detail including nested weeks and days."""
    plan = plan_crud.get_plan_by_id(db, plan_id, current_user.id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found.")
    return plan


# ===========================
# Create / Update / Delete
# ===========================

@router.post("", response_model=WorkoutPlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(
    plan_in: WorkoutPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new workout plan with nested weeks and days.

    All ``template_id`` values must belong to the current user.
    """
    try:
        plan = plan_service.create_plan_for_user(db, current_user.id, plan_in)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return plan


@router.put("/{plan_id}", response_model=WorkoutPlanResponse)
def update_plan(
    plan_id: int,
    plan_in: WorkoutPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Update plan metadata or replace the entire week/day schedule.

    Providing ``weeks`` replaces the whole schedule.
    """
    plan = plan_crud.get_plan_by_id(db, plan_id, current_user.id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found.")

    # Validate template ownership when schedule is being replaced
    if plan_in.weeks is not None:
        try:
            from app.models.template import WorkoutTemplate
            owned_ids = {
                t.id
                for t in db.query(WorkoutTemplate.id)
                .filter(WorkoutTemplate.user_id == current_user.id)
                .all()
            }
            for week in plan_in.weeks:
                for day in week.days:
                    if day.template_id not in owned_ids:
                        raise ValueError(f"Template {day.template_id} does not belong to you.")
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return plan_crud.update_plan(db, plan, plan_in)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a plan and its entire schedule (cascade)."""
    plan = plan_crud.get_plan_by_id(db, plan_id, current_user.id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found.")
    plan_crud.delete_plan(db, plan)


# ===========================
# Status transition
# ===========================

@router.patch("/{plan_id}/status", response_model=WorkoutPlanResponse)
def update_plan_status(
    plan_id: int,
    status_in: PlanStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Change the status of a plan (activate, pause, complete, archive).

    Returns the updated plan. Invalid transitions return HTTP 400.
    """
    plan = plan_crud.get_plan_by_id(db, plan_id, current_user.id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found.")
    try:
        updated = plan_crud.update_plan_status(db, plan, status_in.status)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return updated


# ===========================
# Today's workout
# ===========================

@router.get("/{plan_id}/today")
def get_plan_today(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return today's scheduled workout for a specific plan."""
    plan = plan_crud.get_plan_by_id(db, plan_id, current_user.id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found.")
    if plan.status != PlanStatus.ACTIVE or plan.start_date is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan is not active. Activate the plan first.",
        )
    return plan_service.get_today_workout(plan)


# ===========================
# Start workout shortcut
# ===========================

@router.post("/{plan_id}/start-workout", response_model=WorkoutSessionResponse, status_code=status.HTTP_201_CREATED)
def start_workout_from_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a WorkoutSession pre-populated from today's template.

    Determines today's template via cycle logic, creates a session with
    ``template_id`` and ``plan_id`` set, and pre-populates exercises from
    the template (sets come in empty — user fills reps/weight during the session).

    Returns HTTP 400 when the plan is not active or today is a rest day.
    """
    plan = plan_crud.get_plan_by_id(db, plan_id, current_user.id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found.")
    if plan.status != PlanStatus.ACTIVE or plan.start_date is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan is not active.",
        )

    today_result = plan_service.get_today_workout(plan)
    if today_result.is_rest_day:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Today is a rest day in this plan.",
        )

    # Create an empty session with traceability to the template and plan.
    # The frontend uses the template_id to load exercises during the active workout.
    session_in = WorkoutSessionCreate(
        exercises=[],
        template_id=today_result.template_id,
        plan_id=plan_id,
    )

    session = workout_crud.create_workout_session(db, current_user.id, session_in)
    return session
