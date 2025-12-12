"""
Unit tests for Exercise factory.

These tests verify that factory functions create valid test data.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from tests.fixtures.factories import (
    ExerciseFactory,
    WorkoutSessionFactory,
    LogExerciseFactory
)


@pytest.mark.unit
class TestExerciseFactory:
    """Test suite for ExerciseFactory."""
    
    def test_create_default_exercise(self):
        """Test creating an exercise with default values."""
        exercise = ExerciseFactory.create()
        
        assert exercise.name == "Test Exercise"
        assert exercise.muscle_group == "Test Group"
        assert exercise.equipment_type == "Test Equipment"
    
    def test_create_custom_exercise(self):
        """Test creating an exercise with custom values."""
        exercise = ExerciseFactory.create(
            name="Bench Press",
            muscle_group="Chest",
            equipment_type="Barbell"
        )
        
        assert exercise.name == "Bench Press"
        assert exercise.muscle_group == "Chest"
        assert exercise.equipment_type == "Barbell"
    
    def test_create_exercise_batch(self):
        """Test creating multiple exercises."""
        exercises = ExerciseFactory.create_batch(5)
        
        assert len(exercises) == 5
        assert all(ex.name.startswith("Exercise") for ex in exercises)
    
    def test_create_exercise_batch_with_prefix(self):
        """Test creating multiple exercises with custom prefix."""
        exercises = ExerciseFactory.create_batch(3, prefix="Movement")
        
        assert len(exercises) == 3
        assert exercises[0].name == "Movement 0"
        assert exercises[1].name == "Movement 1"
        assert exercises[2].name == "Movement 2"


@pytest.mark.unit
class TestWorkoutSessionFactory:
    """Test suite for WorkoutSessionFactory."""
    
    def test_create_default_session(self):
        """Test creating a workout session with default values."""
        from datetime import date
        
        session = WorkoutSessionFactory.create()
        
        assert session.user_id == 1
        assert session.date == date.today()
        assert session.duration_minutes == 60
    
    def test_create_custom_session(self):
        """Test creating a workout session with custom values."""
        from datetime import date
        
        custom_date = date(2025, 12, 10)
        session = WorkoutSessionFactory.create(
            user_id=2,
            workout_date=custom_date,
            duration_minutes=90,
            notes="Heavy lifting"
        )
        
        assert session.user_id == 2
        assert session.date == custom_date
        assert session.duration_minutes == 90
        assert session.notes == "Heavy lifting"
    
    def test_create_session_batch(self):
        """Test creating multiple workout sessions."""
        sessions = WorkoutSessionFactory.create_batch(5)
        
        assert len(sessions) == 5
        
        # Dates should be sequential
        for i in range(len(sessions) - 1):
            assert sessions[i + 1].date > sessions[i].date
    
    def test_create_session_batch_custom_start_date(self):
        """Test creating multiple sessions with custom start date."""
        from datetime import date
        
        start = date(2025, 12, 1)
        sessions = WorkoutSessionFactory.create_batch(3, start_date=start)
        
        assert sessions[0].date == start
        assert sessions[1].date == date(2025, 12, 2)
        assert sessions[2].date == date(2025, 12, 3)


@pytest.mark.unit
class TestLogExerciseFactory:
    """Test suite for LogExerciseFactory."""
    
    def test_create_default_log(self):
        """Test creating an exercise log with default values."""
        log = LogExerciseFactory.create(session_id=1, exercise_id=1)
        
        assert log.session_id == 1
        assert log.exercise_id == 1
        assert log.sets_completed == 3
        assert log.top_weight == 100.0
        assert log.total_reps == 30
    
    def test_create_custom_log(self):
        """Test creating an exercise log with custom values."""
        log = LogExerciseFactory.create(
            session_id=5,
            exercise_id=10,
            sets_completed=5,
            top_weight=150.0,
            total_reps=50
        )
        
        assert log.session_id == 5
        assert log.exercise_id == 10
        assert log.sets_completed == 5
        assert log.top_weight == 150.0
        assert log.total_reps == 50
    
    def test_create_log_batch(self):
        """Test creating multiple exercise logs."""
        exercise_ids = [1, 2, 3]
        logs = LogExerciseFactory.create_batch(
            session_id=1,
            exercise_ids=exercise_ids
        )
        
        assert len(logs) == 3
        assert all(log.session_id == 1 for log in logs)
        
        # Weights should increase
        assert logs[1].top_weight > logs[0].top_weight
        assert logs[2].top_weight > logs[1].top_weight
    
    def test_create_log_batch_with_base_weight(self):
        """Test creating multiple logs with custom base weight."""
        logs = LogExerciseFactory.create_batch(
            session_id=1,
            exercise_ids=[1, 2],
            base_weight=200.0
        )
        
        assert logs[0].top_weight == 200.0
        assert logs[1].top_weight == 210.0
