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
from app.models.log import WorkoutSession, LogExercise, LogSet
from app.models.template import WorkoutTemplate, TemplateExercise
from app.models.plan import WorkoutPlan, PlanWeek, PlanDay
from app.models.user import User
from app.models.enums import PlanStatus
from datetime import date


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
            agonist_muscle_group="Chest",
            equipment_type="Barbell"
        ),
        Exercise(
            name="Squat",
            agonist_muscle_group="Legs",
            equipment_type="Barbell"
        ),
        Exercise(
            name="Deadlift",
            agonist_muscle_group="Back",
            equipment_type="Barbell"
        ),
        Exercise(
            name="Pull Up",
            agonist_muscle_group="Back",
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
    log_exercise1 = LogExercise(
        session_id=session.id,
        exercise_id=sample_exercises[0].id
    )
    log_exercise2 = LogExercise(
        session_id=session.id,
        exercise_id=sample_exercises[1].id
    )

    db_session.add(log_exercise1)
    db_session.add(log_exercise2)
    db_session.flush()

    # Add sets for first exercise (3 sets of 10 reps @ 100kg)
    sets1 = [
        LogSet(log_exercise_id=log_exercise1.id, set_number=1, reps=10, weight=100.0),
        LogSet(log_exercise_id=log_exercise1.id, set_number=2, reps=10, weight=100.0),
        LogSet(log_exercise_id=log_exercise1.id, set_number=3, reps=10, weight=100.0),
    ]

    # Add sets for second exercise (4 sets of 8 reps @ 150kg)
    sets2 = [
        LogSet(log_exercise_id=log_exercise2.id, set_number=1, reps=8, weight=150.0),
        LogSet(log_exercise_id=log_exercise2.id, set_number=2, reps=8, weight=150.0),
        LogSet(log_exercise_id=log_exercise2.id, set_number=3, reps=8, weight=150.0),
        LogSet(log_exercise_id=log_exercise2.id, set_number=4, reps=8, weight=150.0),
    ]

    db_session.add_all(sets1 + sets2)
    db_session.commit()

    db_session.refresh(session)

    return session


@pytest.fixture(scope="function")
def sample_user(db_session: Session) -> User:
    """Create a sample user for plan-related tests.

    Returns:
        User: Persisted user instance
    """
    user = User(
        email="testuser@plantest.com",
        password_hash="hashed",
        full_name="Plan Test User",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def sample_template(db_session: Session, sample_exercises: list[Exercise]) -> WorkoutTemplate:
    """Create a sample WorkoutTemplate for testing.

    Returns:
        WorkoutTemplate: Persisted template with one exercise
    """
    tmpl = WorkoutTemplate(user_id=1, name="Upper Body A", description="Push day")
    db_session.add(tmpl)
    db_session.flush()
    te = TemplateExercise(
        template_id=tmpl.id,
        exercise_id=sample_exercises[0].id,
        order_index=0,
    )
    db_session.add(te)
    db_session.commit()
    db_session.refresh(tmpl)
    return tmpl


@pytest.fixture(scope="function")
def sample_plan(db_session: Session, sample_template: WorkoutTemplate) -> WorkoutPlan:
    """Create a sample WorkoutPlan (active, 1 week, Monday assigned).

    Returns:
        WorkoutPlan: Persisted plan with one week and one day
    """
    plan = WorkoutPlan(
        user_id=sample_template.user_id,
        name="Test Plan",
        description="A plan for testing",
        status=PlanStatus.ACTIVE,
        start_date=date.today(),
    )
    db_session.add(plan)
    db_session.flush()

    week = PlanWeek(plan_id=plan.id, week_number=1, name="Week 1")
    db_session.add(week)
    db_session.flush()

    day = PlanDay(
        week_id=week.id,
        day_of_week=0,  # Monday
        template_id=sample_template.id,
    )
    db_session.add(day)
    db_session.commit()
    db_session.refresh(plan)
    return plan


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
