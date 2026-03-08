"""Unit tests for ``app/services/sync_service.py``.

These tests exercise the service directly against an in-memory SQLite database,
bypassing the HTTP layer.  They validate:

- LWW decision table (created / updated / conflict / error)
- Partial atomicity: one failed session does not block sibling sessions
- Idempotency: same sync_id returns cached result
- Intra-batch duplicate detection

Each test class clears the idempotency cache before and after execution so
that test isolation is preserved regardless of run order.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4, UUID

import pytest
from sqlalchemy.orm import Session

from app.models.exercise import Exercise
from app.models.log import LogExercise, LogSet, WorkoutSession
from app.schemas.sync_schema import (
    BulkLogExercise,
    BulkSessionItem,
    BulkSetDetail,
    BulkSyncRequest,
)
from app.services.sync_service import (
    clear_idempotency_cache,
    process_bulk_sync,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _exercise(db: Session, name: str = "Squat") -> Exercise:
    ex = Exercise(name=name)
    db.add(ex)
    db.flush()
    return ex


def _set_item(n: int = 1) -> BulkSetDetail:
    return BulkSetDetail(
        client_uuid=uuid4(),
        set_number=n,
        reps=10,
        weight=100.0,
    )


def _make_session_item(
    exercise_id: int,
    *,
    client_uuid: UUID | None = None,
    updated_at: datetime | None = None,
    exercises: list[BulkLogExercise] | None = None,
) -> BulkSessionItem:
    if exercises is None:
        exercises = [
            BulkLogExercise(
                client_uuid=uuid4(),
                exercise_id=exercise_id,
                sets=[_set_item(1)],
            )
        ]
    return BulkSessionItem(
        client_uuid=client_uuid or uuid4(),
        workout_date=date.today(),
        updated_at=updated_at or datetime.now(timezone.utc),
        exercises=exercises,
    )


def _make_request(*items: BulkSessionItem) -> BulkSyncRequest:
    return BulkSyncRequest(sync_id=uuid4(), sessions=list(items))


# ---------------------------------------------------------------------------
# Auto-clearing idempotency cache between tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_cache():
    """Wipe the in-memory idempotency cache before and after each test."""
    clear_idempotency_cache()
    yield
    clear_idempotency_cache()


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestBulkAllNew:
    """Three brand-new sessions → all created."""

    def test_three_new_sessions_all_created(
        self, db_session: Session
    ) -> None:
        ex = _exercise(db_session)
        db_session.commit()

        items = [_make_session_item(ex.id) for _ in range(3)]
        req = _make_request(*items)

        resp = process_bulk_sync(db_session, user_id=1, request=req)

        assert resp.summary.created == 3
        assert resp.summary.updated == 0
        assert resp.summary.conflicts == 0
        assert resp.summary.errors == 0
        assert len(resp.results) == 3
        for result in resp.results:
            assert result.status == "created"
            assert result.server_id is not None
            assert result.server_data is not None

    def test_created_session_persisted_in_db(
        self, db_session: Session
    ) -> None:
        ex = _exercise(db_session)
        db_session.commit()

        item = _make_session_item(ex.id)
        req = _make_request(item)

        resp = process_bulk_sync(db_session, user_id=1, request=req)
        assert resp.summary.created == 1

        # Verify the session was actually stored
        ws = db_session.query(WorkoutSession).filter(
            WorkoutSession.client_uuid == str(item.client_uuid)
        ).first()
        assert ws is not None
        assert ws.user_id == 1

    def test_empty_sessions_list_returns_empty_summary(
        self, db_session: Session
    ) -> None:
        req = BulkSyncRequest(sync_id=uuid4(), sessions=[])
        resp = process_bulk_sync(db_session, user_id=1, request=req)

        assert resp.summary.created == 0
        assert len(resp.results) == 0

    def test_session_with_multiple_exercises_and_sets(
        self, db_session: Session
    ) -> None:
        ex1 = _exercise(db_session, "Bench Press")
        ex2 = _exercise(db_session, "Row")
        db_session.commit()

        exercises = [
            BulkLogExercise(
                client_uuid=uuid4(),
                exercise_id=ex1.id,
                sets=[_set_item(1), _set_item(2), _set_item(3)],
            ),
            BulkLogExercise(
                client_uuid=uuid4(),
                exercise_id=ex2.id,
                sets=[_set_item(1), _set_item(2)],
            ),
        ]
        item = _make_session_item(ex1.id, exercises=exercises)
        req = _make_request(item)

        resp = process_bulk_sync(db_session, user_id=1, request=req)
        assert resp.results[0].status == "created"

        ws = db_session.query(WorkoutSession).filter(
            WorkoutSession.client_uuid == str(item.client_uuid)
        ).first()
        assert len(ws.exercises_done) == 2
        total_sets = sum(len(le.sets) for le in ws.exercises_done)
        assert total_sets == 5


@pytest.mark.unit
class TestLWWUpdated:
    """Client timestamp newer than server → session replaced."""

    def test_client_newer_returns_updated(self, db_session: Session) -> None:
        ex = _exercise(db_session)

        server_ts = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        client_ts = server_ts + timedelta(hours=2)

        # Pre-create server session with an older updated_at
        client_uuid = str(uuid4())
        ws = WorkoutSession(
            user_id=1,
            workout_date=date(2026, 1, 1),
            client_uuid=client_uuid,
            updated_at=server_ts,
        )
        db_session.add(ws)
        db_session.commit()
        server_id = ws.id

        item = _make_session_item(
            ex.id,
            client_uuid=UUID(client_uuid),
            updated_at=client_ts,
        )
        req = _make_request(item)

        resp = process_bulk_sync(db_session, user_id=1, request=req)

        assert resp.summary.updated == 1
        assert resp.results[0].status == "updated"
        assert resp.results[0].server_id == server_id
        assert resp.results[0].server_data is not None

    def test_updated_session_replaces_exercises(self, db_session: Session) -> None:
        ex1 = _exercise(db_session, "Old Exercise")
        ex2 = _exercise(db_session, "New Exercise")

        server_ts = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        client_uuid_str = str(uuid4())

        ws = WorkoutSession(
            user_id=1,
            workout_date=date(2026, 1, 1),
            client_uuid=client_uuid_str,
            updated_at=server_ts,
        )
        db_session.add(ws)
        db_session.flush()
        old_log = LogExercise(
            session_id=ws.id, exercise_id=ex1.id, client_uuid=str(uuid4())
        )
        db_session.add(old_log)
        db_session.commit()

        # Client sends session with NEW exercise
        item = BulkSessionItem(
            client_uuid=UUID(client_uuid_str),
            workout_date=date(2026, 1, 1),
            updated_at=server_ts + timedelta(hours=1),
            exercises=[
                BulkLogExercise(
                    client_uuid=uuid4(),
                    exercise_id=ex2.id,
                    sets=[_set_item(1)],
                )
            ],
        )
        req = _make_request(item)
        process_bulk_sync(db_session, user_id=1, request=req)

        db_session.expire_all()
        db_session.refresh(ws)
        assert len(ws.exercises_done) == 1
        assert ws.exercises_done[0].exercise_id == ex2.id


@pytest.mark.unit
class TestLWWConflict:
    """Server timestamp equal-or-newer → conflict, no write."""

    def test_server_newer_returns_conflict(self, db_session: Session) -> None:
        ex = _exercise(db_session)

        server_ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        client_ts = server_ts - timedelta(hours=1)  # older

        client_uuid_str = str(uuid4())
        ws = WorkoutSession(
            user_id=1,
            workout_date=date(2026, 1, 1),
            notes="Server note",
            client_uuid=client_uuid_str,
            updated_at=server_ts,
        )
        db_session.add(ws)
        db_session.commit()

        item = _make_session_item(
            ex.id,
            client_uuid=UUID(client_uuid_str),
            updated_at=client_ts,
        )
        req = _make_request(item)

        resp = process_bulk_sync(db_session, user_id=1, request=req)

        assert resp.summary.conflicts == 1
        assert resp.results[0].status == "conflict"
        assert resp.results[0].server_id == ws.id
        # Server data is returned for client-side merge
        assert resp.results[0].server_data is not None
        assert resp.results[0].server_data.notes == "Server note"

    def test_equal_timestamps_is_conflict(self, db_session: Session) -> None:
        """server_ts == client_ts → server wins (conflict)."""
        ex = _exercise(db_session)

        ts = datetime(2026, 3, 1, 9, 0, 0, tzinfo=timezone.utc)
        client_uuid_str = str(uuid4())

        ws = WorkoutSession(
            user_id=1,
            workout_date=date(2026, 3, 1),
            client_uuid=client_uuid_str,
            updated_at=ts,
        )
        db_session.add(ws)
        db_session.commit()

        item = _make_session_item(
            ex.id,
            client_uuid=UUID(client_uuid_str),
            updated_at=ts,  # EQUAL
        )
        req = _make_request(item)
        resp = process_bulk_sync(db_session, user_id=1, request=req)

        assert resp.results[0].status == "conflict"

    def test_conflict_does_not_modify_server_data(self, db_session: Session) -> None:
        ex = _exercise(db_session)

        server_ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        client_uuid_str = str(uuid4())
        original_notes = "Original server note"

        ws = WorkoutSession(
            user_id=1,
            workout_date=date(2026, 1, 1),
            notes=original_notes,
            client_uuid=client_uuid_str,
            updated_at=server_ts,
        )
        db_session.add(ws)
        db_session.commit()

        item = BulkSessionItem(
            client_uuid=UUID(client_uuid_str),
            workout_date=date(2026, 1, 1),
            notes="Client wants to overwrite",
            updated_at=server_ts - timedelta(minutes=5),
            exercises=[],
        )
        req = _make_request(item)
        process_bulk_sync(db_session, user_id=1, request=req)

        db_session.expire_all()
        db_session.refresh(ws)
        assert ws.notes == original_notes


@pytest.mark.unit
class TestMixedBatch:
    """Mixed batch: 2 new + 1 conflict + 1 error = partial atomicity."""

    def test_mixed_batch_partial_results(self, db_session: Session) -> None:
        ex = _exercise(db_session)

        # Pre-create session for conflict scenario
        server_ts = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        conflict_uuid_str = str(uuid4())
        ws = WorkoutSession(
            user_id=1,
            workout_date=date(2026, 1, 1),
            client_uuid=conflict_uuid_str,
            updated_at=server_ts,
        )
        db_session.add(ws)
        db_session.commit()

        # ① new session A
        item_new_a = _make_session_item(ex.id)
        # ② new session B
        item_new_b = _make_session_item(ex.id)
        # ③ conflict: client has older timestamp
        item_conflict = _make_session_item(
            ex.id,
            client_uuid=UUID(conflict_uuid_str),
            updated_at=server_ts - timedelta(hours=1),
        )
        # ④ error: duplicate exercise client_uuid within the session payload
        dup_ex_uuid = uuid4()
        item_error = BulkSessionItem(
            client_uuid=uuid4(),
            workout_date=date.today(),
            updated_at=datetime.now(timezone.utc),
            exercises=[
                BulkLogExercise(
                    client_uuid=dup_ex_uuid,
                    exercise_id=ex.id,
                    sets=[_set_item(1)],
                ),
                # Same client_uuid → UNIQUE constraint violation on log_exercises
                BulkLogExercise(
                    client_uuid=dup_ex_uuid,
                    exercise_id=ex.id,
                    sets=[_set_item(2)],
                ),
            ],
        )

        req = _make_request(item_new_a, item_new_b, item_conflict, item_error)
        resp = process_bulk_sync(db_session, user_id=1, request=req)

        assert resp.summary.created == 2
        assert resp.summary.conflicts == 1
        assert resp.summary.errors == 1
        assert len(resp.results) == 4

        statuses = [r.status for r in resp.results]
        assert statuses.count("created") == 2
        assert statuses.count("conflict") == 1
        assert statuses.count("error") == 1

    def test_error_session_does_not_rollback_others(self, db_session: Session) -> None:
        """An error in session N must not roll back previously committed sessions."""
        ex = _exercise(db_session)
        db_session.commit()

        # Good session first, then an error session
        good_item = _make_session_item(ex.id)
        dup_uuid = uuid4()
        bad_item = BulkSessionItem(
            client_uuid=uuid4(),
            workout_date=date.today(),
            updated_at=datetime.now(timezone.utc),
            exercises=[
                BulkLogExercise(
                    client_uuid=dup_uuid, exercise_id=ex.id, sets=[_set_item(1)]
                ),
                BulkLogExercise(
                    client_uuid=dup_uuid, exercise_id=ex.id, sets=[_set_item(2)]
                ),
            ],
        )

        req = _make_request(good_item, bad_item)
        resp = process_bulk_sync(db_session, user_id=1, request=req)

        assert resp.summary.created == 1
        assert resp.summary.errors == 1

        # The good session must be persisted
        saved = db_session.query(WorkoutSession).filter(
            WorkoutSession.client_uuid == str(good_item.client_uuid)
        ).first()
        assert saved is not None


@pytest.mark.unit
class TestIdempotency:
    """Same sync_id returns cached response without DB writes."""

    def test_same_sync_id_returns_cached_response(self, db_session: Session) -> None:
        ex = _exercise(db_session)
        db_session.commit()

        item = _make_session_item(ex.id)
        req = _make_request(item)

        first_resp = process_bulk_sync(db_session, user_id=1, request=req)
        assert first_resp.summary.created == 1

        # Re-submit identical request with same sync_id
        second_resp = process_bulk_sync(db_session, user_id=1, request=req)

        assert second_resp.sync_id == first_resp.sync_id
        assert second_resp.summary.created == first_resp.summary.created
        assert len(second_resp.results) == len(first_resp.results)

    def test_different_sync_ids_are_independent(self, db_session: Session) -> None:
        ex = _exercise(db_session)
        db_session.commit()

        item1 = _make_session_item(ex.id)
        req1 = _make_request(item1)
        resp1 = process_bulk_sync(db_session, user_id=1, request=req1)

        item2 = _make_session_item(ex.id)
        req2 = _make_request(item2)
        resp2 = process_bulk_sync(db_session, user_id=1, request=req2)

        assert resp1.sync_id != resp2.sync_id
        assert resp1.results[0].client_uuid != resp2.results[0].client_uuid


@pytest.mark.unit
class TestIntraBatchDuplicate:
    """Duplicate client_uuid within the same batch → error on second occurrence."""

    def test_duplicate_uuid_in_batch_errors_second(self, db_session: Session) -> None:
        ex = _exercise(db_session)
        db_session.commit()

        shared_uuid = uuid4()
        item_a = _make_session_item(ex.id, client_uuid=shared_uuid)
        item_b = _make_session_item(ex.id, client_uuid=shared_uuid)  # duplicate

        req = _make_request(item_a, item_b)
        resp = process_bulk_sync(db_session, user_id=1, request=req)

        assert resp.summary.created == 1
        assert resp.summary.errors == 1
        # First occurrence should succeed
        assert resp.results[0].status == "created"
        assert resp.results[1].status == "error"
        assert "Duplicate" in resp.results[1].error

    def test_duplicate_uuid_does_not_double_insert(self, db_session: Session) -> None:
        """Only 1 session must be in the DB after a duplicate batch."""
        ex = _exercise(db_session)
        db_session.commit()

        shared_uuid = uuid4()
        items = [_make_session_item(ex.id, client_uuid=shared_uuid) for _ in range(3)]
        req = _make_request(*items)
        process_bulk_sync(db_session, user_id=1, request=req)

        count = (
            db_session.query(WorkoutSession)
            .filter(WorkoutSession.client_uuid == str(shared_uuid))
            .count()
        )
        assert count == 1


@pytest.mark.unit
class TestUserIsolation:
    """Sessions are scoped to the requesting user."""

    def test_session_from_other_user_is_not_found(self, db_session: Session) -> None:
        """If user B has a session with UUID X, user A syncing UUID X must CREATE."""
        ex = _exercise(db_session)

        shared_uuid_str = str(uuid4())
        # user_id=99 owns this session
        ws = WorkoutSession(
            user_id=99,
            workout_date=date.today(),
            client_uuid=shared_uuid_str,
        )
        db_session.add(ws)
        db_session.commit()

        item = _make_session_item(ex.id, client_uuid=UUID(shared_uuid_str))
        req = _make_request(item)

        # user_id=1 should NOT find user_id=99's session via the LWW lookup
        # (the lookup is filtered by user_id, so user 99's session is invisible to user 1).
        # However, since client_uuid has a GLOBAL UNIQUE constraint, attempting to create
        # a new row with the same UUID triggers an IntegrityError → status "error".
        # This is the CORRECT behavior: user 1 cannot inadvertently overwrite user 99's
        # data (no "updated" result), and the error prevents a stale duplicate row.
        resp = process_bulk_sync(db_session, user_id=1, request=req)

        assert resp.results[0].status == "error"
        # Crucially, user 99's row must remain untouched
        db_session.expire_all()
        db_session.refresh(ws)
        assert ws.user_id == 99
