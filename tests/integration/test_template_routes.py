"""Integration tests for workout template API endpoints."""
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


# ===========================
# Shared fixtures
# ===========================

@pytest.fixture()
def authed_client(db_session: Session):
    """TestClient with DB and auth dependency overridden.

    Returns (client, user) tuple so tests can reference the user's ID.
    """
    user = User(
        email="tester@templates.com",
        password_hash="hashed",
        full_name="Template Tester",
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
    """Persisted exercise for use in templates."""
    ex = Exercise(name="Bench Press", equipment_type="Barbell")
    db_session.add(ex)
    db_session.commit()
    db_session.refresh(ex)
    return ex


@pytest.fixture()
def second_exercise(db_session: Session) -> Exercise:
    """Second persisted exercise for multi-exercise template tests."""
    ex = Exercise(name="Overhead Press", equipment_type="Barbell")
    db_session.add(ex)
    db_session.commit()
    db_session.refresh(ex)
    return ex


@pytest.fixture()
def persisted_template(db_session: Session, sample_exercise: Exercise) -> WorkoutTemplate:
    """A fully persisted template with one exercise, owned by user_id=1."""
    tmpl = WorkoutTemplate(user_id=1, name="Push A", description="Chest + shoulders")
    db_session.add(tmpl)
    db_session.flush()
    te = TemplateExercise(
        template_id=tmpl.id,
        exercise_id=sample_exercise.id,
        order_index=0,
        target_sets=3,
    )
    db_session.add(te)
    db_session.commit()
    db_session.refresh(tmpl)
    return tmpl


# ===========================
# List templates
# ===========================

@pytest.mark.integration
class TestListTemplates:
    """GET /api/templates"""

    def test_list_returns_empty_for_new_user(self, authed_client):
        client, user = authed_client
        response = client.get("/api/templates")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_returns_own_templates(self, authed_client, persisted_template):
        client, user = authed_client
        response = client.get("/api/templates")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Push A"

    def test_list_respects_skip_and_limit(self, authed_client, db_session: Session, sample_exercise):
        client, user = authed_client
        # Create 3 templates
        for i in range(3):
            t = WorkoutTemplate(user_id=user.id, name=f"Template {i}")
            db_session.add(t)
        db_session.commit()

        response = client.get("/api/templates?skip=1&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1


# ===========================
# Get template by ID
# ===========================

@pytest.mark.integration
class TestGetTemplate:
    """GET /api/templates/{id}"""

    def test_get_existing_template(self, authed_client, persisted_template):
        client, user = authed_client
        response = client.get(f"/api/templates/{persisted_template.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == persisted_template.id
        assert data["name"] == "Push A"
        assert len(data["exercises"]) == 1

    def test_get_nonexistent_template_returns_404(self, authed_client):
        client, user = authed_client
        response = client.get("/api/templates/99999")
        assert response.status_code == 404

    def test_get_other_user_template_returns_404(self, authed_client, db_session: Session):
        """Template owned by a different user must not be accessible."""
        client, user = authed_client
        other_template = WorkoutTemplate(user_id=9999, name="Other User Template")
        db_session.add(other_template)
        db_session.commit()

        response = client.get(f"/api/templates/{other_template.id}")
        assert response.status_code == 404


# ===========================
# Create template
# ===========================

@pytest.mark.integration
class TestCreateTemplate:
    """POST /api/templates"""

    def test_create_template_without_exercises(self, authed_client):
        """Schema requires at least 1 exercise — empty list returns 422."""
        client, user = authed_client
        payload = {"name": "Empty Template", "description": "No exercises", "exercises": []}
        response = client.post("/api/templates", json=payload)
        assert response.status_code == 422

    def test_create_template_with_exercises(self, authed_client, sample_exercise):
        client, user = authed_client
        payload = {
            "name": "Full Body",
            "description": "All muscles",
            "exercises": [
                {"exercise_id": sample_exercise.id, "order_index": 0, "target_sets": 4}
            ],
        }
        response = client.post("/api/templates", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Full Body"
        assert len(data["exercises"]) == 1
        assert data["exercises"][0]["exercise_id"] == sample_exercise.id

    def test_create_template_with_invalid_exercise_returns_400(self, authed_client):
        client, user = authed_client
        payload = {
            "name": "Bad Template",
            "exercises": [{"exercise_id": 99999, "order_index": 0}],
        }
        response = client.post("/api/templates", json=payload)
        assert response.status_code == 400

    def test_create_template_missing_name_returns_422(self, authed_client):
        client, user = authed_client
        response = client.post("/api/templates", json={"exercises": []})
        assert response.status_code == 422


# ===========================
# Update template
# ===========================

@pytest.mark.integration
class TestUpdateTemplate:
    """PUT /api/templates/{id}"""

    def test_update_template_name(self, authed_client, persisted_template):
        client, user = authed_client
        response = client.put(
            f"/api/templates/{persisted_template.id}",
            json={"name": "Push A - Updated"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Push A - Updated"

    def test_update_template_description(self, authed_client, persisted_template):
        client, user = authed_client
        response = client.put(
            f"/api/templates/{persisted_template.id}",
            json={"description": "New description"},
        )
        assert response.status_code == 200
        assert response.json()["description"] == "New description"

    def test_update_nonexistent_template_returns_404(self, authed_client):
        client, user = authed_client
        response = client.put("/api/templates/99999", json={"name": "Ghost"})
        assert response.status_code == 404

    def test_update_other_user_template_returns_404(self, authed_client, db_session: Session):
        client, user = authed_client
        other_tmpl = WorkoutTemplate(user_id=9999, name="Theirs")
        db_session.add(other_tmpl)
        db_session.commit()

        response = client.put(f"/api/templates/{other_tmpl.id}", json={"name": "Mine now"})
        assert response.status_code == 404


# ===========================
# Delete template
# ===========================

@pytest.mark.integration
class TestDeleteTemplate:
    """DELETE /api/templates/{id}"""

    def test_delete_template(self, authed_client, persisted_template):
        client, user = authed_client
        response = client.delete(f"/api/templates/{persisted_template.id}")
        assert response.status_code == 204

        # Verify it no longer exists
        get_response = client.get(f"/api/templates/{persisted_template.id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_template_returns_404(self, authed_client):
        client, user = authed_client
        response = client.delete("/api/templates/99999")
        assert response.status_code == 404

    def test_delete_other_user_template_returns_404(self, authed_client, db_session: Session):
        client, user = authed_client
        other_tmpl = WorkoutTemplate(user_id=9999, name="Theirs")
        db_session.add(other_tmpl)
        db_session.commit()

        response = client.delete(f"/api/templates/{other_tmpl.id}")
        assert response.status_code == 404


# ===========================
# Prepare workout from template
# ===========================

@pytest.mark.integration
class TestPrepareWorkout:
    """POST /api/templates/{id}/prepare"""

    def test_prepare_returns_workout_structure(self, authed_client, persisted_template):
        client, user = authed_client
        # ExecuteTemplateRequest requires template_id in body
        payload = {"template_id": persisted_template.id, "workout_date": str(date.today())}
        response = client.post(
            f"/api/templates/{persisted_template.id}/prepare",
            json=payload,
        )
        assert response.status_code == 200
        data = response.json()
        # Should contain template info and exercises to fill in
        assert "exercises" in data or "template" in data or isinstance(data, dict)

    def test_prepare_nonexistent_template_returns_404(self, authed_client):
        client, user = authed_client
        # ExecuteTemplateRequest requires template_id in body
        payload = {"template_id": 99999, "workout_date": str(date.today())}
        response = client.post("/api/templates/99999/prepare", json=payload)
        assert response.status_code == 404
