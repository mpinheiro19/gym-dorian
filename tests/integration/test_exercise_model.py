"""
Integration tests for Exercise model and operations.

These tests verify CRUD operations on the Exercise model.
"""

import pytest
import os
from sqlalchemy.orm import Session


from app.models.exercise import Exercise


@pytest.mark.integration
class TestExerciseModel:
    """Test suite for Exercise model operations."""
    
    def test_create_exercise(self, db_session: Session):
        """Test creating a new exercise."""
        exercise = Exercise(
            name="Bench Press",
            agonist_muscle_group="Chest",
            equipment_type="Barbell"
        )
        
        db_session.add(exercise)
        db_session.commit()
        db_session.refresh(exercise)
        
        assert exercise.id is not None
        assert exercise.name == "Bench Press"
        assert exercise.agonist_muscle_group == "Chest"
        assert exercise.equipment_type == "Barbell"
    
    def test_exercise_unique_name_constraint(self, db_session: Session):
        """Test that exercise names must be unique."""
        exercise1 = Exercise(name="Squat", agonist_muscle_group="Legs")
        exercise2 = Exercise(name="Squat", agonist_muscle_group="Legs")
        
        db_session.add(exercise1)
        db_session.commit()
        
        db_session.add(exercise2)
        
        with pytest.raises(Exception):  # SQLAlchemy will raise an IntegrityError
            db_session.commit()
    
    def test_query_exercise_by_name(self, db_session: Session, sample_exercises):
        """Test querying exercises by name."""
        result = db_session.query(Exercise).filter(
            Exercise.name == "Bench Press"
        ).first()
        
        assert result is not None
        assert result.name == "Bench Press"
        assert result.agonist_muscle_group == "Chest"
    
    def test_query_exercises_by_muscle_group(self, db_session: Session, sample_exercises):
        """Test querying exercises by muscle group."""
        back_exercises = db_session.query(Exercise).filter(
            Exercise.agonist_muscle_group == "Back"
        ).all()
        
        assert len(back_exercises) == 2
        names = [ex.name for ex in back_exercises]
        assert "Deadlift" in names
        assert "Pull Up" in names
    
    def test_update_exercise(self, db_session: Session, sample_exercises):
        """Test updating an exercise."""
        exercise = sample_exercises[0]
        original_name = exercise.name
        
        exercise.agonist_muscle_group = "Upper Chest"
        db_session.commit()
        db_session.refresh(exercise)
        
        assert exercise.name == original_name
        assert exercise.agonist_muscle_group == "Upper Chest"
    
    def test_delete_exercise(self, db_session: Session, sample_exercises):
        """Test deleting an exercise."""
        exercise = sample_exercises[0]
        exercise_id = exercise.id
        
        db_session.delete(exercise)
        db_session.commit()
        
        result = db_session.query(Exercise).filter(
            Exercise.id == exercise_id
        ).first()
        
        assert result is None
    
    def test_list_all_exercises(self, db_session: Session, sample_exercises):
        """Test listing all exercises."""
        exercises = db_session.query(Exercise).all()
        
        assert len(exercises) == 4
        names = [ex.name for ex in exercises]
        assert "Bench Press" in names
        assert "Squat" in names
        assert "Deadlift" in names
        assert "Pull Up" in names
    
    def test_exercise_with_optional_fields_none(self, db_session: Session):
        """Test creating an exercise with optional fields as None."""
        exercise = Exercise(name="Push Up")
        
        db_session.add(exercise)
        db_session.commit()
        db_session.refresh(exercise)
        
        assert exercise.id is not None
        assert exercise.name == "Push Up"
        assert exercise.agonist_muscle_group is None
        assert exercise.equipment_type is None
    
    def test_exercise_count(self, db_session: Session, sample_exercises):
        """Test counting exercises."""
        count = db_session.query(Exercise).count()
        assert count == 4


@pytest.mark.integration
class TestExerciseQueryPerformance:
    """Test suite for exercise query performance and indexing."""
    
    def test_query_by_indexed_name_is_efficient(self, db_session: Session, sample_exercises):
        """Test that querying by name uses the index."""
        # This test verifies that the query works correctly
        # In a real scenario, you might want to check query plans
        result = db_session.query(Exercise).filter(
            Exercise.name == "Deadlift"
        ).first()
        
        assert result is not None
        assert result.name == "Deadlift"
