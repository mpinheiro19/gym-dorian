"""CRUD operations for workout logging."""
from typing import Optional, List
from datetime import date, datetime
from sqlalchemy import func, and_
from sqlalchemy.orm import Session, joinedload

from app.models.log import WorkoutSession, LogExercise
from app.models.exercise import Exercise
from app.schemas.workout_schema import (
    WorkoutSessionCreate,
    WorkoutSessionUpdate,
    LogExerciseCreate,
    LogExerciseUpdate,
    ExerciseCreate,
    ExerciseUpdate,
    QuickWorkoutLog,
)


# ===========================
# Exercise CRUD
# ===========================

def get_exercises(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    muscle_group: Optional[str] = None,
    search: Optional[str] = None
) -> List[Exercise]:
    """
    Get list of exercises with optional filtering.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum records to return
        muscle_group: Filter by muscle group
        search: Search by name

    Returns:
        List[Exercise]: List of exercises
    """
    query = db.query(Exercise)

    if muscle_group:
        query = query.filter(Exercise.muscle_group == muscle_group)

    if search:
        query = query.filter(Exercise.name.ilike(f"%{search}%"))

    return query.offset(skip).limit(limit).all()


def get_exercise_by_id(db: Session, exercise_id: int) -> Optional[Exercise]:
    """Get exercise by ID."""
    return db.query(Exercise).filter(Exercise.id == exercise_id).first()


def get_exercise_by_name(db: Session, name: str) -> Optional[Exercise]:
    """Get exercise by name."""
    return db.query(Exercise).filter(Exercise.name == name).first()


def create_exercise(db: Session, exercise_in: ExerciseCreate) -> Exercise:
    """
    Create a new exercise.

    Args:
        db: Database session
        exercise_in: Exercise creation data

    Returns:
        Exercise: Created exercise
    """
    exercise = Exercise(**exercise_in.model_dump())
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise


def update_exercise(
    db: Session,
    exercise: Exercise,
    exercise_in: ExerciseUpdate
) -> Exercise:
    """
    Update an exercise.

    Args:
        db: Database session
        exercise: Existing exercise
        exercise_in: Exercise update data

    Returns:
        Exercise: Updated exercise
    """
    update_data = exercise_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(exercise, field, value)

    db.commit()
    db.refresh(exercise)
    return exercise


def delete_exercise(db: Session, exercise: Exercise) -> None:
    """
    Delete an exercise.

    Args:
        db: Database session
        exercise: Exercise to delete
    """
    db.delete(exercise)
    db.commit()


# ===========================
# Workout Session CRUD
# ===========================

