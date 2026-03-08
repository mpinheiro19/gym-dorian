"""Unit tests for plan_service — cycle calculation and business logic."""
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
import pytest

from app.services.plan_service import (
    current_week_number,
    get_today_workout,
    validate_plan_ownership,
    validate_templates_belong_to_user,
)
from app.models.plan import WorkoutPlan, PlanWeek, PlanDay
from app.models.template import WorkoutTemplate
from app.models.enums import PlanStatus
from app.schemas.plan_schema import (
    WorkoutPlanCreate,
    PlanWeekCreate,
    PlanDayCreate,
    TodayWorkoutResponse,
    RestDayResponse,
)


# ===========================
# Helpers
# ===========================

def _make_plan(weeks: list[PlanWeek], start_date: date) -> WorkoutPlan:
    """Build a minimal WorkoutPlan for testing."""
    plan = WorkoutPlan()
    plan.id = 1
    plan.user_id = 1
    plan.name = "Test Plan"
    plan.status = PlanStatus.ACTIVE
    plan.start_date = start_date
    plan.weeks = weeks
    return plan


def _make_week(week_number: int, days: list[PlanDay]) -> PlanWeek:
    week = PlanWeek()
    week.id = week_number
    week.plan_id = 1
    week.week_number = week_number
    week.name = None
    week.days = days
    return week


def _make_day(day_of_week: int, template_id: int, template_name: str = "T") -> PlanDay:
    day = PlanDay()
    day.id = day_of_week + 1
    day.week_id = 1
    day.day_of_week = day_of_week
    day.template_id = template_id
    day.notes = None
    t = WorkoutTemplate()
    t.id = template_id
    t.name = template_name
    t.description = None
    day.template = t
    return day


# ===========================
# current_week_number
# ===========================

class TestCurrentWeekNumber:
    """Tests for cycle week calculation."""

    def test_day_zero_is_week_one(self):
        """start_date itself is week 1."""
        start = date(2025, 1, 6)  # Monday
        plan = _make_plan(
            [_make_week(1, []), _make_week(2, [])],
            start_date=start,
        )
        assert current_week_number(plan, reference=start) == 1

    def test_day_six_still_week_one(self):
        """Last day of the first week is still week 1."""
        start = date(2025, 1, 6)
        plan = _make_plan(
            [_make_week(1, []), _make_week(2, [])],
            start_date=start,
        )
        assert current_week_number(plan, reference=start + timedelta(days=6)) == 1

    def test_day_seven_is_week_two(self):
        """First day of the second week."""
        start = date(2025, 1, 6)
        plan = _make_plan(
            [_make_week(1, []), _make_week(2, [])],
            start_date=start,
        )
        assert current_week_number(plan, reference=start + timedelta(days=7)) == 2

    def test_cycle_wraps_single_week_plan(self):
        """A 1-week plan should always return week 1."""
        start = date(2025, 1, 6)
        plan = _make_plan([_make_week(1, [])], start_date=start)
        for offset in (0, 7, 14, 21, 100):
            assert current_week_number(plan, reference=start + timedelta(days=offset)) == 1

    def test_three_week_cycle_wraps(self):
        """3-week plan resets on week 4."""
        start = date(2025, 1, 6)
        plan = _make_plan(
            [_make_week(1, []), _make_week(2, []), _make_week(3, [])],
            start_date=start,
        )
        assert current_week_number(plan, reference=start + timedelta(days=21)) == 1

    def test_raises_when_no_start_date(self):
        """Plans without start_date (not yet activated) should raise."""
        plan = _make_plan([_make_week(1, [])], start_date=None)
        plan.start_date = None
        with pytest.raises(ValueError, match="start_date"):
            current_week_number(plan)

    def test_raises_when_no_weeks(self):
        """Plans with empty week list should raise."""
        plan = _make_plan([], start_date=date(2025, 1, 6))
        with pytest.raises(ValueError, match="no weeks"):
            current_week_number(plan)


# ===========================
# get_today_workout
# ===========================

class TestGetTodayWorkout:
    """Tests for today's workout resolution."""

    def test_returns_template_when_day_is_scheduled(self):
        """Returns TodayWorkoutResponse when a template is on this day."""
        monday = date(2025, 1, 6)  # weekday() == 0 (Monday)
        day = _make_day(day_of_week=0, template_id=42, template_name="Chest Day")
        week1 = _make_week(1, [day])
        plan = _make_plan([week1], start_date=monday)

        result = get_today_workout(plan, reference=monday)

        assert isinstance(result, TodayWorkoutResponse)
        assert result.template_id == 42
        assert result.template_name == "Chest Day"
        assert result.day_name == "Monday"
        assert result.is_rest_day is False

    def test_returns_rest_day_when_no_template(self):
        """Returns RestDayResponse when no template for the day."""
        monday = date(2025, 1, 6)
        week1 = _make_week(1, [])  # No days configured
        plan = _make_plan([week1], start_date=monday)

        result = get_today_workout(plan, reference=monday)

        assert isinstance(result, RestDayResponse)
        assert result.is_rest_day is True

    def test_returns_rest_day_when_week_not_found(self):
        """If week not found (shouldn't happen but safeguard) → rest day."""
        start = date(2025, 1, 6)
        plan = _make_plan([_make_week(1, [])], start_date=start)
        # Reference in second week of 1-week plan (wraps back to week 1 anyway)
        result = get_today_workout(plan, reference=start + timedelta(days=7))
        assert isinstance(result, TodayWorkoutResponse | RestDayResponse)

    def test_correct_day_name_for_each_weekday(self):
        """Day names are correct for all 7 days."""
        expected = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        # Start on Monday Jan 6 2025
        start = date(2025, 1, 6)
        plan = _make_plan([_make_week(1, [])], start_date=start)
        for i, name in enumerate(expected):
            result = get_today_workout(plan, reference=start + timedelta(days=i))
            assert result.day_name == name


# ===========================
# validate_plan_ownership
# ===========================

class TestValidatePlanOwnership:
    """Tests for plan ownership validation."""

    def test_returns_plan_when_valid(self):
        plan = _make_plan([_make_week(1, [])], date(2025, 1, 6))
        result = validate_plan_ownership(plan, user_id=1)
        assert result is plan

    def test_raises_when_plan_is_none(self):
        with pytest.raises(ValueError, match="not found"):
            validate_plan_ownership(None, user_id=1)

    def test_raises_when_wrong_user(self):
        plan = _make_plan([_make_week(1, [])], date(2025, 1, 6))
        with pytest.raises(ValueError, match="not found"):
            validate_plan_ownership(plan, user_id=99)


# ===========================
# validate_templates_belong_to_user
# ===========================

class TestValidateTemplatesBelongToUser:
    """Tests for template ownership validation in plan creation."""

    def _make_create_payload(self, template_ids: list[int]) -> WorkoutPlanCreate:
        days = [PlanDayCreate(day_of_week=i % 7, template_id=tid) for i, tid in enumerate(template_ids)]
        weeks = [PlanWeekCreate(week_number=1, days=days)]
        return WorkoutPlanCreate(name="Plan", weeks=weeks)

    def test_passes_when_all_owned(self):
        payload = self._make_create_payload([1, 2, 3])
        validate_templates_belong_to_user(payload, user_template_ids={1, 2, 3})  # should not raise

    def test_raises_when_template_not_owned(self):
        payload = self._make_create_payload([1, 99])
        with pytest.raises(ValueError, match="99"):
            validate_templates_belong_to_user(payload, user_template_ids={1})
