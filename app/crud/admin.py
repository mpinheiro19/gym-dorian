"""Admin CRUD operations for user management and analytics."""
from typing import Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.models.user import User, UserSettings, UserGoal, GoalStatus
from app.models.log import WorkoutSession, LogExercise
from app.models.exercise import Exercise
from app.schemas.user_schema import UserCreate, UserUpdate


# ===========================
# Admin User Management
# ===========================

def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    is_superuser: Optional[bool] = None,
    search: Optional[str] = None
) -> list[User]:
    """
    Get list of users with filtering and pagination.

    Args:
        db: Database session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        is_active: Filter by active status
        is_superuser: Filter by superuser status
        search: Search by email or name

    Returns:
        list[User]: List of users matching criteria
    """
    query = db.query(User)

    # Apply filters
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if is_superuser is not None:
        query = query.filter(User.is_superuser == is_superuser)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (User.email.ilike(search_pattern)) |
            (User.full_name.ilike(search_pattern))
        )

    # Apply pagination and ordering
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return users


def get_user_count(
    db: Session,
    is_active: Optional[bool] = None,
    is_superuser: Optional[bool] = None
) -> int:
    """
    Get total count of users matching criteria.

    Args:
        db: Database session
        is_active: Filter by active status
        is_superuser: Filter by superuser status

    Returns:
        int: Total count of users
    """
    query = db.query(func.count(User.id))

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if is_superuser is not None:
        query = query.filter(User.is_superuser == is_superuser)

    return query.scalar()


def get_user_by_id_admin(db: Session, user_id: int) -> Optional[User]:
    """
    Get user by ID (admin access).

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Optional[User]: User object or None
    """
    return db.query(User).filter(User.id == user_id).first()


def create_user_admin(db: Session, user_in: UserCreate, is_superuser: bool = False) -> User:
    """
    Create user as admin (can set superuser flag).

    Args:
        db: Database session
        user_in: User creation data
        is_superuser: Whether to make user a superuser

    Returns:
        User: Created user object
    """
    from app.core.security import get_password_hash

    hashed_password = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        password_hash=hashed_password,
        full_name=user_in.full_name,
        is_superuser=is_superuser,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create default settings
    from app.crud.user import create_user_settings
    from app.schemas.user_schema import UserSettingsCreate
    create_user_settings(db, user.id, UserSettingsCreate())

    return user


def update_user_admin(db: Session, user: User, user_in: UserUpdate) -> User:
    """
    Update user as admin (can modify is_active, is_superuser).

    Args:
        db: Database session
        user: Existing user object
        user_in: User update data

    Returns:
        User: Updated user object
    """
    from app.core.security import get_password_hash

    update_data = user_in.model_dump(exclude_unset=True)

    # Handle password update separately (needs hashing)
    if "password" in update_data:
        hashed_password = get_password_hash(update_data["password"])
        update_data["password_hash"] = hashed_password
        del update_data["password"]

    for field, value in update_data.items():
        setattr(user, field, value)

    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user


def toggle_user_active_status(db: Session, user_id: int) -> User:
    """
    Toggle user active status.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        User: Updated user object
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_active = not user.is_active
        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
    return user


def delete_user_admin(db: Session, user_id: int) -> bool:
    """
    Delete a user (admin only).

    Args:
        db: Database session
        user_id: User ID to delete

    Returns:
        bool: True if deleted, False if not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False


# ===========================
# Admin Analytics
# ===========================

def get_user_statistics(db: Session) -> dict:
    """
    Get overall user statistics.

    Args:
        db: Database session

    Returns:
        dict: Statistics about users
    """
    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    inactive_users = total_users - active_users
    superusers = db.query(func.count(User.id)).filter(User.is_superuser == True).scalar()

    # New users in last 30 days
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    new_users_30d = db.query(func.count(User.id)).filter(
        User.created_at >= thirty_days_ago
    ).scalar()

    # Users with recent activity (logged in last 7 days)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    active_users_7d = db.query(func.count(User.id)).filter(
        User.last_login >= seven_days_ago
    ).scalar()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "superusers": superusers,
        "new_users_last_30_days": new_users_30d,
        "active_users_last_7_days": active_users_7d,
    }


