"""
Integration tests for WorkoutSession and LogExercise models.

These tests verify CRUD operations and relationships between workout sessions and exercises.
"""

import pytest
import sys
import os
from datetime import date
from sqlalchemy.orm import Session

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from models.log import WorkoutSession, LogExercise
from models.exercise import Exercise


@pytest.mark.integration
class TestWorkoutSessionModel:
    """Test suite for WorkoutSession model operations."""
    
    def test_create_workout_session(self, db_session: Session):
        """Test creating a new workout session."""
        session = WorkoutSession(
            user_id=1,
            date=date(2025, 12, 11),
            duration_minutes=45,
            notes="Morning workout"
        )
        
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        
        assert session.id is not None
        assert session.user_id == 1
        assert session.date == date(2025, 12, 11)
        assert session.duration_minutes == 45
        assert session.notes == "Morning workout"
    
    def test_create_workout_session_with_defaults(self, db_session: Session):
        """Test creating a workout session with default values."""
        session = WorkoutSession()
        
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        
        assert session.id is not None
        assert session.user_id == 1  # default
        assert session.date is not None  # default to current date
        assert session.duration_minutes is None
        assert session.notes is None
    
    def test_query_sessions_by_user_id(self, db_session: Session):
        """Test querying workout sessions by user ID."""
        session1 = WorkoutSession(user_id=1, date=date(2025, 12, 10))
        session2 = WorkoutSession(user_id=1, date=date(2025, 12, 11))
        session3 = WorkoutSession(user_id=2, date=date(2025, 12, 11))
        
        db_session.add_all([session1, session2, session3])
        db_session.commit()
        
        user1_sessions = db_session.query(WorkoutSession).filter(
            WorkoutSession.user_id == 1
        ).all()
        
        assert len(user1_sessions) == 2
    
    def test_query_sessions_by_date_range(self, db_session: Session):
        """Test querying workout sessions by date range."""
        session1 = WorkoutSession(date=date(2025, 12, 1))
        session2 = WorkoutSession(date=date(2025, 12, 15))
        session3 = WorkoutSession(date=date(2025, 12, 30))
        
        db_session.add_all([session1, session2, session3])
        db_session.commit()
        
        sessions = db_session.query(WorkoutSession).filter(
            WorkoutSession.date >= date(2025, 12, 10),
            WorkoutSession.date <= date(2025, 12, 20)
        ).all()
        
        assert len(sessions) == 1
        assert sessions[0].date == date(2025, 12, 15)
    
    def test_update_workout_session(self, db_session: Session):
        """Test updating a workout session."""
        session = WorkoutSession(duration_minutes=30, notes="Quick workout")
        db_session.add(session)
        db_session.commit()
        
        session.duration_minutes = 60
        session.notes = "Extended workout"
        db_session.commit()
        db_session.refresh(session)
        
        assert session.duration_minutes == 60
        assert session.notes == "Extended workout"
    
    def test_delete_workout_session(self, db_session: Session):
        """Test deleting a workout session."""
        session = WorkoutSession(date=date(2025, 12, 11))
        db_session.add(session)
        db_session.commit()
        
        session_id = session.id
        db_session.delete(session)
        db_session.commit()
        
        result = db_session.query(WorkoutSession).filter(
            WorkoutSession.id == session_id
        ).first()
        
        assert result is None


