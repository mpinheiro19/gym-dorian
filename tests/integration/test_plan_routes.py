"""Integration tests for workout plan API endpoints."""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import get_db
from app.api.dependencies.auth import get_current_active_user
from app.models.user import User
from app.models.exercise import Exercise
from app.models.template import WorkoutTemplate, TemplateExercise
from app.models.plan import WorkoutPlan, PlanWeek, PlanDay
from app.models.enums import PlanStatus


# ===========================
# Shared fixtures (module-level helpers)
# ===========================

@pytest.fixture()
def authed_client(db_session: Session):
    """TestClient with both DB and auth dependency overridden.

    Creates a real User in the test DB so Foreign Key constraints hold.
    Returns (client, user) tuple.
    """
    # Create a real user in the test DB
    user = User(
        email="planner@test.com",
        password_hash="hashed",
        full_name="Plan Tester",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user():
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = override_get_current_user

    with TestClient(app) as client:
        yield client, user

    app.dependency_overrides.clear()


@pytest.fixture()
def sample_exercise(db_session: Session) -> Exercise:
    """A persisted Exercise used as template content."""
    ex = Exercise(name="Bench Press", equipment_type="Barbell")
    db_session.add(ex)
    db_session.commit()
    db_session.refresh(ex)
    return ex


@pytest.fixture()
def sample_template(db_session: Session, sample_exercise: Exercise) -> WorkoutTemplate:
    """A persisted WorkoutTemplate owned by user_id == the authed_client user (resolved lazily)."""
    # We set user_id = 1 here — authed_client creates user first so this will be correct
    # when used together with authed_client fixture.
    tmpl = WorkoutTemplate(user_id=1, name="Upper Body A", description="Push movements")
    db_session.add(tmpl)
    db_session.flush()
    te = TemplateExercise(template_id=tmpl.id, exercise_id=sample_exercise.id, order_index=0)
    db_session.add(te)
    db_session.commit()
    db_session.refresh(tmpl)
    return tmpl


# Helper to build a minimal plan payload
def _plan_payload(template_id: int, weeks: int = 1) -> dict:
    days = [{"day_of_week": 0, "template_id": template_id}]  # Monday only
    return {
        "name": "Test Plan",
        "description": "Integration test plan",
        "weeks": [{"week_number": i + 1, "days": days} for i in range(weeks)],
    }


# ===========================
# Plan CRUD
# ===========================

@pytest.mark.integration
class TestCreatePlan:
    """POST /api/plans"""

    def test_create_plan_returns_201(self, authed_client, sample_template):
        client, user = authed_client
        # Ensure template belongs to this user
        sample_template.user_id = user.id

        response = client.post("/api/plans", json=_plan_payload(sample_template.id))
        assert response.status_code == 201, response.text

    def test_created_plan_has_correct_fields(self, authed_client, sample_template):
        client, user = authed_client
        sample_template.user_id = user.id
        payload = _plan_payload(sample_template.id)

        data = client.post("/api/plans", json=payload).json()

        assert data["name"] == "Test Plan"
        assert data["status"] == "queued"
        assert data["user_id"] == user.id
        assert len(data["weeks"]) == 1
        assert len(data["weeks"][0]["days"]) == 1

    def test_create_plan_with_multiple_weeks(self, authed_client, sample_template):
        client, user = authed_client
        sample_template.user_id = user.id

        data = client.post("/api/plans", json=_plan_payload(sample_template.id, weeks=3)).json()
        assert len(data["weeks"]) == 3

    def test_create_plan_rejects_foreign_template(self, authed_client):
        """template_id that doesn't belong to user → 400."""
        client, _ = authed_client
        response = client.post("/api/plans", json=_plan_payload(template_id=99999))
        assert response.status_code == 400


@pytest.mark.integration
class TestGetPlan:
    """GET /api/plans and GET /api/plans/{id}"""

    def test_list_plans_empty(self, authed_client):
        client, _ = authed_client
        data = client.get("/api/plans").json()
        assert data == []

    def test_get_plan_returns_404_when_not_found(self, authed_client):
        client, _ = authed_client
        assert client.get("/api/plans/999").status_code == 404

    def test_list_and_get_created_plan(self, authed_client, sample_template):
        client, user = authed_client
        sample_template.user_id = user.id

        created = client.post("/api/plans", json=_plan_payload(sample_template.id)).json()
        plan_id = created["id"]

        # List
        plans = client.get("/api/plans").json()
        assert len(plans) == 1
        assert plans[0]["id"] == plan_id

        # Detail
        detail = client.get(f"/api/plans/{plan_id}").json()
        assert detail["id"] == plan_id
        assert len(detail["weeks"]) == 1

    def test_list_filter_by_status(self, authed_client, sample_template):
        client, user = authed_client
        sample_template.user_id = user.id

        # Create plan (queued by default)
        client.post("/api/plans", json=_plan_payload(sample_template.id))

        queued = client.get("/api/plans?status=queued").json()
        active = client.get("/api/plans?status=active").json()

        assert len(queued) == 1
        assert len(active) == 0


@pytest.mark.integration
class TestUpdatePlan:
    """PUT /api/plans/{id}"""

    def test_update_plan_name(self, authed_client, sample_template):
        client, user = authed_client
        sample_template.user_id = user.id

        plan = client.post("/api/plans", json=_plan_payload(sample_template.id)).json()
        plan_id = plan["id"]

        updated = client.put(f"/api/plans/{plan_id}", json={"name": "Renamed Plan"}).json()
        assert updated["name"] == "Renamed Plan"

    def test_update_returns_404_for_missing_plan(self, authed_client):
        client, _ = authed_client
        assert client.put("/api/plans/9999", json={"name": "X"}).status_code == 404


@pytest.mark.integration
class TestDeletePlan:
    """DELETE /api/plans/{id}"""

    def test_delete_plan(self, authed_client, sample_template):
        client, user = authed_client
        sample_template.user_id = user.id

        plan = client.post("/api/plans", json=_plan_payload(sample_template.id)).json()
        plan_id = plan["id"]

        assert client.delete(f"/api/plans/{plan_id}").status_code == 204
        assert client.get(f"/api/plans/{plan_id}").status_code == 404

    def test_delete_returns_404_when_not_found(self, authed_client):
        client, _ = authed_client
        assert client.delete("/api/plans/9999").status_code == 404


# ===========================
# Status transitions
# ===========================

@pytest.mark.integration
class TestStatusTransitions:
    """PATCH /api/plans/{id}/status"""

    def _create_plan(self, client, user, sample_template):
        sample_template.user_id = user.id
        return client.post("/api/plans", json=_plan_payload(sample_template.id)).json()

    def test_activate_plan(self, authed_client, sample_template):
        client, user = authed_client
        plan = self._create_plan(client, user, sample_template)
        plan_id = plan["id"]

        response = client.patch(f"/api/plans/{plan_id}/status", json={"status": "active"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["start_date"] is not None

    def test_pause_active_plan(self, authed_client, sample_template):
        client, user = authed_client
        plan = self._create_plan(client, user, sample_template)
        plan_id = plan["id"]

        client.patch(f"/api/plans/{plan_id}/status", json={"status": "active"})
        response = client.patch(f"/api/plans/{plan_id}/status", json={"status": "paused"})
        assert response.status_code == 200
        assert response.json()["status"] == "paused"

    def test_invalid_transition_returns_400(self, authed_client, sample_template):
        """queued → completed is not allowed."""
        client, user = authed_client
        plan = self._create_plan(client, user, sample_template)
        plan_id = plan["id"]

        response = client.patch(f"/api/plans/{plan_id}/status", json={"status": "completed"})
        assert response.status_code == 400

    def test_archived_is_terminal(self, authed_client, sample_template):
        """archived → anything should return 400."""
        client, user = authed_client
        plan = self._create_plan(client, user, sample_template)
        plan_id = plan["id"]

        client.patch(f"/api/plans/{plan_id}/status", json={"status": "active"})
        client.patch(f"/api/plans/{plan_id}/status", json={"status": "archived"})

        for target in ("active", "paused", "completed"):
            response = client.patch(f"/api/plans/{plan_id}/status", json={"status": target})
            assert response.status_code == 400, f"Expected 400 for archived→{target}"


# ===========================
# Today's workout
# ===========================

@pytest.mark.integration
class TestTodayWorkout:
    """GET /api/plans/{id}/today and GET /api/plans/active/today"""

    def test_today_returns_400_when_plan_not_active(self, authed_client, sample_template):
        client, user = authed_client
        sample_template.user_id = user.id

        plan = client.post("/api/plans", json=_plan_payload(sample_template.id)).json()
        plan_id = plan["id"]

        response = client.get(f"/api/plans/{plan_id}/today")
        assert response.status_code == 400  # not active

    def test_today_returns_workout_or_rest_day_when_active(self, authed_client, sample_template):
        client, user = authed_client
        sample_template.user_id = user.id

        plan = client.post("/api/plans", json=_plan_payload(sample_template.id)).json()
        plan_id = plan["id"]

        client.patch(f"/api/plans/{plan_id}/status", json={"status": "active"})

        response = client.get(f"/api/plans/{plan_id}/today")
        assert response.status_code == 200
        data = response.json()
        assert "is_rest_day" in data
        assert "day_name" in data

    def test_active_today_returns_none_when_no_active_plan(self, authed_client):
        client, _ = authed_client
        response = client.get("/api/plans/active/today")
        assert response.status_code == 200
        assert response.json() is None
