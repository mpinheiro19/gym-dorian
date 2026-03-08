"""
Unit tests for Exercise factory.

These tests verify that factory functions create valid test data.
"""

import pytest
import os


from tests.fixtures.factories import (
    ExerciseFactory,
    WorkoutSessionFactory,
    LogExerciseFactory,
    LogSetFactory
)


@pytest.mark.unit
class TestExerciseFactory:
    """Test suite for ExerciseFactory."""
    
    def test_create_default_exercise(self):
        """Test creating an exercise with default values."""
        exercise = ExerciseFactory.create()
        
        assert exercise.name == "Test Exercise"
        assert exercise.agonist_muscle_group == "Test Group"
        assert exercise.equipment_type == "Test Equipment"
    
    def test_create_custom_exercise(self):
        """Test creating an exercise with custom values."""
        exercise = ExerciseFactory.create(
            name="Bench Press",
            agonist_muscle_group="Chest",
            equipment_type="Barbell"
        )
        
        assert exercise.name == "Bench Press"
        assert exercise.agonist_muscle_group == "Chest"
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
        assert session.workout_date == date.today()
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
        assert session.workout_date == custom_date
        assert session.duration_minutes == 90
        assert session.notes == "Heavy lifting"
    
    def test_create_session_batch(self):
        """Test creating multiple workout sessions."""
        sessions = WorkoutSessionFactory.create_batch(5)
        
        assert len(sessions) == 5
        
        # Dates should be sequential
        for i in range(len(sessions) - 1):
            assert sessions[i + 1].workout_date > sessions[i].workout_date
    
    def test_create_session_batch_custom_start_date(self):
        """Test creating multiple sessions with custom start date."""
        from datetime import date
        
        start = date(2025, 12, 1)
        sessions = WorkoutSessionFactory.create_batch(3, start_date=start)
        
        assert sessions[0].workout_date == start
        assert sessions[1].workout_date == date(2025, 12, 2)
        assert sessions[2].workout_date == date(2025, 12, 3)


@pytest.mark.unit
class TestLogExerciseFactory:
    """Test suite for LogExerciseFactory."""

    def test_create_log_exercise(self):
        """Test creating an exercise log without sets."""
        log = LogExerciseFactory.create(session_id=1, exercise_id=1)

        assert log.session_id == 1
        assert log.exercise_id == 1
        # LogExercise without sets should have zero for calculated properties
        assert log.sets_completed == 0
        assert log.top_weight == 0
        assert log.total_reps == 0

    def test_create_log_exercise_with_sets(self):
        """Test creating an exercise log with sets using LogSetFactory."""
        log = LogExerciseFactory.create(session_id=5, exercise_id=10)

        # Note: In a real test with database, we would need log.id
        # For unit test, we'll use a mock ID
        log.id = 1

        # Create sets using LogSetFactory
        sets = LogSetFactory.create_batch(
            log_exercise_id=log.id,
            count=5,
            base_weight=150.0,
            base_reps=10
        )

        # Simulate adding sets to the log exercise
        log.sets = sets

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
        assert logs[0].exercise_id == 1
        assert logs[1].exercise_id == 2
        assert logs[2].exercise_id == 3


@pytest.mark.unit
class TestLogSetFactory:
    """Test suite for LogSetFactory."""

    def test_create_default_set(self):
        """Test creating a set with default values."""
        log_set = LogSetFactory.create(log_exercise_id=1)

        assert log_set.log_exercise_id == 1
        assert log_set.set_number == 1
        assert log_set.reps == 10
        assert log_set.weight == 100.0

    def test_create_custom_set(self):
        """Test creating a set with custom values."""
        log_set = LogSetFactory.create(
            log_exercise_id=2,
            set_number=3,
            reps=12,
            weight=150.0,
            rpe=8,
            notes="Heavy set"
        )

        assert log_set.log_exercise_id == 2
        assert log_set.set_number == 3
        assert log_set.reps == 12
        assert log_set.weight == 150.0
        assert log_set.rpe == 8
        assert log_set.notes == "Heavy set"

    def test_create_set_batch(self):
        """Test creating multiple sets."""
        sets = LogSetFactory.create_batch(
            log_exercise_id=1,
            count=4,
            base_weight=100.0
        )

        assert len(sets) == 4
        assert all(s.log_exercise_id == 1 for s in sets)
        assert sets[0].set_number == 1
        assert sets[3].set_number == 4

    def test_create_set_batch_with_custom_weight(self):
        """Test creating multiple sets with custom base weight."""
        sets = LogSetFactory.create_batch(
            log_exercise_id=1,
            count=2,
            base_weight=200.0,
            base_reps=8
        )

        assert sets[0].weight == 200.0
        assert sets[1].weight == 200.0
        assert sets[0].reps == 8
        assert sets[1].reps == 8
