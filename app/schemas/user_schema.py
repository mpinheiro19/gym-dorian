"""User-related Pydantic schemas for API requests and responses."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.user import WeightUnit, DistanceUnit, GoalType, GoalStatus


# ===========================
# User Schemas
# ===========================

class UserBase(BaseModel):
    """Base schema for User with common attributes."""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user (registration)."""
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """Schema for User as stored in database (with password hash)."""
    id: int
    password_hash: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserBase):
    """Schema for User in API responses (without sensitive data)."""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """Schema for user login request."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for JWT token payload data."""
    email: Optional[str] = None
    user_id: Optional[int] = None


# ===========================
# UserSettings Schemas
# ===========================

class UserSettingsBase(BaseModel):
    """Base schema for UserSettings."""
    weight_unit: WeightUnit = WeightUnit.KILOGRAMS
    distance_unit: DistanceUnit = DistanceUnit.KILOMETERS
    default_rest_time: int = Field(90, ge=0, le=600, description="Rest time in seconds")
    private_profile: bool = False
    email_notifications: bool = True


class UserSettingsCreate(UserSettingsBase):
    """Schema for creating user settings."""
    pass


class UserSettingsUpdate(BaseModel):
    """Schema for updating user settings."""
    weight_unit: Optional[WeightUnit] = None
    distance_unit: Optional[DistanceUnit] = None
    default_rest_time: Optional[int] = Field(None, ge=0, le=600)
    private_profile: Optional[bool] = None
    email_notifications: Optional[bool] = None


class UserSettingsResponse(UserSettingsBase):
    """Schema for UserSettings in API responses."""
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===========================
# UserGoal Schemas
# ===========================

class UserGoalBase(BaseModel):
    """Base schema for UserGoal."""
    goal_type: GoalType
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    target_date: Optional[datetime] = None


class UserGoalCreate(UserGoalBase):
    """Schema for creating a user goal."""
    pass


class UserGoalUpdate(BaseModel):
    """Schema for updating a user goal."""
    goal_type: Optional[GoalType] = None
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    target_date: Optional[datetime] = None
    status: Optional[GoalStatus] = None


class UserGoalResponse(UserGoalBase):
    """Schema for UserGoal in API responses."""
    id: int
    user_id: int
    status: GoalStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ===========================
# Composite Schemas
# ===========================

class UserWithSettings(UserResponse):
    """User response with settings included."""
    settings: Optional[UserSettingsResponse] = None


class UserWithGoals(UserResponse):
    """User response with goals included."""
    goals: list[UserGoalResponse] = []


class UserComplete(UserResponse):
    """Complete user response with all related data."""
    settings: Optional[UserSettingsResponse] = None
    goals: list[UserGoalResponse] = []