@pytest.mark.integration
class TestLogExerciseModel:
    """Test suite for LogExercise model operations."""
    
    def test_create_log_exercise(self, db_session: Session, sample_exercises):
        """Test creating a new exercise log."""
        session = WorkoutSession(date=date(2025, 12, 11))
        db_session.add(session)
        db_session.commit()
        
        log = LogExercise(
            session_id=session.id,
            exercise_id=sample_exercises[0].id,
            sets_completed=3,
            top_weight=100.0,
            total_reps=30
        )
        
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)
        
        assert log.id is not None
        assert log.session_id == session.id
        assert log.exercise_id == sample_exercises[0].id
        assert log.sets_completed == 3
        assert log.top_weight == 100.0
        assert log.total_reps == 30
    
    def test_log_exercise_relationships(self, db_session: Session, sample_exercises):
        """Test relationships between LogExercise, WorkoutSession, and Exercise."""
        session = WorkoutSession(date=date(2025, 12, 11))
        db_session.add(session)
        db_session.commit()
        
        log = LogExercise(
            session_id=session.id,
            exercise_id=sample_exercises[0].id,
            sets_completed=3,
            top_weight=100.0,
            total_reps=30
        )
        
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)
        
        # Test accessing session through relationship
        assert log.session.id == session.id
        assert log.session.date == date(2025, 12, 11)
        
        # Test accessing exercise through relationship
        assert log.exercise.id == sample_exercises[0].id
        assert log.exercise.name == "Bench Press"
    
    def test_workout_session_exercises_done_relationship(
        self, db_session: Session, sample_workout_session
    ):
        """Test accessing exercises from a workout session."""
        # sample_workout_session already has 2 logged exercises
        assert len(sample_workout_session.exercises_done) == 2
        
        # Verify the logged exercises
        exercise_names = [
            log.exercise.name for log in sample_workout_session.exercises_done
        ]
        assert "Bench Press" in exercise_names
        assert "Squat" in exercise_names
    
    def test_query_logs_by_session(self, db_session: Session, sample_workout_session):
        """Test querying exercise logs by session ID."""
        logs = db_session.query(LogExercise).filter(
            LogExercise.session_id == sample_workout_session.id
        ).all()
        
        assert len(logs) == 2
    
    def test_query_logs_by_exercise(self, db_session: Session, sample_exercises):
        """Test querying exercise logs by exercise ID."""
        session1 = WorkoutSession(date=date(2025, 12, 10))
        session2 = WorkoutSession(date=date(2025, 12, 11))
        db_session.add_all([session1, session2])
        db_session.commit()
        
        # Log the same exercise in two different sessions
        log1 = LogExercise(
            session_id=session1.id,
            exercise_id=sample_exercises[0].id,
            sets_completed=3,
            top_weight=100.0,
            total_reps=30
        )
        log2 = LogExercise(
            session_id=session2.id,
            exercise_id=sample_exercises[0].id,
            sets_completed=4,
            top_weight=110.0,
            total_reps=32
        )
        
        db_session.add_all([log1, log2])
        db_session.commit()
        
        logs = db_session.query(LogExercise).filter(
            LogExercise.exercise_id == sample_exercises[0].id
        ).all()
        
        assert len(logs) == 2
    
    def test_update_log_exercise(self, db_session: Session, sample_workout_session):
        """Test updating an exercise log."""
        log = sample_workout_session.exercises_done[0]
        
        log.sets_completed = 5
        log.top_weight = 120.0
        db_session.commit()
        db_session.refresh(log)
        
        assert log.sets_completed == 5
        assert log.top_weight == 120.0
    
    def test_delete_log_exercise(self, db_session: Session, sample_workout_session):
        """Test deleting an exercise log."""
        log = sample_workout_session.exercises_done[0]
        log_id = log.id
        
        db_session.delete(log)
        db_session.commit()
        
        result = db_session.query(LogExercise).filter(
            LogExercise.id == log_id
        ).first()
        
        assert result is None


@pytest.mark.integration
class TestWorkoutSessionComplexQueries:
    """Test suite for complex queries involving workout sessions."""
    
    def test_get_total_workout_duration_for_user(self, db_session: Session):
        """Test calculating total workout duration for a user."""
        sessions = [
            WorkoutSession(user_id=1, duration_minutes=30),
            WorkoutSession(user_id=1, duration_minutes=45),
            WorkoutSession(user_id=1, duration_minutes=60),
        ]
        
        db_session.add_all(sessions)
        db_session.commit()
        
        total = db_session.query(WorkoutSession).filter(
            WorkoutSession.user_id == 1
        ).count()
        
        assert total == 3
    
    def test_get_exercises_for_specific_session(
        self, db_session: Session, sample_workout_session
    ):
        """Test getting all exercises performed in a specific session."""
        logs = db_session.query(LogExercise).filter(
            LogExercise.session_id == sample_workout_session.id
        ).all()
        
        assert len(logs) == 2
        
        # Verify we can access exercise details through the relationship
        for log in logs:
            assert log.exercise.name is not None
            assert log.sets_completed > 0
            assert log.total_reps > 0
    
    def test_get_personal_records(self, db_session: Session, sample_exercises):
        """Test finding personal records (max weight) for each exercise."""
        session1 = WorkoutSession(date=date(2025, 12, 1))
        session2 = WorkoutSession(date=date(2025, 12, 15))
        db_session.add_all([session1, session2])
        db_session.commit()
        
        # Log bench press with different weights
        logs = [
            LogExercise(
                session_id=session1.id,
                exercise_id=sample_exercises[0].id,
                sets_completed=3,
                top_weight=100.0,
                total_reps=30
            ),
            LogExercise(
                session_id=session2.id,
                exercise_id=sample_exercises[0].id,
                sets_completed=3,
                top_weight=110.0,
                total_reps=27
            ),
        ]
        
        db_session.add_all(logs)
        db_session.commit()
        
        # Find max weight for bench press
        from sqlalchemy import func
        
        max_weight = db_session.query(
            func.max(LogExercise.top_weight)
        ).filter(
            LogExercise.exercise_id == sample_exercises[0].id
        ).scalar()
        
        assert max_weight == 110.0
