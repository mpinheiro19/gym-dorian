"""
Database connection and session management module.

This module provides:
- SQLAlchemy engine with connection pooling
- SessionLocal factory for creating database sessions
- get_db() dependency for FastAPI endpoint injection

The Base class is imported from models.base to register all models
for Alembic migrations. All models must inherit from Base to be
automatically discovered by Alembic.

Database Configuration:
    - Connection URL is loaded from app.core.config.Settings
    - Pool pre-ping ensures connections are alive before use
    - Sessions use autocommit=False for explicit transaction control
    - Sessions use autoflush=False for better control over DB writes

Usage in FastAPI endpoints:
    ```python
    from fastapi import Depends
    from sqlalchemy.orm import Session
    from database import get_db
    
    @app.get("/items/")
    def read_items(db: Session = Depends(get_db)):
        return db.query(Item).all()
    ```
"""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from app.core.config import settings

# Import Base to ensure all models are registered for Alembic
# All models must inherit from Base and be imported somewhere
# in the application startup for Alembic to detect them
from app.models.base import Base  # noqa: F401

# SQLAlchemy engine with connection pooling
# pool_pre_ping=True ensures connections are tested before use
engine = create_engine(
    str(settings.DATABASE_URL), 
    pool_pre_ping=True,
)

# Session factory for creating database sessions
# autocommit=False: Requires explicit commit() calls
# autoflush=False: Requires explicit flush() calls for better control
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.
    
    This function creates a new SQLAlchemy session for each request
    and ensures it is properly closed after the request is completed,
    even if an exception occurs.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        ```python
        @app.get("/users/")
        def get_users(db: Session = Depends(get_db)):
            users = db.query(User).all()
            return users
        ```
    
    Note:
        The session is automatically closed in the finally block,
        ensuring proper resource cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()