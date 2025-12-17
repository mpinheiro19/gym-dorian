"""User profile, settings, and goals routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.dependencies.auth import get_current_active_user
from app.models.user import User
from app.crud.user import (
    update_user,
    get_user_settings,
    update_user_settings,
    create_user_settings,
    get_user_goals,
    get_user_goal_by_id,
    create_user_goal,
    update_user_goal,
    delete_user_goal,
)
from app.schemas.user_schema import (
    UserResponse,
    UserUpdate,
    UserComplete,
    UserSettingsResponse,
    UserSettingsCreate,
    UserSettingsUpdate,
    UserGoalResponse,
    UserGoalCreate,
    UserGoalUpdate,
)

router = APIRouter(prefix="/users", tags=["Users"])


# ===========================
# User Profile Endpoints
# ===========================

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user profile.

    Returns the authenticated user's profile information.

    Args:
        current_user: Current authenticated user

    Returns:
        UserResponse: User profile data
    """
    return current_user


@router.get("/me/complete", response_model=UserComplete)
def get_current_user_complete(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get complete user profile with settings and goals.

    Returns user data including related settings and goals.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        UserComplete: Complete user data with settings and goals
    """
    # The relationships will be automatically loaded
    return current_user


@router.put("/me", response_model=UserResponse)
def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile.

    Update user information such as email, full name, or password.

    Args:
        user_update: User update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        UserResponse: Updated user profile

    Raises:
        HTTPException 400: If trying to change email to an already registered one
    """
    # TODO: Add check for duplicate email if email is being updated
    updated_user = update_user(db, current_user, user_update)
    return updated_user


# ===========================
# User Settings Endpoints
# ===========================

@router.get("/me/settings", response_model=UserSettingsResponse)
def get_current_user_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user settings.

    Returns user preferences and settings.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        UserSettingsResponse: User settings data

    Raises:
        HTTPException 404: If settings not found
    """
    settings = get_user_settings(db, current_user.id)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User settings not found"
        )
    return settings


@router.put("/me/settings", response_model=UserSettingsResponse)
def update_current_user_settings(
    settings_update: UserSettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user settings.

    Update user preferences such as weight units, rest time, privacy settings.

    Args:
        settings_update: Settings update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        UserSettingsResponse: Updated settings

    Raises:
        HTTPException 404: If settings not found
    """
    settings = get_user_settings(db, current_user.id)
    if not settings:
        # Create settings if they don't exist
        settings = create_user_settings(db, current_user.id, UserSettingsCreate())

    updated_settings = update_user_settings(db, settings, settings_update)
    return updated_settings


# ===========================
# User Goals Endpoints
# ===========================

@router.get("/me/goals", response_model=list[UserGoalResponse])
def get_current_user_goals(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all goals for current user.

    Returns all fitness goals for the authenticated user.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        list[UserGoalResponse]: List of user goals
    """
    goals = get_user_goals(db, current_user.id)
    return goals


@router.post("/me/goals", response_model=UserGoalResponse, status_code=status.HTTP_201_CREATED)
def create_current_user_goal(
    goal_create: UserGoalCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new goal for current user.

    Create a new fitness goal (strength, weight loss, etc.).

    Args:
        goal_create: Goal creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        UserGoalResponse: Created goal data
    """
    goal = create_user_goal(db, current_user.id, goal_create)
    return goal


@router.get("/me/goals/{goal_id}", response_model=UserGoalResponse)
def get_current_user_goal(
    goal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific goal by ID.

    Returns a single goal for the authenticated user.

    Args:
        goal_id: Goal ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        UserGoalResponse: Goal data

    Raises:
        HTTPException 404: If goal not found
    """
    goal = get_user_goal_by_id(db, goal_id, current_user.id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    return goal


@router.put("/me/goals/{goal_id}", response_model=UserGoalResponse)
def update_current_user_goal(
    goal_id: int,
    goal_update: UserGoalUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a goal.

    Update goal information such as progress, status, target values.

    Args:
        goal_id: Goal ID
        goal_update: Goal update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        UserGoalResponse: Updated goal data

    Raises:
        HTTPException 404: If goal not found
    """
    goal = get_user_goal_by_id(db, goal_id, current_user.id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )

    updated_goal = update_user_goal(db, goal, goal_update)
    return updated_goal


@router.delete("/me/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_current_user_goal(
    goal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a goal.

    Permanently delete a fitness goal.

    Args:
        goal_id: Goal ID
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException 404: If goal not found
    """
    goal = get_user_goal_by_id(db, goal_id, current_user.id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )

    delete_user_goal(db, goal)
    return None
