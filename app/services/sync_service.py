"""Bulk sync service implementing offline-first session synchronisation.

Architecture overview
---------------------
This module implements the business logic for ``POST /api/workouts/sessions/bulk``.

Each ``BulkSessionItem`` in the request is processed inside its own
**savepoint** (``db.begin_nested()``), which means:
- If a single session fails (validation error, DB constraint, …), only that
  session is rolled back.  All other sessions in the same request are not
  affected — this is the *partial atomicity* guarantee.
- A final ``db.commit()`` at the end of the function persists all successful
  savepoints in one transaction.

Conflict resolution (Last-Write-Wins, LWW)
-------------------------------------------
The LWW strategy operates at the **session level** (the whole ``WorkoutSession``
together with its exercises and sets is replaced atomically).

Decision table:

+----------------------------+------------------+---------------------+
| Condition                  | Server action    | Result status       |
+============================+==================+=====================+
| ``client_uuid`` not found  | INSERT           | ``"created"``       |
+----------------------------+------------------+---------------------+
| Found, client_ts > srv_ts  | DELETE + INSERT  | ``"updated"``       |
+----------------------------+------------------+---------------------+
| Found, srv_ts >= client_ts | No write         | ``"conflict"``      |
+----------------------------+------------------+---------------------+
| Any exception              | Rollback SP      | ``"error"``         |
+----------------------------+------------------+---------------------+

Idempotency
-----------
``BulkSyncRequest.sync_id`` is used as an idempotency key.  The in-memory
cache (``_idempotency_cache``) stores the ``BulkSyncResponse`` keyed by
``str(sync_id)``.  Resubmitting the same ``sync_id`` within the process
lifetime returns the cached response without re-executing any DB writes.

The cache is intentionally module-level so it survives across requests in
the same process.  Entries are never evicted in this implementation;
future work can add TTL via ``cachetools`` or externalise to Redis.

Duplicate client_uuid within a batch
-------------------------------------
If the same ``client_uuid`` appears more than once in the ``sessions`` list,
only the first occurrence is processed.  Subsequent duplicates receive
status ``"error"`` with an explanatory message.  This prevents accidental
double-inserts in malformed sync payloads and satisfies the UNIQUE constraint
on ``workout_sessions.client_uuid``.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.log import LogExercise, LogSet, WorkoutSession
from app.schemas.sync_schema import (
    BulkLogExercise,
    BulkSessionItem,
    BulkSetDetail,
    BulkSyncRequest,
    BulkSyncResponse,
    SessionSyncResult,
    SyncSummary,
)
from app.schemas.workout_schema import WorkoutSessionResponse

# ---------------------------------------------------------------------------
# In-memory idempotency cache
# key: str(sync_id)   value: BulkSyncResponse (already computed)
# ---------------------------------------------------------------------------
_idempotency_cache: Dict[str, BulkSyncResponse] = {}


def clear_idempotency_cache() -> None:
    """Clear the in-memory idempotency cache.

    Intended for **testing only**.  Call this inside test fixtures or
    teardown hooks to avoid cross-test contamination.
    """
    _idempotency_cache.clear()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _make_aware(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware (UTC assumed when naive)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _create_log_sets(db: Session, log_exercise_id: int, sets: List[BulkSetDetail]) -> None:
    """Insert ``LogSet`` rows for a given ``LogExercise``.

    Args:
        db: Active SQLAlchemy session (no commit issued here).
        log_exercise_id: FK to the parent ``LogExercise`` row.
        sets: Ordered list of ``BulkSetDetail`` items from the client.
    """
    for s in sets:
        db.add(LogSet(
            log_exercise_id=log_exercise_id,
            set_number=s.set_number,
            reps=s.reps,
            weight=s.weight,
            rpe=s.rpe,
            notes=s.notes,
            rest_time_seconds=s.rest_time_seconds,
            client_uuid=str(s.client_uuid),
        ))


def _create_log_exercises(
    db: Session,
    session_id: int,
    exercises: List[BulkLogExercise],
) -> None:
    """Insert ``LogExercise`` + ``LogSet`` rows for a given ``WorkoutSession``.

    Args:
        db: Active SQLAlchemy session (no commit issued here).
        session_id: FK to the parent ``WorkoutSession`` row.
        exercises: List of ``BulkLogExercise`` items from the client.
    """
    for ex in exercises:
        log_exercise = LogExercise(
            session_id=session_id,
            exercise_id=ex.exercise_id,
            client_uuid=str(ex.client_uuid),
        )
        db.add(log_exercise)
        db.flush()  # need log_exercise.id for FK in LogSet
        _create_log_sets(db, log_exercise.id, ex.sets)


def _insert_session(
    db: Session,
    user_id: int,
    item: BulkSessionItem,
) -> WorkoutSession:
    """Create a new ``WorkoutSession`` and all child entities from a sync item.

    Args:
        db: Active SQLAlchemy session.
        user_id: Authenticated user PK.
        item: Validated ``BulkSessionItem`` from the client.

    Returns:
        The newly created and flushed ``WorkoutSession`` instance.
    """
    ws = WorkoutSession(
        user_id=user_id,
        workout_date=item.workout_date,
        duration_minutes=item.duration_minutes,
        notes=item.notes,
        template_id=item.template_id,
        plan_id=item.plan_id,
        client_uuid=str(item.client_uuid),
        # Override updated_at so the server record reflects the client's write
        # time.  This is critical for LWW to be stable on round-trips.
        updated_at=_make_aware(item.updated_at),
    )
    db.add(ws)
    db.flush()
    _create_log_exercises(db, ws.id, item.exercises)
    db.flush()
    db.refresh(ws)
    return ws


def _replace_session(
    db: Session,
    existing: WorkoutSession,
    item: BulkSessionItem,
) -> WorkoutSession:
    """Replace all exercises/sets of an existing session with new client data.

    Only used when the client wins the LWW check.  The session-level fields
    are updated in-place; exercises + sets are deleted and re-created.

    Args:
        db: Active SQLAlchemy session.
        existing: The server ``WorkoutSession`` to update.
        item: Validated ``BulkSessionItem`` from the client with newer data.

    Returns:
        The updated and refreshed ``WorkoutSession`` instance.
    """
    existing.workout_date = item.workout_date
    existing.duration_minutes = item.duration_minutes
    existing.notes = item.notes
    existing.template_id = item.template_id
    existing.plan_id = item.plan_id
    existing.updated_at = _make_aware(item.updated_at)

    # Delete existing child entities (cascade would also handle LogSets)
    for le in list(existing.exercises_done):
        db.delete(le)
    db.flush()

    # Re-create with fresh client data
    _create_log_exercises(db, existing.id, item.exercises)
    db.flush()
    db.refresh(existing)
    return existing


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def process_bulk_sync(
    db: Session,
    user_id: int,
    request: BulkSyncRequest,
) -> BulkSyncResponse:
    """Process a bulk sync request and return per-session results.

    This is the main entry point called by the route handler.

    LWW logic per session
    ~~~~~~~~~~~~~~~~~~~~~~
    1. Open a savepoint.
    2. Look up ``workout_sessions`` by ``(client_uuid, user_id)``.
    3. **Not found** → INSERT full session tree → status ``"created"``.
    4. **Found** → compare ``item.updated_at`` (client) vs
       ``existing.updated_at`` (server):
       - client  > server → replace session tree → status ``"updated"``.
       - server >= client → no write, return server copy → status ``"conflict"``.
    5. On any exception → rollback savepoint → status ``"error"``.
    6. After all sessions → ``db.commit()`` to persist all savepoints.

    Idempotency
    ~~~~~~~~~~~
    If ``request.sync_id`` is found in ``_idempotency_cache``, the cached
    ``BulkSyncResponse`` is returned immediately without touching the DB.

    Args:
        db: SQLAlchemy session (provided by FastAPI ``Depends(get_db)``).
        user_id: Authenticated user whose sessions are being synced.
        request: Validated ``BulkSyncRequest`` from the HTTP body.

    Returns:
        ``BulkSyncResponse`` with one ``SessionSyncResult`` per session.
    """
    cache_key = str(request.sync_id)

    # ------------------------------------------------------------------
    # Idempotency: return cached result on replay
    # ------------------------------------------------------------------
    if cache_key in _idempotency_cache:
        return _idempotency_cache[cache_key]

    results: List[SessionSyncResult] = []
    # Track client_uuids seen within this batch to detect intra-batch duplicates
    seen_in_batch: set[str] = set()

    for item in request.sessions:
        uuid_str = str(item.client_uuid)

        # ------------------------------------------------------------------
        # Guard: duplicate client_uuid within the same batch
        # ------------------------------------------------------------------
        if uuid_str in seen_in_batch:
            results.append(SessionSyncResult(
                client_uuid=item.client_uuid,
                status="error",
                error=(
                    f"Duplicate client_uuid '{uuid_str}' within the same batch. "
                    "Each session must have a unique UUID."
                ),
            ))
            continue

        seen_in_batch.add(uuid_str)

        # ------------------------------------------------------------------
        # Per-session savepoint for partial atomicity
        # ------------------------------------------------------------------
        savepoint = db.begin_nested()
        try:
            existing: WorkoutSession | None = (
                db.query(WorkoutSession)
                .filter(
                    WorkoutSession.client_uuid == uuid_str,
                    WorkoutSession.user_id == user_id,
                )
                .first()
            )

            if existing is None:
                # ── CREATE ──────────────────────────────────────────────────
                ws = _insert_session(db, user_id, item)
                savepoint.commit()
                results.append(SessionSyncResult(
                    client_uuid=item.client_uuid,
                    status="created",
                    server_id=ws.id,
                    server_data=WorkoutSessionResponse.model_validate(ws),
                ))

            else:
                # ── LWW conflict check ───────────────────────────────────
                client_ts = _make_aware(item.updated_at)
                server_ts = _make_aware(existing.updated_at)

                if client_ts > server_ts:
                    # Client wins → UPDATE
                    ws = _replace_session(db, existing, item)
                    savepoint.commit()
                    results.append(SessionSyncResult(
                        client_uuid=item.client_uuid,
                        status="updated",
                        server_id=ws.id,
                        server_data=WorkoutSessionResponse.model_validate(ws),
                    ))
                else:
                    # Server wins → CONFLICT (no write)
                    savepoint.commit()
                    results.append(SessionSyncResult(
                        client_uuid=item.client_uuid,
                        status="conflict",
                        server_id=existing.id,
                        server_data=WorkoutSessionResponse.model_validate(existing),
                    ))

        except Exception as exc:  # noqa: BLE001
            savepoint.rollback()
            results.append(SessionSyncResult(
                client_uuid=item.client_uuid,
                status="error",
                error=str(exc),
            ))

    # Persist all successful savepoints in a single transaction
    db.commit()

    # Build summary
    summary = SyncSummary(
        created=sum(1 for r in results if r.status == "created"),
        updated=sum(1 for r in results if r.status == "updated"),
        conflicts=sum(1 for r in results if r.status == "conflict"),
        errors=sum(1 for r in results if r.status == "error"),
    )

    response = BulkSyncResponse(
        sync_id=request.sync_id,
        results=results,
        summary=summary,
    )

    # Cache for idempotency
    _idempotency_cache[cache_key] = response
    return response
