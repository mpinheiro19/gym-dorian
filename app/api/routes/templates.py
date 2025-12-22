"""Workout template routes for managing reusable workout routines."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.dependencies.auth import get_current_active_user
from app.models.user import User
from app.crud import template as template_crud
from app.crud import workout as workout_crud
from app.schemas.workout_schema import (
    WorkoutTemplateResponse,
    WorkoutTemplateCreate,
    WorkoutTemplateUpdate,
    ExecuteTemplateRequest,
)

router = APIRouter(prefix="/templates", tags=["Workout Templates"])


@router.get("", response_model=List[WorkoutTemplateResponse])
def list_user_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of workout templates for the current user.

    Args:
        skip: Number of records to skip
        limit: Maximum records to return
        db: Database session
        current_user: Authenticated user

    Returns:
        List[WorkoutTemplateResponse]: List of templates
    """
    return template_crud.get_user_templates(db, current_user.id, skip, limit)


@router.get("/{template_id}", response_model=WorkoutTemplateResponse)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific workout template by ID.

    Args:
        template_id: Template ID
        db: Database session
        current_user: Authenticated user

    Returns:
        WorkoutTemplateResponse: Template details with exercises

    Raises:
        HTTPException 404: If template not found or not owned by user
    """
    template = template_crud.get_template_by_id(db, template_id, current_user.id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    return template


@router.post("", response_model=WorkoutTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    template_in: WorkoutTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new workout template.

    Validates that all exercises in the template exist
    before creating.

    Args:
        template_in: Template creation data
        db: Database session
        current_user: Authenticated user

    Returns:
        WorkoutTemplateResponse: Created template

    Raises:
        HTTPException 400: If any exercise_id doesn't exist
    """
    # Verify all exercises exist
    for ex_data in template_in.exercises:
        exercise = workout_crud.get_exercise_by_id(db, ex_data.exercise_id)
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Exercise with ID {ex_data.exercise_id} not found"
            )

    return template_crud.create_template(db, current_user.id, template_in)


@router.put("/{template_id}", response_model=WorkoutTemplateResponse)
def update_template(
    template_id: int,
    template_in: WorkoutTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update an existing workout template.

    Args:
        template_id: Template ID to update
        template_in: Update data
        db: Database session
        current_user: Authenticated user

    Returns:
        WorkoutTemplateResponse: Updated template

    Raises:
        HTTPException 404: If template not found or not owned by user
    """
    template = template_crud.get_template_by_id(db, template_id, current_user.id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    return template_crud.update_template(db, template, template_in)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a workout template.

    Args:
        template_id: Template ID to delete
        db: Database session
        current_user: Authenticated user

    Raises:
        HTTPException 404: If template not found or not owned by user
    """
    template = template_crud.get_template_by_id(db, template_id, current_user.id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    template_crud.delete_template(db, template)


@router.post("/{template_id}/prepare")
def prepare_workout_from_template(
    template_id: int,
    execute_req: ExecuteTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Prepare a workout based on a template.

    This endpoint returns formatted data for the frontend
    to populate with actual workout data (reps, weights, etc).
    It does NOT create a workout session.

    Args:
        template_id: Template ID to prepare from
        execute_req: Execution request with date
        db: Database session
        current_user: Authenticated user

    Returns:
        dict: Prepared workout structure ready for frontend

    Raises:
        HTTPException 404: If template not found or not owned by user
    """
    template = template_crud.get_template_by_id(db, template_id, current_user.id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    return template_crud.prepare_workout_from_template(
        db,
        template,
        execute_req.workout_date
    )