def get_workout_sessions(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[WorkoutSession]:
    """
    Get workout sessions for a user with optional date filtering.

    Args:
        db: Database session
        user_id: User ID
        skip: Number of records to skip
        limit: Maximum records to return
        start_date: Filter by start date
        end_date: Filter by end date

    Returns:
        List[WorkoutSession]: List of workout sessions
    """
    query = db.query(WorkoutSession).filter(WorkoutSession.user_id == user_id)

    if start_date:
        query = query.filter(WorkoutSession.workout_date >= start_date)

    if end_date:
        query = query.filter(WorkoutSession.workout_date <= end_date)

    return query.order_by(WorkoutSession.workout_date.desc()).offset(skip).limit(limit).all()


def get_workout_session_by_id(
    db: Session,
    workout_id: int,
    user_id: int
) -> Optional[WorkoutSession]:
    """
    Get a specific workout session by ID for a user.

    Args:
        db: Database session
        workout_id: Workout session ID
        user_id: User ID (for ownership verification)

    Returns:
        Optional[WorkoutSession]: Workout session or None
    """
    return db.query(WorkoutSession).options(
        joinedload(WorkoutSession.exercises_done).joinedload(LogExercise.exercise)
    ).filter(
        WorkoutSession.id == workout_id,
        WorkoutSession.user_id == user_id
    ).first()


def create_workout_session(
    db: Session,
    user_id: int,
    workout_in: WorkoutSessionCreate
) -> WorkoutSession:
    """
    Create a new workout session with exercises.

    Args:
        db: Database session
        user_id: User ID
        workout_in: Workout session creation data

    Returns:
        WorkoutSession: Created workout session
    """
    # Create workout session
    workout = WorkoutSession(
        user_id=user_id,
        workout_date=workout_in.workout_date,
        duration_minutes=workout_in.duration_minutes,
        notes=workout_in.notes
    )
    db.add(workout)
    db.flush()  # Flush to get workout.id

    # Add exercises
    for exercise_data in workout_in.exercises:
        log_exercise = LogExercise(
            session_id=workout.id,
            exercise_id=exercise_data.exercise_id,
            sets_completed=exercise_data.sets_completed,
            top_weight=exercise_data.top_weight,
            total_reps=exercise_data.total_reps
        )
        db.add(log_exercise)

    db.commit()
    db.refresh(workout)
    return workout


def create_quick_workout(
    db: Session,
    user_id: int,
    quick_log: QuickWorkoutLog
) -> WorkoutSession:
    """
    Quick workout logging from sets data.

    Automatically calculates sets_completed, top_weight, and total_reps from sets.

    Args:
        db: Database session
        user_id: User ID
        quick_log: Quick workout log data

    Returns:
        WorkoutSession: Created workout session
    """
    # Create workout session
    workout = WorkoutSession(
        user_id=user_id,
        workout_date=quick_log.workout_date,
        duration_minutes=quick_log.duration_minutes,
        notes=quick_log.notes
    )
    db.add(workout)
    db.flush()

    # Process each exercise
    for exercise_data in quick_log.exercises:
        # Calculate aggregates from sets
        sets_count = len(exercise_data.sets)
        top_weight = max(s.weight for s in exercise_data.sets)
        total_reps = sum(s.reps for s in exercise_data.sets)

        log_exercise = LogExercise(
            session_id=workout.id,
            exercise_id=exercise_data.exercise_id,
            sets_completed=sets_count,
            top_weight=top_weight,
            total_reps=total_reps
        )
        db.add(log_exercise)

    db.commit()
    db.refresh(workout)
    return workout


def update_workout_session(
    db: Session,
    workout: WorkoutSession,
    workout_in: WorkoutSessionUpdate
) -> WorkoutSession:
    """
    Update a workout session.

    Args:
        db: Database session
        workout: Existing workout session
        workout_in: Workout session update data

    Returns:
        WorkoutSession: Updated workout session
    """
    update_data = workout_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(workout, field, value)

    db.commit()
    db.refresh(workout)
    return workout


def delete_workout_session(db: Session, workout: WorkoutSession) -> None:
    """
    Delete a workout session (cascades to log exercises).

    Args:
        db: Database session
        workout: Workout session to delete
    """
    db.delete(workout)
    db.commit()


def copy_workout_session(
    db: Session,
    source_workout: WorkoutSession,
    user_id: int,
    new_date: date,
    copy_notes: bool = False
) -> WorkoutSession:
    """
    Copy a previous workout session to a new date.

    Args:
        db: Database session
        source_workout: Source workout to copy
        user_id: User ID
        new_date: New workout date
        copy_notes: Whether to copy notes

    Returns:
        WorkoutSession: New copied workout session
    """
    # Create new workout session
    new_workout = WorkoutSession(
        user_id=user_id,
        workout_date=new_date,
        duration_minutes=source_workout.duration_minutes,
        notes=source_workout.notes if copy_notes else None
    )
    db.add(new_workout)
    db.flush()

    # Copy exercises
    for log_exercise in source_workout.exercises_done:
        new_log = LogExercise(
            session_id=new_workout.id,
            exercise_id=log_exercise.exercise_id,
            sets_completed=log_exercise.sets_completed,
            top_weight=log_exercise.top_weight,
            total_reps=log_exercise.total_reps
        )
        db.add(new_log)

    db.commit()
    db.refresh(new_workout)
    return new_workout


# ===========================
# Log Exercise CRUD
# ===========================

def add_exercise_to_workout(
    db: Session,
    workout_id: int,
    exercise_in: LogExerciseCreate
) -> LogExercise:
    """
    Add an exercise to an existing workout session.

    Args:
        db: Database session
        workout_id: Workout session ID
        exercise_in: Exercise log data

    Returns:
        LogExercise: Created exercise log
    """
    log_exercise = LogExercise(
        session_id=workout_id,
        **exercise_in.model_dump()
    )
    db.add(log_exercise)
    db.commit()
    db.refresh(log_exercise)
    return log_exercise


def update_logged_exercise(
    db: Session,
    log_exercise: LogExercise,
    exercise_in: LogExerciseUpdate
) -> LogExercise:
    """
    Update a logged exercise.

    Args:
        db: Database session
        log_exercise: Existing log exercise
        exercise_in: Exercise log update data

    Returns:
        LogExercise: Updated exercise log
    """
    update_data = exercise_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(log_exercise, field, value)

    db.commit()
    db.refresh(log_exercise)
    return log_exercise


def delete_logged_exercise(db: Session, log_exercise: LogExercise) -> None:
    """
    Delete a logged exercise from a workout.

    Args:
        db: Database session
        log_exercise: Exercise log to delete
    """
    db.delete(log_exercise)
    db.commit()


def get_logged_exercise_by_id(
    db: Session,
    log_exercise_id: int,
    user_id: int
) -> Optional[LogExercise]:
    """
    Get a logged exercise by ID (with ownership verification).

    Args:
        db: Database session
        log_exercise_id: Log exercise ID
        user_id: User ID (for ownership verification)

    Returns:
        Optional[LogExercise]: Logged exercise or None
    """
    return db.query(LogExercise).join(WorkoutSession).filter(
        LogExercise.id == log_exercise_id,
        WorkoutSession.user_id == user_id
    ).first()


# ===========================
# Statistics & Helpers
# ===========================

def get_workout_stats(
    db: Session,
    user_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> dict:
    """
    Get workout statistics for a user in a date range.

    Args:
        db: Database session
        user_id: User ID
        start_date: Optional start date
        end_date: Optional end date

    Returns:
        dict: Workout statistics
    """
    query = db.query(WorkoutSession).filter(WorkoutSession.user_id == user_id)

    if start_date:
        query = query.filter(WorkoutSession.workout_date >= start_date)
    if end_date:
        query = query.filter(WorkoutSession.workout_date <= end_date)

    workouts = query.all()

    total_workouts = len(workouts)
    total_duration = sum(w.duration_minutes or 0 for w in workouts)
    total_exercises = sum(len(w.exercises_done) for w in workouts)

    # Calculate total volume
    total_volume = db.query(
        func.sum(LogExercise.total_reps * LogExercise.top_weight)
    ).join(WorkoutSession).filter(
        WorkoutSession.user_id == user_id
    )

    if start_date:
        total_volume = total_volume.filter(WorkoutSession.workout_date >= start_date)
    if end_date:
        total_volume = total_volume.filter(WorkoutSession.workout_date <= end_date)

    total_volume = total_volume.scalar() or 0.0

    # Count unique exercises
    unique_exercises = db.query(
        func.count(func.distinct(LogExercise.exercise_id))
    ).join(WorkoutSession).filter(
        WorkoutSession.user_id == user_id
    )

    if start_date:
        unique_exercises = unique_exercises.filter(WorkoutSession.workout_date >= start_date)
    if end_date:
        unique_exercises = unique_exercises.filter(WorkoutSession.workout_date <= end_date)

    unique_exercises = unique_exercises.scalar() or 0

    return {
        "total_workouts": total_workouts,
        "total_duration_minutes": total_duration,
        "total_exercises_logged": total_exercises,
        "total_volume": float(total_volume),
        "unique_exercises": unique_exercises,
        "avg_workout_duration": total_duration / total_workouts if total_workouts > 0 else 0.0
    }
