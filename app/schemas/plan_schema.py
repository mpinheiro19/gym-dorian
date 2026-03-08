"""Workout plan schemas for API requests and responses."""
from typing import Optional, List
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict

from app.models.enums import PlanStatus


# ===========================
# PlanDay Schemas
# ===========================

class PlanDayBase(BaseModel):
    """Base schema for PlanDay."""
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday … 6=Sunday (ISO 8601)")
    template_id: int = Field(..., gt=0)
    notes: Optional[str] = Field(None, max_length=1000)


class PlanDayCreate(PlanDayBase):
    """Schema for creating a PlanDay (used when building a plan)."""
    pass


class PlanDayResponse(PlanDayBase):
    """Schema for PlanDay in API responses."""
    id: int
    week_id: int
    # Inline template summary to avoid n+1 calls on the frontend
    template_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_template(cls, day: object) -> "PlanDayResponse":
        """Build response with template name resolved."""
        obj = cls.model_validate(day)
        if hasattr(day, "template") and day.template:
            obj.template_name = day.template.name
        return obj


# ===========================
# PlanWeek Schemas
# ===========================

class PlanWeekBase(BaseModel):
    """Base schema for PlanWeek."""
    week_number: int = Field(..., ge=1)
    name: Optional[str] = Field(None, max_length=255)


class PlanWeekCreate(PlanWeekBase):
    """Schema for creating a PlanWeek with its days."""
    days: List[PlanDayCreate] = Field(default_factory=list)


class PlanWeekResponse(PlanWeekBase):
    """Schema for PlanWeek in API responses."""
    id: int
    plan_id: int
    days: List[PlanDayResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ===========================
# WorkoutPlan Schemas
# ===========================

class WorkoutPlanBase(BaseModel):
    """Base schema for WorkoutPlan."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)


class WorkoutPlanCreate(WorkoutPlanBase):
    """Schema for creating a WorkoutPlan with nested weeks and days."""
    weeks: List[PlanWeekCreate] = Field(..., min_length=1)


class WorkoutPlanUpdate(BaseModel):
    """Schema for partially updating a WorkoutPlan."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    weeks: Optional[List[PlanWeekCreate]] = None


class WorkoutPlanResponse(WorkoutPlanBase):
    """Schema for WorkoutPlan in API responses."""
    id: int
    user_id: int
    status: PlanStatus
    start_date: Optional[date]
    created_at: datetime
    updated_at: Optional[datetime]
    weeks: List[PlanWeekResponse] = []

    model_config = ConfigDict(from_attributes=True)


class WorkoutPlanSummary(BaseModel):
    """Lightweight plan summary (without full week/day tree)."""
    id: int
    name: str
    description: Optional[str]
    status: PlanStatus
    start_date: Optional[date]
    total_weeks: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===========================
# Status Transition Schema
# ===========================

class PlanStatusUpdate(BaseModel):
    """Schema for changing a plan's status."""
    status: PlanStatus


# ===========================
# Today's Workout Schema
# ===========================

class TodayWorkoutResponse(BaseModel):
    """Response for the 'today's workout' endpoint.

    Contains enough information for the dashboard widget to render the
    day's template and allow the user to start a session.
    """
    plan_id: int
    plan_name: str
    week_number: int
    day_of_week: int
    day_name: str  # e.g. "Monday"
    template_id: int
    template_name: str
    template_description: Optional[str]
    is_rest_day: bool = False

    model_config = ConfigDict(from_attributes=True)


class RestDayResponse(BaseModel):
    """Response when today is a rest day in the active plan."""
    plan_id: int
    plan_name: str
    week_number: int
    day_of_week: int
    day_name: str
    is_rest_day: bool = True
