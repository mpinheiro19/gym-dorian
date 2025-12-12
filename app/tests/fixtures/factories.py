"""
Factory functions for creating test data.

These factories provide convenient methods for creating test objects
with customizable attributes.
"""

import sys
import os
from datetime import date, timedelta
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from models.exercise import Exercise
from models.log import WorkoutSession, LogExercise


class ExerciseFactory:
    """Factory for creating Exercise test instances."""
    
    @staticmethod
    def create(
        name: str = "Test Exercise",
        muscle_group: Optional[str] = "Test Group",
        equipment_type: Optional[str] = "Test Equipment"
    ) -> Exercise:
        """
        Create an Exercise instance.
        
        Args:
            name: Exercise name
            muscle_group: Target muscle group
            equipment_type: Required equipment
            
        Returns:
            Exercise: New exercise instance
        """
        return Exercise(
            name=name,
            muscle_group=muscle_group,
            equipment_type=equipment_type
        )
    
    @staticmethod
    def create_batch(count: int, prefix: str = "Exercise") -> list[Exercise]:
        """
        Create multiple exercise instances.
        
        Args:
            count: Number of exercises to create
            prefix: Name prefix for exercises
            
        Returns:
            list[Exercise]: List of exercise instances
        """
        return [
            Exercise(
                name=f"{prefix} {i}",
                muscle_group=f"Group {i % 3}",
                equipment_type=f"Equipment {i % 2}"
            )
            for i in range(count)
        ]


class WorkoutSessionFactory:
    """Factory for creating WorkoutSession test instances."""
    
    @staticmethod
    def create(
        user_id: int = 1,
        workout_date: Optional[date] = None,
        duration_minutes: Optional[int] = 60,
        notes: Optional[str] = None
    ) -> WorkoutSession:
        """
        Create a WorkoutSession instance.
        
        Args:
            user_id: User identifier
            workout_date: Date of workout
            duration_minutes: Duration in minutes
            notes: Session notes
            
        Returns:
            WorkoutSession: New workout session instance
        """
        if workout_date is None:
            workout_date = date.today()
        
        return WorkoutSession(
            user_id=user_id,
            date=workout_date,
            duration_minutes=duration_minutes,
            notes=notes
        )
    
    @staticmethod
    def create_batch(
        count: int,
        user_id: int = 1,
        start_date: Optional[date] = None
    ) -> list[WorkoutSession]:
        """
        Create multiple workout session instances.
        
        Args:
            count: Number of sessions to create
            user_id: User identifier
            start_date: Starting date (will increment for each session)
            
        Returns:
            list[WorkoutSession]: List of workout session instances
        """
        if start_date is None:
            start_date = date.today() - timedelta(days=count - 1)
        
        return [
            WorkoutSession(
                user_id=user_id,
                date=start_date + timedelta(days=i),
                duration_minutes=45 + (i * 5),
                notes=f"Session {i + 1}"
            )
            for i in range(count)
        ]


class LogExerciseFactory:
    """Factory for creating LogExercise test instances."""
    
    @staticmethod
    def create(
        session_id: int,
        exercise_id: int,
        sets_completed: int = 3,
        top_weight: float = 100.0,
        total_reps: int = 30
    ) -> LogExercise:
        """
        Create a LogExercise instance.
        
        Args:
            session_id: Workout session ID
            exercise_id: Exercise ID
            sets_completed: Number of sets
            top_weight: Heaviest weight used
            total_reps: Total repetitions
            
        Returns:
            LogExercise: New exercise log instance
        """
        return LogExercise(
            session_id=session_id,
            exercise_id=exercise_id,
            sets_completed=sets_completed,
            top_weight=top_weight,
            total_reps=total_reps
        )
    
    @staticmethod
    def create_batch(
        session_id: int,
        exercise_ids: list[int],
        base_weight: float = 100.0
    ) -> list[LogExercise]:
        """
        Create multiple exercise log instances for a session.
        
        Args:
            session_id: Workout session ID
            exercise_ids: List of exercise IDs
            base_weight: Base weight (will increment for each exercise)
            
        Returns:
            list[LogExercise]: List of exercise log instances
        """
        return [
            LogExercise(
                session_id=session_id,
                exercise_id=exercise_id,
                sets_completed=3 + (i % 2),
                top_weight=base_weight + (i * 10),
                total_reps=30 + (i * 2)
            )
            for i, exercise_id in enumerate(exercise_ids)
        ]
