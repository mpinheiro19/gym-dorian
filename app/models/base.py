"""SQLAlchemy 2.0 Base Model and reusable mixins.

All models must inherit from this Base class to be registered
for Alembic migrations.
"""
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models using SQLAlchemy 2.0 style."""
    pass


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamp fields.

    Use this mixin on any model that needs automatic timestamp tracking.
    - created_at: set once when the record is first inserted
    - updated_at: set on insert AND automatically updated on every UPDATE
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=_utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )


class SyncMixin:
    """Mixin that adds a client_uuid field for offline-first sync support.

    client_uuid is generated on the client side before the record is sent
    to the server.  If none is provided the server generates one via the
    Python-side default so the column is always populated.

    The column has a UNIQUE constraint and an index to support fast lookup
    by client UUID during bulk sync operations.
    """

    client_uuid: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        unique=True,
        index=True,
        default=lambda: str(uuid4()),
        nullable=False,
    )