"""CRUD operations for workout templates."""
from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session, joinedload

from app.models.template import WorkoutTemplate, TemplateExercise
from app.schemas.workout_schema import (
    WorkoutTemplateCreate,
    WorkoutTemplateUpdate,
)


def get_user_templates(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[WorkoutTemplate]:
    """
    Get list of templates for a user.

    Args:
        db: Database session
        user_id: User ID to filter templates
        skip: Number of records to skip
        limit: Maximum records to return

    Returns:
        List[WorkoutTemplate]: List of templates ordered by creation date
    """
    return db.query(WorkoutTemplate).filter(
        WorkoutTemplate.user_id == user_id
    ).order_by(
        WorkoutTemplate.created_at.desc()
    ).offset(skip).limit(limit).all()


def get_template_by_id(
    db: Session,
    template_id: int,
    user_id: int
) -> Optional[WorkoutTemplate]:
    """
    Get template by ID with ownership verification.

    Uses eager loading to fetch exercises and exercise details
    in a single query to avoid N+1 problem.

    Args:
        db: Database session
        template_id: Template ID
        user_id: User ID for ownership verification

    Returns:
        Optional[WorkoutTemplate]: Template if found and owned by user, None otherwise
    """
    return db.query(WorkoutTemplate).options(
        joinedload(WorkoutTemplate.exercises).joinedload(TemplateExercise.exercise)
    ).filter(
        WorkoutTemplate.id == template_id,
        WorkoutTemplate.user_id == user_id
    ).first()


def create_template(
    db: Session,
    user_id: int,
    template_in: WorkoutTemplateCreate
) -> WorkoutTemplate:
    """
    Create a new workout template with exercises.

    Args:
        db: Database session
        user_id: User ID who owns the template
        template_in: Template creation data

    Returns:
        WorkoutTemplate: Created template with exercises
    """
    # 1. Create template
    template = WorkoutTemplate(
        user_id=user_id,
        name=template_in.name,
        description=template_in.description
    )
    db.add(template)
    db.flush()  # Get template.id

    # 2. Add exercises to template
    for exercise_data in template_in.exercises:
        template_exercise = TemplateExercise(
            template_id=template.id,
            **exercise_data.model_dump()
        )
        db.add(template_exercise)

    db.commit()
    db.refresh(template)
    return template


def update_template(
    db: Session,
    template: WorkoutTemplate,
    template_in: WorkoutTemplateUpdate
) -> WorkoutTemplate:
    """
    Update an existing template.

    If exercises are provided, replaces all existing exercises.
    Otherwise, only updates template fields.

    Args:
        db: Database session
        template: Existing template to update
        template_in: Update data

    Returns:
        WorkoutTemplate: Updated template
    """
    # Update template fields
    update_data = template_in.model_dump(exclude_unset=True, exclude={'exercises'})
    for field, value in update_data.items():
        setattr(template, field, value)

    # If exercises provided, replace all
    if template_in.exercises is not None:
        # Delete existing exercises
        db.query(TemplateExercise).filter(
            TemplateExercise.template_id == template.id
        ).delete()

        # Create new exercises
        for exercise_data in template_in.exercises:
            template_exercise = TemplateExercise(
                template_id=template.id,
                **exercise_data.model_dump()
            )
            db.add(template_exercise)

    db.commit()
    db.refresh(template)
    return template


def delete_template(db: Session, template: WorkoutTemplate) -> None:
    """
    Delete a template.

    Cascade delete will remove all associated template exercises.

    Args:
        db: Database session
        template: Template to delete
    """
    db.delete(template)
    db.commit()


def prepare_workout_from_template(
    db: Session,
    template: WorkoutTemplate,
    workout_date: date
) -> dict:
    """
    Prepare workout structure from template for frontend.

    This does NOT create a workout session - it only returns
    formatted data for the frontend to populate and submit.

    Args:
        db: Database session
        template: Template to prepare from
        workout_date: Date for the workout

    Returns:
        dict: Prepared workout structure with exercises and metadata
    """
    return {
        "template_id": template.id,
        "template_name": template.name,
        "workout_date": workout_date.isoformat(),
        "exercises": [
            {
                "exercise_id": te.exercise_id,
                "exercise": {
                    "id": te.exercise.id,
                    "name": te.exercise.name,
                    "agonist_muscle_group": te.exercise.agonist_muscle_group,
                    "synergist_muscle_group": te.exercise.synergist_muscle_group,
                    "equipment_type": te.exercise.equipment_type,
                },
                "order_index": te.order_index,
                "target_sets": te.target_sets or 3,
                "notes": te.notes
            }
            for te in sorted(template.exercises, key=lambda x: x.order_index)
        ]
    }
