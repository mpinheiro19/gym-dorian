"""
Factory functions for creating test data.

These factories provide convenient methods for creating test objects
with customizable attributes.
"""

import os
from datetime import date, timedelta
from typing import Optional


from app.models.exercise import Exercise
from app.models.log import WorkoutSession, LogExercise, LogSet


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
            workout_date=workout_date,
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
                workout_date=start_date + timedelta(days=i),
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
        exercise_id: int
    ) -> LogExercise:
        """
        Create a LogExercise instance.

        Note: This creates the LogExercise without sets.
        Use LogSetFactory to create sets for this exercise.

        Args:
            session_id: Workout session ID
            exercise_id: Exercise ID

        Returns:
            LogExercise: New exercise log instance
        """
        return LogExercise(
            session_id=session_id,
            exercise_id=exercise_id
        )

    @staticmethod
    def create_batch(
        session_id: int,
        exercise_ids: list[int]
    ) -> list[LogExercise]:
        """
        Create multiple exercise log instances for a session.

        Note: This creates LogExercise instances without sets.
        Use LogSetFactory to create sets for these exercises.

        Args:
            session_id: Workout session ID
            exercise_ids: List of exercise IDs

        Returns:
            list[LogExercise]: List of exercise log instances
        """
        return [
            LogExercise(
                session_id=session_id,
                exercise_id=exercise_id
            )
            for exercise_id in exercise_ids
        ]


class LogSetFactory:
    """Factory for creating LogSet test instances."""

    @staticmethod
    def create(
        log_exercise_id: int,
        set_number: int = 1,
        reps: int = 10,
        weight: float = 100.0,
        rpe: Optional[int] = None,
        notes: Optional[str] = None,
        rest_time_seconds: Optional[int] = None
    ) -> LogSet:
        """
        Create a LogSet instance.

        Args:
            log_exercise_id: LogExercise ID
            set_number: Set sequence number
            reps: Number of repetitions
            weight: Weight used
            rpe: Rate of Perceived Exertion (1-10)
            notes: Set-specific notes
            rest_time_seconds: Rest time after set

        Returns:
            LogSet: New set instance
        """
        return LogSet(
            log_exercise_id=log_exercise_id,
            set_number=set_number,
            reps=reps,
            weight=weight,
            rpe=rpe,
            notes=notes,
            rest_time_seconds=rest_time_seconds
        )

    @staticmethod
    def create_batch(
        log_exercise_id: int,
        count: int = 3,
        base_weight: float = 100.0,
        base_reps: int = 10
    ) -> list[LogSet]:
        """
        Create multiple set instances for a logged exercise.

        Args:
            log_exercise_id: LogExercise ID
            count: Number of sets to create
            base_weight: Starting weight (remains constant by default)
            base_reps: Starting reps (remains constant by default)

        Returns:
            list[LogSet]: List of set instances
        """
        return [
            LogSet(
                log_exercise_id=log_exercise_id,
                set_number=i + 1,
                reps=base_reps,
                weight=base_weight
            )
            for i in range(count)
        ]
