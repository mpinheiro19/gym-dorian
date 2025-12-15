"""CRUD operations for User model."""
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.user import User, UserSettings, UserGoal
from app.schemas.user_schema import (
    UserCreate,
    UserUpdate,
    UserSettingsCreate,
    UserSettingsUpdate,
    UserGoalCreate,
    UserGoalUpdate,
)
from app.core.security import get_password_hash, verify_password


# ===========================
# User CRUD
# ===========================

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    """
    Create a new user with hashed password.

    Args:
        db: Database session
        user_in: User creation schema with plain password

    Returns:
        User: Created user object
    """
    hashed_password = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        password_hash=hashed_password,
        full_name=user_in.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create default settings for the user
    create_user_settings(db, user.id, UserSettingsCreate())

    return user


def update_user(db: Session, user: User, user_in: UserUpdate) -> User:
    """
    Update user information.

    Args:
        db: Database session
        user: Existing user object
        user_in: User update schema

    Returns:
        User: Updated user object
    """
    update_data = user_in.model_dump(exclude_unset=True)

    # Handle password update separately (needs hashing)
    if "password" in update_data:
        hashed_password = get_password_hash(update_data["password"])
        update_data["password_hash"] = hashed_password
        del update_data["password"]

    for field, value in update_data.items():
        setattr(user, field, value)

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate user by email and password.

    Args:
        db: Database session
        email: User email
        password: Plain text password

    Returns:
        Optional[User]: User object if authentication successful, None otherwise
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None

    # Update last login timestamp
    user.last_login = datetime.utcnow()
    db.commit()

    return user


def delete_user(db: Session, user: User) -> None:
    """
    Delete a user (cascades to settings, goals, workouts).

    Args:
        db: Database session
        user: User object to delete
    """
    db.delete(user)
    db.commit()


# ===========================
# UserSettings CRUD
# ===========================

def get_user_settings(db: Session, user_id: int) -> Optional[UserSettings]:
    """Get user settings by user ID."""
    return db.query(UserSettings).filter(UserSettings.user_id == user_id).first()


def create_user_settings(
    db: Session,
    user_id: int,
    settings_in: UserSettingsCreate
) -> UserSettings:
    """
    Create user settings.

    Args:
        db: Database session
        user_id: User ID
        settings_in: Settings creation schema

    Returns:
        UserSettings: Created settings object
    """
    settings = UserSettings(
        user_id=user_id,
        **settings_in.model_dump()
    )
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def update_user_settings(
    db: Session,
    settings: UserSettings,
    settings_in: UserSettingsUpdate
) -> UserSettings:
    """
    Update user settings.

    Args:
        db: Database session
        settings: Existing settings object
        settings_in: Settings update schema

    Returns:
        UserSettings: Updated settings object
    """
    update_data = settings_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(settings, field, value)

    settings.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(settings)
    return settings


# ===========================
# UserGoal CRUD
# ===========================

def get_user_goals(db: Session, user_id: int) -> list[UserGoal]:
    """Get all goals for a user."""
    return db.query(UserGoal).filter(UserGoal.user_id == user_id).all()


def get_user_goal_by_id(db: Session, goal_id: int, user_id: int) -> Optional[UserGoal]:
    """Get a specific goal by ID for a user."""
    return db.query(UserGoal).filter(
        UserGoal.id == goal_id,
        UserGoal.user_id == user_id
    ).first()


def create_user_goal(
    db: Session,
    user_id: int,
    goal_in: UserGoalCreate
) -> UserGoal:
    """
    Create a new user goal.

    Args:
        db: Database session
        user_id: User ID
        goal_in: Goal creation schema

    Returns:
        UserGoal: Created goal object
    """
    goal = UserGoal(
        user_id=user_id,
        **goal_in.model_dump()
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def update_user_goal(
    db: Session,
    goal: UserGoal,
    goal_in: UserGoalUpdate
) -> UserGoal:
    """
    Update a user goal.

    Args:
        db: Database session
        goal: Existing goal object
        goal_in: Goal update schema

    Returns:
        UserGoal: Updated goal object
    """
    update_data = goal_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(goal, field, value)

    # If status is being set to completed, record completion time
    if update_data.get("status") == "completed" and goal.completed_at is None:
        goal.completed_at = datetime.utcnow()

    goal.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(goal)
    return goal


def delete_user_goal(db: Session, goal: UserGoal) -> None:
    """
    Delete a user goal.

    Args:
        db: Database session
        goal: Goal object to delete
    """
    db.delete(goal)
    db.commit()
