"""Admin-specific Pydantic schemas for API requests and responses."""
from typing import Optional, Generic, TypeVar, List
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.user_schema import UserResponse


# ===========================
# Pagination Schemas
# ===========================

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Query parameters for pagination."""
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of records to return")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    items: List[T]
    total: int
    skip: int
    limit: int
    has_more: bool

    @classmethod
    def create(cls, items: List[T], total: int, skip: int, limit: int):
        """Create a paginated response."""
        return cls(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + len(items)) < total
        )


# ===========================
# Admin User Management Schemas
# ===========================

class UserListFilters(BaseModel):
    """Filters for user listing."""
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_superuser: Optional[bool] = Field(None, description="Filter by superuser status")
    search: Optional[str] = Field(None, description="Search by email or name")


class AdminUserResponse(UserResponse):
    """Extended user response for admin with additional fields."""
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AdminUserCreate(BaseModel):
    """Schema for admin to create a user with superuser flag."""
    email: str
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    is_superuser: bool = False
    is_active: bool = True


class AdminUserUpdate(BaseModel):
    """Schema for admin to update a user including status fields."""
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


# ===========================
# Statistics Schemas
# ===========================

class UserStatistics(BaseModel):
    """Overall user statistics."""
    total_users: int
    active_users: int
    inactive_users: int
    superusers: int
    new_users_last_30_days: int
    active_users_last_7_days: int


class ActiveUserInfo(BaseModel):
    """Information about active user."""
    email: str
    full_name: Optional[str]
    workout_count: int


class PopularExerciseInfo(BaseModel):
    """Information about popular exercise."""
    exercise: str
    times_logged: int


class WorkoutStatistics(BaseModel):
    """Overall workout statistics."""
    total_workouts: int
    total_exercises_logged: int
    workouts_last_30_days: int
    most_active_users: List[ActiveUserInfo]
    popular_exercises: List[PopularExerciseInfo]


class GoalTypeInfo(BaseModel):
    """Goal count by type."""
    type: str
    count: int


class GoalStatistics(BaseModel):
    """Overall goal statistics."""
    total_goals: int
    active_goals: int
    completed_goals: int
    abandoned_goals: int
    completion_rate: float
    goals_by_type: List[GoalTypeInfo]


class UserActivityDetails(BaseModel):
    """Detailed activity information for a user."""
    user_id: int
    email: str
    full_name: Optional[str]
    account_created: datetime
    last_login: Optional[datetime]
    is_active: bool
    total_workouts: int
    total_workout_duration_minutes: int
    last_workout_date: Optional[date]
    active_goals: int
    completed_goals: int


class DashboardStatistics(BaseModel):
    """Combined statistics for admin dashboard."""
    users: UserStatistics
    workouts: WorkoutStatistics
    goals: GoalStatistics
