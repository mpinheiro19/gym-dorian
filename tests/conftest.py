"""
Global pytest configuration and fixtures.

This module provides shared fixtures for all tests, including:
- Database session management
- Test client setup
- Mock data factories
"""

import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.database import get_db
from app.main import app
from app.models.base import Base
from app.models.exercise import Exercise
from app.models.log import WorkoutSession, LogExercise


# Use in-memory SQLite for tests (fast and isolated)
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine with StaticPool to maintain the same in-memory database
# across all connections in the same test
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Create a fresh database session for each test.
    
    This fixture:
    - Creates all tables before the test
    - Provides a clean session
    - Rolls back all changes after the test
    - Drops all tables after the test
    
    Yields:
        Session: SQLAlchemy database session
    """
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables to ensure clean state
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with database dependency override.
    
    This fixture provides a FastAPI TestClient with the database
    session overridden to use the test database.
    
    Args:
        db_session: Database session fixture
        
    Yields:
        TestClient: FastAPI test client
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def sample_exercises(db_session: Session) -> list[Exercise]:
    """
    Create sample exercises for testing.
    
    Returns:
        list[Exercise]: List of sample exercise objects
    """
    exercises = [
        Exercise(
            name="Bench Press",
            muscle_group="Chest",
            equipment_type="Barbell"
        ),
        Exercise(
            name="Squat",
            muscle_group="Legs",
            equipment_type="Barbell"
        ),
        Exercise(
            name="Deadlift",
            muscle_group="Back",
            equipment_type="Barbell"
        ),
        Exercise(
            name="Pull Up",
            muscle_group="Back",
            equipment_type="Bodyweight"
        ),
    ]
    
    db_session.add_all(exercises)
    db_session.commit()
    
    for exercise in exercises:
        db_session.refresh(exercise)
    
    return exercises


@pytest.fixture(scope="function")
def sample_workout_session(db_session: Session, sample_exercises: list[Exercise]) -> WorkoutSession:
    """
    Create a sample workout session with logged exercises.
    
    Args:
        db_session: Database session
        sample_exercises: List of sample exercises
        
    Returns:
        WorkoutSession: Sample workout session with exercises
    """
    from datetime import date
    
    session = WorkoutSession(
        user_id=1,
        workout_date=date(2025, 12, 10),
        duration_minutes=60,
        notes="Great workout session"
    )
    
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    
    # Add exercise logs
    log_exercises = [
        LogExercise(
            session_id=session.id,
            exercise_id=sample_exercises[0].id,
            sets_completed=3,
            top_weight=100.0,
            total_reps=30
        ),
        LogExercise(
            session_id=session.id,
            exercise_id=sample_exercises[1].id,
            sets_completed=4,
            top_weight=150.0,
            total_reps=32
        ),
    ]
    
    db_session.add_all(log_exercises)
    db_session.commit()
    
    db_session.refresh(session)
    
    return session


# Pytest configuration hooks
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """
    Automatically add markers to tests based on their location.
    
    This hook adds appropriate markers to tests:
    - Tests in tests/unit/ get the 'unit' marker
    - Tests in tests/integration/ get the 'integration' marker
    """
    for item in items:
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
