"""Admin routes for user management and system statistics.

All endpoints require superuser authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.dependencies.auth import get_current_superuser
from app.models.user import User
from app.crud import admin as admin_crud
from app.crud.user import get_user_by_email
from app.schemas.admin_schema import (
    AdminUserResponse,
    AdminUserCreate,
    AdminUserUpdate,
    PaginatedResponse,
    UserStatistics,
    WorkoutStatistics,
    GoalStatistics,
    DashboardStatistics,
    UserActivityDetails,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(get_current_superuser)]  # All routes require superuser
)


# ===========================
# User Management Endpoints
# ===========================

@router.get("/users", response_model=PaginatedResponse[AdminUserResponse])
def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    is_active: bool = Query(None, description="Filter by active status"),
    is_superuser: bool = Query(None, description="Filter by superuser status"),
    search: str = Query(None, description="Search by email or name"),
    db: Session = Depends(get_db),
    current_superuser: User = Depends(get_current_superuser)
):
    """
    Get paginated list of all users with optional filtering.

    Requires superuser authentication.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        is_active: Filter by active status
        is_superuser: Filter by superuser status
        search: Search term for email or name
        db: Database session
        current_superuser: Current authenticated superuser

    Returns:
        PaginatedResponse[AdminUserResponse]: Paginated list of users
    """
    users = admin_crud.get_users(
        db,
        skip=skip,
        limit=limit,
        is_active=is_active,
        is_superuser=is_superuser,
        search=search
    )

    total = admin_crud.get_user_count(
        db,
        is_active=is_active,
        is_superuser=is_superuser
    )

    return PaginatedResponse.create(
        items=users,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/users/{user_id}", response_model=AdminUserResponse)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    current_superuser: User = Depends(get_current_superuser)
):
    """
    Get user details by ID.

    Requires superuser authentication.

    Args:
        user_id: User ID
        db: Database session
        current_superuser: Current authenticated superuser

    Returns:
        AdminUserResponse: User details

    Raises:
        HTTPException 404: If user not found
    """
    user = admin_crud.get_user_by_id_admin(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: AdminUserCreate,
    db: Session = Depends(get_db),
    current_superuser: User = Depends(get_current_superuser)
):
    """
    Create a new user (admin only).

    Can create users with superuser privileges.
    Requires superuser authentication.

    Args:
        user_in: User creation data
        db: Database session
        current_superuser: Current authenticated superuser

    Returns:
        AdminUserResponse: Created user

    Raises:
        HTTPException 400: If email already exists
    """
    # Check if user already exists
    existing_user = get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    from app.schemas.user_schema import UserCreate
    user_create = UserCreate(
        email=user_in.email,
        password=user_in.password,
        full_name=user_in.full_name
    )
    user = admin_crud.create_user_admin(db, user_create, is_superuser=user_in.is_superuser)

    # Set active status if different from default
    if not user_in.is_active:
        user.is_active = user_in.is_active
        db.commit()
        db.refresh(user)

    return user


@router.put("/users/{user_id}", response_model=AdminUserResponse)
def update_user(
    user_id: int,
    user_update: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_superuser: User = Depends(get_current_superuser)
):
    """
    Update user information (admin only).

    Can modify user status, superuser flag, and other fields.
    Requires superuser authentication.

    Args:
        user_id: User ID to update
        user_update: User update data
        db: Database session
        current_superuser: Current authenticated superuser

    Returns:
        AdminUserResponse: Updated user

    Raises:
        HTTPException 404: If user not found
        HTTPException 400: If trying to change email to an existing one
    """
    user = admin_crud.get_user_by_id_admin(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check email uniqueness if email is being updated
    if user_update.email and user_update.email != user.email:
        existing_user = get_user_by_email(db, user_update.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # Convert to UserUpdate schema for the update function
    from app.schemas.user_schema import UserUpdate
    user_update_data = UserUpdate(**user_update.model_dump(exclude_unset=True))

    updated_user = admin_crud.update_user_admin(db, user, user_update_data)
    return updated_user


@router.post("/users/{user_id}/toggle-active", response_model=AdminUserResponse)
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_superuser: User = Depends(get_current_superuser)
):
    """
    Toggle user active/inactive status.

    Requires superuser authentication.

    Args:
        user_id: User ID
        db: Database session
        current_superuser: Current authenticated superuser

    Returns:
        AdminUserResponse: Updated user

    Raises:
        HTTPException 404: If user not found
        HTTPException 400: If trying to deactivate self
    """
    if user_id == current_superuser.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )

    user = admin_crud.toggle_user_active_status(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_superuser: User = Depends(get_current_superuser)
):
    """
    Delete a user (admin only).

    Permanently deletes user and all related data (cascading).
    Requires superuser authentication.

    Args:
        user_id: User ID to delete
        db: Database session
        current_superuser: Current authenticated superuser

    Raises:
        HTTPException 404: If user not found
        HTTPException 400: If trying to delete self
    """
    if user_id == current_superuser.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    deleted = admin_crud.delete_user_admin(db, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return None


@router.get("/users/{user_id}/activity", response_model=UserActivityDetails)
def get_user_activity(
    user_id: int,
    db: Session = Depends(get_db),
    current_superuser: User = Depends(get_current_superuser)
):
    """
    Get detailed activity information for a specific user.

    Includes workout statistics, goal progress, and account info.
    Requires superuser authentication.

    Args:
        user_id: User ID
        db: Database session
        current_superuser: Current authenticated superuser

    Returns:
        UserActivityDetails: Detailed user activity

    Raises:
        HTTPException 404: If user not found
    """
    activity = admin_crud.get_user_activity_details(db, user_id)
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return activity


# ===========================
# Statistics Endpoints
# ===========================

@router.get("/statistics/users", response_model=UserStatistics)
def get_user_statistics(
    db: Session = Depends(get_db),
    current_superuser: User = Depends(get_current_superuser)
):
    """
    Get overall user statistics.

    Includes total users, active users, new signups, etc.
    Requires superuser authentication.

    Args:
        db: Database session
        current_superuser: Current authenticated superuser

    Returns:
        UserStatistics: User statistics
    """
    return admin_crud.get_user_statistics(db)


@router.get("/statistics/workouts", response_model=WorkoutStatistics)
def get_workout_statistics(
    db: Session = Depends(get_db),
    current_superuser: User = Depends(get_current_superuser)
):
    """
    Get overall workout statistics.

    Includes total workouts, most active users, popular exercises.
    Requires superuser authentication.

    Args:
        db: Database session
        current_superuser: Current authenticated superuser

    Returns:
        WorkoutStatistics: Workout statistics
    """
    return admin_crud.get_workout_statistics(db)


@router.get("/statistics/goals", response_model=GoalStatistics)
def get_goal_statistics(
    db: Session = Depends(get_db),
    current_superuser: User = Depends(get_current_superuser)
):
    """
    Get overall goal statistics.

    Includes total goals, completion rates, goals by type.
    Requires superuser authentication.

    Args:
        db: Database session
        current_superuser: Current authenticated superuser

    Returns:
        GoalStatistics: Goal statistics
    """
    return admin_crud.get_goal_statistics(db)


@router.get("/statistics/dashboard", response_model=DashboardStatistics)
def get_dashboard_statistics(
    db: Session = Depends(get_db),
    current_superuser: User = Depends(get_current_superuser)
):
    """
    Get combined statistics for admin dashboard.

    Returns all statistics in a single response.
    Requires superuser authentication.

    Args:
        db: Database session
        current_superuser: Current authenticated superuser

    Returns:
        DashboardStatistics: Combined statistics
    """
    return DashboardStatistics(
        users=admin_crud.get_user_statistics(db),
        workouts=admin_crud.get_workout_statistics(db),
        goals=admin_crud.get_goal_statistics(db)
    )
