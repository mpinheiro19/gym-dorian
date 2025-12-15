"""Workout logging routes for tracking exercises and sessions."""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.dependencies.auth import get_current_active_user
from app.models.user import User
from app.crud import workout as workout_crud
from app.schemas.workout_schema import (
    ExerciseResponse,
    ExerciseCreate,
    ExerciseUpdate,
    WorkoutSessionResponse,
    WorkoutSessionCreate,
    WorkoutSessionUpdate,
    WorkoutSessionSummary,
    LogExerciseCreate,
    LogExerciseUpdate,
    LogExerciseResponse,
    QuickWorkoutLog,
    WorkoutStats,
    CopyWorkoutRequest,
)

router = APIRouter(prefix="/workouts", tags=["Workouts"])


# ===========================
# Exercise Management
# ===========================

@router.get("/exercises", response_model=List[ExerciseResponse])
def list_exercises(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    muscle_group: Optional[str] = Query(None, description="Filter by muscle group"),
    search: Optional[str] = Query(None, description="Search by exercise name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of available exercises.

    Query parameters allow filtering by muscle group and searching by name.

    Args:
        skip: Number of records to skip
        limit: Maximum records to return
        muscle_group: Filter by muscle group
        search: Search term for exercise name
        db: Database session
        current_user: Authenticated user

    Returns:
        List[ExerciseResponse]: List of exercises
    """
    return workout_crud.get_exercises(db, skip, limit, muscle_group, search)


@router.get("/exercises/{exercise_id}", response_model=ExerciseResponse)
def get_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific exercise by ID.

    Args:
        exercise_id: Exercise ID
        db: Database session
        current_user: Authenticated user

    Returns:
        ExerciseResponse: Exercise details

    Raises:
        HTTPException 404: If exercise not found
    """
    exercise = workout_crud.get_exercise_by_id(db, exercise_id)
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )
    return exercise


@router.post("/exercises", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
def create_exercise(
    exercise_in: ExerciseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new exercise.

    Args:
        exercise_in: Exercise creation data
        db: Database session
        current_user: Authenticated user

    Returns:
        ExerciseResponse: Created exercise

    Raises:
        HTTPException 400: If exercise name already exists
    """
    # Check if exercise already exists
    existing = workout_crud.get_exercise_by_name(db, exercise_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exercise with this name already exists"
        )

    return workout_crud.create_exercise(db, exercise_in)


@router.put("/exercises/{exercise_id}", response_model=ExerciseResponse)
def update_exercise(
    exercise_id: int,
    exercise_in: ExerciseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update an exercise.

    Args:
        exercise_id: Exercise ID
        exercise_in: Exercise update data
        db: Database session
        current_user: Authenticated user

    Returns:
        ExerciseResponse: Updated exercise

    Raises:
        HTTPException 404: If exercise not found
        HTTPException 400: If new name already exists
    """
    exercise = workout_crud.get_exercise_by_id(db, exercise_id)
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )

    # Check name uniqueness if being updated
    if exercise_in.name and exercise_in.name != exercise.name:
        existing = workout_crud.get_exercise_by_name(db, exercise_in.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exercise with this name already exists"
            )

    return workout_crud.update_exercise(db, exercise, exercise_in)


@router.delete("/exercises/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete an exercise.

    Args:
        exercise_id: Exercise ID
        db: Database session
        current_user: Authenticated user

    Raises:
        HTTPException 404: If exercise not found
    """
    exercise = workout_crud.get_exercise_by_id(db, exercise_id)
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )

    workout_crud.delete_exercise(db, exercise)
    return None


# ===========================
# Workout Session Management
# ===========================

@router.get("/sessions", response_model=List[WorkoutSessionResponse])
def list_workout_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get workout sessions for the current user.

    Returns sessions ordered by date (most recent first).

    Args:
        skip: Number of records to skip
        limit: Maximum records to return
        start_date: Filter by start date
        end_date: Filter by end date
        db: Database session
        current_user: Authenticated user

    Returns:
        List[WorkoutSessionResponse]: List of workout sessions
    """
    return workout_crud.get_workout_sessions(
        db,
        current_user.id,
        skip,
        limit,
        start_date,
        end_date
    )


@router.get("/sessions/{workout_id}", response_model=WorkoutSessionResponse)
def get_workout_session(
    workout_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific workout session with all exercises.

    Args:
        workout_id: Workout session ID
        db: Database session
        current_user: Authenticated user

    Returns:
        WorkoutSessionResponse: Workout session details

    Raises:
        HTTPException 404: If workout not found
    """
    workout = workout_crud.get_workout_session_by_id(db, workout_id, current_user.id)
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout session not found"
        )
    return workout


@router.post("/sessions", response_model=WorkoutSessionResponse, status_code=status.HTTP_201_CREATED)
def create_workout_session(
    workout_in: WorkoutSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new workout session with exercises.

    Args:
        workout_in: Workout session data with exercises
        db: Database session
        current_user: Authenticated user

    Returns:
        WorkoutSessionResponse: Created workout session

    Raises:
        HTTPException 400: If invalid exercise ID provided
    """
    # Verify all exercise IDs exist
    for exercise_data in workout_in.exercises:
        exercise = workout_crud.get_exercise_by_id(db, exercise_data.exercise_id)
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Exercise with ID {exercise_data.exercise_id} not found"
            )

    return workout_crud.create_workout_session(db, current_user.id, workout_in)


@router.post("/sessions/quick", response_model=WorkoutSessionResponse, status_code=status.HTTP_201_CREATED)
def quick_log_workout(
    quick_log: QuickWorkoutLog,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Quick workout logging with automatic calculation of totals.

    Provide individual sets, and the system will calculate:
    - sets_completed (count of sets)
    - top_weight (max weight from all sets)
    - total_reps (sum of reps from all sets)

    Args:
        quick_log: Quick workout log data
        db: Database session
        current_user: Authenticated user

    Returns:
        WorkoutSessionResponse: Created workout session

    Raises:
        HTTPException 400: If invalid exercise ID provided
    """
    # Verify all exercise IDs exist
    for exercise_data in quick_log.exercises:
        exercise = workout_crud.get_exercise_by_id(db, exercise_data.exercise_id)
        if not exercise:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Exercise with ID {exercise_data.exercise_id} not found"
            )

    return workout_crud.create_quick_workout(db, current_user.id, quick_log)


@router.put("/sessions/{workout_id}", response_model=WorkoutSessionResponse)
def update_workout_session(
    workout_id: int,
    workout_in: WorkoutSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a workout session.

    Note: This updates session-level fields (date, duration, notes).
    To modify exercises, use the exercise-specific endpoints.

    Args:
        workout_id: Workout session ID
        workout_in: Workout session update data
        db: Database session
        current_user: Authenticated user

    Returns:
        WorkoutSessionResponse: Updated workout session

    Raises:
        HTTPException 404: If workout not found
    """
    workout = workout_crud.get_workout_session_by_id(db, workout_id, current_user.id)
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout session not found"
        )

    return workout_crud.update_workout_session(db, workout, workout_in)


@router.delete("/sessions/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout_session(
    workout_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a workout session.

    Cascades to delete all logged exercises in this session.

    Args:
        workout_id: Workout session ID
        db: Database session
        current_user: Authenticated user

    Raises:
        HTTPException 404: If workout not found
    """
    workout = workout_crud.get_workout_session_by_id(db, workout_id, current_user.id)
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout session not found"
        )

    workout_crud.delete_workout_session(db, workout)
    return None


@router.post("/sessions/copy", response_model=WorkoutSessionResponse, status_code=status.HTTP_201_CREATED)
def copy_workout_session(
    copy_request: CopyWorkoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Copy a previous workout to a new date.

    Useful for repeating routines.

    Args:
        copy_request: Copy workout request data
        db: Database session
        current_user: Authenticated user

    Returns:
        WorkoutSessionResponse: New copied workout session

    Raises:
        HTTPException 404: If source workout not found
    """
    source_workout = workout_crud.get_workout_session_by_id(
        db,
        copy_request.source_workout_id,
        current_user.id
    )

    if not source_workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source workout not found"
        )

    return workout_crud.copy_workout_session(
        db,
        source_workout,
        current_user.id,
        copy_request.new_date,
        copy_request.copy_notes
    )


# ===========================
# Exercise Logging Management
# ===========================

@router.post("/sessions/{workout_id}/exercises", response_model=LogExerciseResponse, status_code=status.HTTP_201_CREATED)
def add_exercise_to_workout(
    workout_id: int,
    exercise_in: LogExerciseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Add an exercise to an existing workout session.

    Args:
        workout_id: Workout session ID
        exercise_in: Exercise log data
        db: Database session
        current_user: Authenticated user

    Returns:
        LogExerciseResponse: Created exercise log

    Raises:
        HTTPException 404: If workout or exercise not found
    """
    # Verify workout exists and belongs to user
    workout = workout_crud.get_workout_session_by_id(db, workout_id, current_user.id)
    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout session not found"
        )

    # Verify exercise exists
    exercise = workout_crud.get_exercise_by_id(db, exercise_in.exercise_id)
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )

    return workout_crud.add_exercise_to_workout(db, workout_id, exercise_in)


@router.put("/exercises/logged/{log_exercise_id}", response_model=LogExerciseResponse)
def update_logged_exercise(
    log_exercise_id: int,
    exercise_in: LogExerciseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a logged exercise.

    Args:
        log_exercise_id: Log exercise ID
        exercise_in: Exercise log update data
        db: Database session
        current_user: Authenticated user

    Returns:
        LogExerciseResponse: Updated exercise log

    Raises:
        HTTPException 404: If logged exercise not found
    """
    log_exercise = workout_crud.get_logged_exercise_by_id(db, log_exercise_id, current_user.id)
    if not log_exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Logged exercise not found"
        )

    return workout_crud.update_logged_exercise(db, log_exercise, exercise_in)


@router.delete("/exercises/logged/{log_exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_logged_exercise(
    log_exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a logged exercise from a workout.

    Args:
        log_exercise_id: Log exercise ID
        db: Database session
        current_user: Authenticated user

    Raises:
        HTTPException 404: If logged exercise not found
    """
    log_exercise = workout_crud.get_logged_exercise_by_id(db, log_exercise_id, current_user.id)
    if not log_exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Logged exercise not found"
        )

    workout_crud.delete_logged_exercise(db, log_exercise)
    return None


# ===========================
# Statistics
# ===========================

@router.get("/stats", response_model=WorkoutStats)
def get_workout_statistics(
    start_date: Optional[date] = Query(None, description="Start date for stats"),
    end_date: Optional[date] = Query(None, description="End date for stats"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get workout statistics for the current user.

    Returns aggregate statistics such as total workouts, volume, etc.

    Args:
        start_date: Optional start date
        end_date: Optional end date
        db: Database session
        current_user: Authenticated user

    Returns:
        WorkoutStats: Workout statistics
    """
    stats = workout_crud.get_workout_stats(db, current_user.id, start_date, end_date)
    return WorkoutStats(**stats)
