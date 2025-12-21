"""SQLAlchemy 2.0 Base Model.

All models must inherit from this Base class to be registered
for Alembic migrations.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models using SQLAlchemy 2.0 style."""
    pass