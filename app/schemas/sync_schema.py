"""Bulk sync schemas for offline-first synchronisation endpoint.

This module defines the request and response shapes for
``POST /api/workouts/sessions/bulk``.

Design decisions:
- All ``client_uuid`` fields are **required** in bulk payloads (unlike the
  regular Create schemas where they are Optional).  The sync endpoint is
  explicitly designed for clients that pre-generate UUIDs offline.
- ``BulkSessionItem.updated_at`` carries the *client-side* timestamp and is
  used as the "write timestamp" in the Last-Write-Wins (LWW) conflict
  resolution strategy.
- The status field in ``SessionSyncResult`` uses a enum-like string literal
  set: ``"created" | "updated" | "conflict" | "error"``.
- ``BulkSyncResponse.summary`` is an embedded ``SyncSummary`` model so the
  response body is fully typed and documented.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.workout_schema import WorkoutSessionResponse


# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------

class BulkSetDetail(BaseModel):
    """A single set submitted in a bulk sync payload.

    Attributes:
        client_uuid: UUID generated on the client before sending.  Required
            for idempotent set-level deduplication in future Plan 3 work.
        set_number: 1-based ordinal within this exercise (1, 2, 3, …).
        reps: Number of repetitions performed in this set.
        weight: Load lifted, in kilograms.
        rpe: Optional Rate of Perceived Exertion (1-10 Borg/RPE scale).
        notes: Free-text annotation for this specific set.
        rest_time_seconds: Rest period *after* this set, in seconds.
    """

    client_uuid: UUID = Field(..., description="Client-generated UUID for this set")
    set_number: int = Field(..., ge=1, le=100)
    reps: int = Field(..., ge=1, le=1000)
    weight: float = Field(..., ge=0, le=10000)
    rpe: Optional[int] = Field(None, ge=1, le=10, description="Rate of Perceived Exertion (1-10)")
    notes: Optional[str] = Field(None, max_length=500)
    rest_time_seconds: Optional[int] = Field(None, ge=0, le=3600)


class BulkLogExercise(BaseModel):
    """An exercise entry submitted inside a bulk sync session.

    Attributes:
        client_uuid: UUID generated on the client for this log-exercise entry.
        exercise_id: Server-side ``exercises.id`` PK.  The client must resolve
            the exercise ID before sending; exercise creation is out of scope
            for the sync endpoint.
        sets: One or more set entries (at least 1 required).
    """

    client_uuid: UUID = Field(..., description="Client-generated UUID for this log-exercise entry")
    exercise_id: int = Field(..., gt=0)
    sets: List[BulkSetDetail] = Field(..., min_length=1)


class BulkSessionItem(BaseModel):
    """A single workout session submitted in a bulk sync request.

    This schema represents one offline workout session the mobile client
    wants to persist on the server.

    Attributes:
        client_uuid: UUID generated on the client for this session.  Used as
            the lookup key on the server to detect duplicates.
        workout_date: Calendar date on which the workout was performed.
        duration_minutes: Total session time in minutes (optional).
        notes: Free-text session notes (optional, max 2 000 chars).
        template_id: Optional FK linking session to its originating template.
        plan_id: Optional FK linking session to its originating plan.
        exercises: Ordered list of exercises performed.
        updated_at: **Client-side modification timestamp**.  Used as the
            "write timestamp" for Last-Write-Wins conflict resolution.
            The client MUST set this to the wall-clock time in UTC at the
            moment the user last modified the session offline.
    """

    client_uuid: UUID = Field(..., description="Client-generated UUID for this session")
    workout_date: date = Field(..., description="Date the workout was performed")
    duration_minutes: Optional[int] = Field(None, ge=1, le=600)
    notes: Optional[str] = Field(None, max_length=2000)
    template_id: Optional[int] = Field(None, gt=0)
    plan_id: Optional[int] = Field(None, gt=0)
    exercises: List[BulkLogExercise] = Field(default_factory=list)
    updated_at: datetime = Field(
        ...,
        description=(
            "Client-side UTC timestamp of the last local modification.  "
            "The server uses this for LWW conflict resolution: if this value "
            "is greater than the server's updated_at, the session is updated; "
            "otherwise a conflict is returned."
        ),
    )


class BulkSyncRequest(BaseModel):
    """Top-level request body for the bulk sync endpoint.

    Attributes:
        sync_id: A UUID generated by the client for this entire sync batch.
            Used as an **idempotency key**: submitting the same ``sync_id``
            twice will return the cached result from the first successful run.
            Clients should generate a fresh UUID per sync attempt.
        sessions: List of session items to sync.  An empty list is valid and
            returns an empty result set (not an error).

    Example::

        {
          "sync_id": "a1b2c3d4-...",
          "sessions": [
            {
              "client_uuid": "...",
              "workout_date": "2026-03-07",
              "duration_minutes": 55,
              "exercises": [...],
              "updated_at": "2026-03-07T18:00:00Z"
            }
          ]
        }
    """

    sync_id: UUID = Field(..., description="Idempotency key for this sync batch")
    sessions: List[BulkSessionItem] = Field(
        default_factory=list,
        description="List of sessions to synchronise (can be empty)",
    )


# ---------------------------------------------------------------------------
# Output schemas
# ---------------------------------------------------------------------------

class SyncSummary(BaseModel):
    """Aggregate counts for a bulk sync response.

    Attributes:
        created: Sessions inserted as new records.
        updated: Sessions where the client had a newer ``updated_at`` and
            the server record was replaced.
        conflicts: Sessions where the server had an equal-or-newer
            ``updated_at``; the server data is returned for client-side merge.
        errors: Sessions that failed due to a validation or database error.
            These do **not** affect other sessions (partial atomicity).
    """

    created: int = 0
    updated: int = 0
    conflicts: int = 0
    errors: int = 0


class SessionSyncResult(BaseModel):
    """Per-session result within a bulk sync response.

    Attributes:
        client_uuid: Echoes the ``client_uuid`` from the request item so the
            client can correlate results without relying on list order.
        status: Outcome of processing this session.
            - ``"created"``: session was new and has been inserted.
            - ``"updated"``: client timestamp was newer; session was replaced.
            - ``"conflict"``: server timestamp was equal or newer; no write
              happened.  The ``server_data`` field contains the authoritative
              server record which the client should use to resolve the
              conflict locally.
            - ``"error"``: an exception occurred; the ``error`` field contains
              a human-readable message.
        server_id: The ``workout_sessions.id`` PK on the server (populated for
            ``created`` and ``updated`` and ``conflict`` statuses).
        error: Populated only when ``status == "error"``.
        server_data: Full ``WorkoutSessionResponse`` returned only when
            ``status == "conflict"``, so the client has the authoritative
            copy.  Also returned on ``"updated"`` for immediate cache sync.
    """

    client_uuid: UUID
    status: str = Field(..., pattern=r"^(created|updated|conflict|error)$")
    server_id: Optional[int] = None
    error: Optional[str] = None
    server_data: Optional[WorkoutSessionResponse] = None

    model_config = ConfigDict(from_attributes=True)


class BulkSyncResponse(BaseModel):
    """Top-level response body for ``POST /api/workouts/sessions/bulk``.

    HTTP status code is **207 Multi-Status** because different sessions can
    have different outcomes (created, conflict, error) in the same request.

    Attributes:
        sync_id: Echoes the ``sync_id`` from the request for correlation.
        results: One ``SessionSyncResult`` per session in the request, in the
            same order.
        summary: Aggregate counts across all results.
    """

    sync_id: UUID
    results: List[SessionSyncResult] = Field(default_factory=list)
    summary: SyncSummary = Field(default_factory=SyncSummary)

    model_config = ConfigDict(from_attributes=True)