def get_workout_statistics(db: Session) -> dict:
    """
    Get overall workout statistics.

    Args:
        db: Database session

    Returns:
        dict: Statistics about workouts
    """
    total_workouts = db.query(func.count(WorkoutSession.id)).scalar()
    total_exercises_logged = db.query(func.count(LogExercise.id)).scalar()

    # Workouts in last 30 days
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    workouts_30d = db.query(func.count(WorkoutSession.id)).filter(
        WorkoutSession.workout_date >= thirty_days_ago.date()
    ).scalar()

    # Most active users (top 5 by workout count)
    most_active_users = db.query(
        User.email,
        User.full_name,
        func.count(WorkoutSession.id).label("workout_count")
    ).join(WorkoutSession).group_by(User.id).order_by(
        func.count(WorkoutSession.id).desc()
    ).limit(5).all()

    # Most popular exercises (top 5)
    popular_exercises = db.query(
        Exercise.name,
        func.count(LogExercise.id).label("times_logged")
    ).join(LogExercise).group_by(Exercise.id).order_by(
        func.count(LogExercise.id).desc()
    ).limit(5).all()

    return {
        "total_workouts": total_workouts,
        "total_exercises_logged": total_exercises_logged,
        "workouts_last_30_days": workouts_30d,
        "most_active_users": [
            {
                "email": email,
                "full_name": full_name,
                "workout_count": count
            }
            for email, full_name, count in most_active_users
        ],
        "popular_exercises": [
            {
                "exercise": name,
                "times_logged": count
            }
            for name, count in popular_exercises
        ],
    }


def get_goal_statistics(db: Session) -> dict:
    """
    Get overall goal statistics.

    Args:
        db: Database session

    Returns:
        dict: Statistics about user goals
    """
    total_goals = db.query(func.count(UserGoal.id)).scalar()
    active_goals = db.query(func.count(UserGoal.id)).filter(
        UserGoal.status == GoalStatus.ACTIVE
    ).scalar()
    completed_goals = db.query(func.count(UserGoal.id)).filter(
        UserGoal.status == GoalStatus.COMPLETED
    ).scalar()
    abandoned_goals = db.query(func.count(UserGoal.id)).filter(
        UserGoal.status == GoalStatus.ABANDONED
    ).scalar()

    # Goal completion rate
    completion_rate = 0
    if total_goals > 0:
        completion_rate = (completed_goals / total_goals) * 100

    # Goals by type
    goals_by_type = db.query(
        UserGoal.goal_type,
        func.count(UserGoal.id).label("count")
    ).group_by(UserGoal.goal_type).all()

    return {
        "total_goals": total_goals,
        "active_goals": active_goals,
        "completed_goals": completed_goals,
        "abandoned_goals": abandoned_goals,
        "completion_rate": round(completion_rate, 2),
        "goals_by_type": [
            {
                "type": goal_type.value,
                "count": count
            }
            for goal_type, count in goals_by_type
        ],
    }


def get_user_activity_details(db: Session, user_id: int) -> dict:
    """
    Get detailed activity information for a specific user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        dict: Detailed user activity statistics
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    # Workout stats
    total_workouts = db.query(func.count(WorkoutSession.id)).filter(
        WorkoutSession.user_id == user_id
    ).scalar()

    total_duration = db.query(func.sum(WorkoutSession.duration_minutes)).filter(
        WorkoutSession.user_id == user_id
    ).scalar() or 0

    # Last workout
    last_workout = db.query(WorkoutSession).filter(
        WorkoutSession.user_id == user_id
    ).order_by(WorkoutSession.workout_date.desc()).first()

    # Goal stats
    active_goals_count = db.query(func.count(UserGoal.id)).filter(
        UserGoal.user_id == user_id,
        UserGoal.status == GoalStatus.ACTIVE
    ).scalar()

    completed_goals_count = db.query(func.count(UserGoal.id)).filter(
        UserGoal.user_id == user_id,
        UserGoal.status == GoalStatus.COMPLETED
    ).scalar()

    return {
        "user_id": user_id,
        "email": user.email,
        "full_name": user.full_name,
        "account_created": user.created_at,
        "last_login": user.last_login,
        "is_active": user.is_active,
        "total_workouts": total_workouts,
        "total_workout_duration_minutes": total_duration,
        "last_workout_date": last_workout.workout_date if last_workout else None,
        "active_goals": active_goals_count,
        "completed_goals": completed_goals_count,
    }
