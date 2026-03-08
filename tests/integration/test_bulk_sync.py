"""Integration tests for ``POST /api/workouts/sessions/bulk``.

These tests exercise the HTTP layer end-to-end using an in-memory SQLite
database.  Authentication is handled by overriding the
``get_current_active_user`` dependency with a function that returns a real
``User`` row created in the test database (so FK constraints are satisfied).

All tests assert HTTP 207 Multi-Status for success paths or the appropriate
error code for failure paths (401, 422).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4, UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import get_db
from app.api.dependencies.auth import get_current_active_user
from app.models.exercise import Exercise
from app.models.log import WorkoutSession
from app.models.user import User
from app.services.sync_service import clear_idempotency_cache

BULK_URL = "/api/workouts/sessions/bulk"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def authed_client(db_session: Session):
    """TestClient with DB + auth dependency overridden.

    Creates a real User row in the test DB.
    Yields ``(client, user)`` so tests can reference the authenticated user.
    """
    clear_idempotency_cache()

    user = User(
        email="sync_tester@example.com",
        password_hash="hashed",
        full_name="Sync Tester",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    def _override_db():
        try:
            yield db_session
        finally:
            pass

    def _override_auth():
        return user

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_active_user] = _override_auth

    with TestClient(app) as client:
        yield client, user

    app.dependency_overrides.clear()
    clear_idempotency_cache()


@pytest.fixture()
def sample_exercise(db_session: Session) -> Exercise:
    ex = Exercise(name="Bench Press", equipment_type="Barbell")
    db_session.add(ex)
    db_session.commit()
    db_session.refresh(ex)
    return ex


# ---------------------------------------------------------------------------
# Payload helpers
# ---------------------------------------------------------------------------


def _set_payload(n: int = 1) -> dict:
    return {"client_uuid": str(uuid4()), "set_number": n, "reps": 10, "weight": 100.0}


def _exercise_payload(exercise_id: int, num_sets: int = 2) -> dict:
    return {
        "client_uuid": str(uuid4()),
        "exercise_id": exercise_id,
        "sets": [_set_payload(i + 1) for i in range(num_sets)],
    }


def _session_payload(
    exercise_id: int,
    *,
    client_uuid: str | None = None,
    updated_at: datetime | None = None,
    notes: str | None = None,
    exercises: list[dict] | None = None,
) -> dict:
    payload = {
        "client_uuid": client_uuid or str(uuid4()),
        "workout_date": str(date.today()),
        "updated_at": (updated_at or datetime.now(timezone.utc)).isoformat(),
        "exercises": exercises if exercises is not None else [_exercise_payload(exercise_id)],
    }
    if notes is not None:
        payload["notes"] = notes
    return payload


def _bulk_payload(*sessions: dict) -> dict:
    return {"sync_id": str(uuid4()), "sessions": list(sessions)}


# ---------------------------------------------------------------------------
# Tests: Happy Paths
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestBulkSyncCreated:
    """New sessions are created and 207 is returned."""

    def test_single_session_returns_207(self, authed_client, sample_exercise):
        client, _ = authed_client
        payload = _bulk_payload(_session_payload(sample_exercise.id))

        resp = client.post(BULK_URL, json=payload)

        assert resp.status_code == 207, resp.text

    def test_single_session_status_is_created(self, authed_client, sample_exercise):
        client, _ = authed_client
        payload = _bulk_payload(_session_payload(sample_exercise.id))

        data = client.post(BULK_URL, json=payload).json()

        assert data["summary"]["created"] == 1
        assert data["results"][0]["status"] == "created"
        assert data["results"][0]["server_id"] is not None

    def test_three_sessions_all_created(self, authed_client, sample_exercise):
        client, _ = authed_client
        payload = _bulk_payload(*[_session_payload(sample_exercise.id) for _ in range(3)])

        data = client.post(BULK_URL, json=payload).json()

        assert data["summary"]["created"] == 3
        assert all(r["status"] == "created" for r in data["results"])

    def test_empty_sessions_array_returns_207_not_422(self, authed_client, _=None):
        client, _ = authed_client
        payload = {"sync_id": str(uuid4()), "sessions": []}

        resp = client.post(BULK_URL, json=payload)

        assert resp.status_code == 207, resp.text
        data = resp.json()
        assert data["summary"]["created"] == 0
        assert len(data["results"]) == 0

    def test_response_contains_sync_id_matching_request(
        self, authed_client, sample_exercise
    ):
        client, _ = authed_client
        sync_id = str(uuid4())
        payload = {"sync_id": sync_id, "sessions": [_session_payload(sample_exercise.id)]}

        data = client.post(BULK_URL, json=payload).json()

        assert data["sync_id"] == sync_id

    def test_large_batch_50_sessions(self, authed_client, sample_exercise):
        client, _ = authed_client
        sessions = [_session_payload(sample_exercise.id) for _ in range(50)]
        payload = _bulk_payload(*sessions)

        data = client.post(BULK_URL, json=payload).json()

        assert data["summary"]["created"] == 50
        assert len(data["results"]) == 50

    def test_server_data_returned_for_created_session(
        self, authed_client, sample_exercise
    ):
        client, _ = authed_client
        payload = _bulk_payload(_session_payload(sample_exercise.id))

        data = client.post(BULK_URL, json=payload).json()
        result = data["results"][0]

        assert result["server_data"] is not None
        assert "id" in result["server_data"]
        assert "client_uuid" in result["server_data"]

    def test_session_without_exercises_is_created(self, authed_client, sample_exercise):
        """Sending a session with an empty exercises list should still create it."""
        client, _ = authed_client
        payload = _bulk_payload(
            _session_payload(sample_exercise.id, exercises=[])
        )

        data = client.post(BULK_URL, json=payload).json()

        assert data["results"][0]["status"] == "created"


# ---------------------------------------------------------------------------
# Tests: LWW — Updated
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestBulkSyncUpdated:
    """Client timestamp > server timestamp → session updated."""

    def test_newer_client_returns_updated_status(
        self, authed_client, sample_exercise, db_session: Session
    ):
        client, user = authed_client

        server_ts = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        client_uuid_str = str(uuid4())

        ws = WorkoutSession(
            user_id=user.id,
            workout_date=date(2026, 1, 1),
            notes="Old note",
            client_uuid=client_uuid_str,
            updated_at=server_ts,
        )
        db_session.add(ws)
        db_session.commit()

        item = _session_payload(
            sample_exercise.id,
            client_uuid=client_uuid_str,
            updated_at=server_ts + timedelta(hours=2),
            notes="New note",
        )
        payload = _bulk_payload(item)

        data = client.post(BULK_URL, json=payload).json()

        assert data["results"][0]["status"] == "updated"
        assert data["summary"]["updated"] == 1


# ---------------------------------------------------------------------------
# Tests: LWW — Conflict
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestBulkSyncConflict:
    """Server timestamp >= client timestamp → conflict, server wins."""

    def test_older_client_returns_conflict(
        self, authed_client, sample_exercise, db_session: Session
    ):
        client, user = authed_client

        server_ts = datetime(2026, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        client_uuid_str = str(uuid4())

        ws = WorkoutSession(
            user_id=user.id,
            workout_date=date(2026, 2, 1),
            notes="Server note",
            client_uuid=client_uuid_str,
            updated_at=server_ts,
        )
        db_session.add(ws)
        db_session.commit()

        item = _session_payload(
            sample_exercise.id,
            client_uuid=client_uuid_str,
            updated_at=server_ts - timedelta(hours=1),
        )
        payload = _bulk_payload(item)

        data = client.post(BULK_URL, json=payload).json()

        assert data["results"][0]["status"] == "conflict"
        assert data["summary"]["conflicts"] == 1

    def test_conflict_returns_server_data_for_client_merge(
        self, authed_client, sample_exercise, db_session: Session
    ):
        client, user = authed_client

        server_ts = datetime(2026, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        client_uuid_str = str(uuid4())

        ws = WorkoutSession(
            user_id=user.id,
            workout_date=date(2026, 2, 1),
            notes="Authoritative server note",
            client_uuid=client_uuid_str,
            updated_at=server_ts,
        )
        db_session.add(ws)
        db_session.commit()

        item = _session_payload(
            sample_exercise.id,
            client_uuid=client_uuid_str,
            updated_at=server_ts - timedelta(minutes=30),
        )
        payload = _bulk_payload(item)
        data = client.post(BULK_URL, json=payload).json()

        result = data["results"][0]
        assert result["server_data"] is not None
        assert result["server_data"]["notes"] == "Authoritative server note"


# ---------------------------------------------------------------------------
# Tests: Idempotency
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestBulkSyncIdempotency:
    """Replaying the same sync_id must return the cached response."""

    def test_same_sync_id_returns_same_summary(self, authed_client, sample_exercise):
        client, _ = authed_client
        payload = _bulk_payload(_session_payload(sample_exercise.id))

        first = client.post(BULK_URL, json=payload).json()
        second = client.post(BULK_URL, json=payload).json()

        assert second["sync_id"] == first["sync_id"]
        assert second["summary"] == first["summary"]
        assert len(second["results"]) == len(first["results"])

    def test_second_call_does_not_create_duplicate_db_rows(
        self, authed_client, sample_exercise, db_session: Session
    ):
        client, _ = authed_client
        payload = _bulk_payload(_session_payload(sample_exercise.id))

        client.post(BULK_URL, json=payload)
        client.post(BULK_URL, json=payload)

        count = db_session.query(WorkoutSession).count()
        assert count == 1


# ---------------------------------------------------------------------------
# Tests: Error Handling
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestBulkSyncErrors:
    """Error cases: auth, validation, partial failures."""

    def test_unauthenticated_returns_401(self, client):
        """Calling without auth override must return 401."""
        payload = _bulk_payload()  # empty is fine
        resp = client.post(BULK_URL, json=payload)
        assert resp.status_code == 401

    def test_missing_sync_id_returns_422(self, authed_client):
        # 'sync_id' is the only required field (sessions has default_factory=list)
        client, _ = authed_client
        resp = client.post(BULK_URL, json={"sessions": []})
        assert resp.status_code == 422

    def test_invalid_uuid_field_returns_422(self, authed_client):
        client, _ = authed_client
        payload = {"sync_id": "not-a-uuid", "sessions": []}
        resp = client.post(BULK_URL, json=payload)
        assert resp.status_code == 422

    def test_duplicate_session_uuid_in_batch_errors_second(
        self, authed_client, sample_exercise
    ):
        client, _ = authed_client
        shared_uuid = str(uuid4())
        item_a = _session_payload(sample_exercise.id, client_uuid=shared_uuid)
        item_b = _session_payload(sample_exercise.id, client_uuid=shared_uuid)
        payload = _bulk_payload(item_a, item_b)

        data = client.post(BULK_URL, json=payload).json()

        assert data["summary"]["created"] == 1
        assert data["summary"]["errors"] == 1
        statuses = [r["status"] for r in data["results"]]
        assert statuses.index("created") < statuses.index("error")  # first wins

    def test_error_session_does_not_block_good_sessions(
        self, authed_client, sample_exercise
    ):
        client, _ = authed_client
        good_item = _session_payload(sample_exercise.id)
        dup_uuid = str(uuid4())
        bad_item = _session_payload(
            sample_exercise.id,
            exercises=[
                _exercise_payload(sample_exercise.id) | {"client_uuid": dup_uuid},
                _exercise_payload(sample_exercise.id) | {"client_uuid": dup_uuid},
            ],
        )
        payload = _bulk_payload(good_item, bad_item)

        data = client.post(BULK_URL, json=payload).json()

        assert data["summary"]["created"] == 1
        assert data["summary"]["errors"] == 1


# ---------------------------------------------------------------------------
# Tests: Response Schema Completeness
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestBulkSyncResponseSchema:
    """Ensure the 207 response shape is stable for frontend consumers."""

    def test_response_has_all_top_level_keys(self, authed_client, sample_exercise):
        client, _ = authed_client
        payload = _bulk_payload(_session_payload(sample_exercise.id))

        data = client.post(BULK_URL, json=payload).json()

        assert "sync_id" in data
        assert "results" in data
        assert "summary" in data

    def test_summary_has_all_counters(self, authed_client, sample_exercise):
        client, _ = authed_client
        payload = _bulk_payload(_session_payload(sample_exercise.id))

        summary = client.post(BULK_URL, json=payload).json()["summary"]

        for field in ("created", "updated", "conflicts", "errors"):
            assert field in summary, f"Missing summary field: {field}"

    def test_result_item_has_required_fields(self, authed_client, sample_exercise):
        client, _ = authed_client
        payload = _bulk_payload(_session_payload(sample_exercise.id))

        result = client.post(BULK_URL, json=payload).json()["results"][0]

        for field in ("client_uuid", "status", "server_id"):
            assert field in result, f"Missing result field: {field}"
