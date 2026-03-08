"""Script to populate exercises from workout-example.json"""
import json
from app.database import SessionLocal
from app.models.exercise import Exercise
from app.models.enums import MuscleGroup

# Mapping of exercise names to muscle groups
EXERCISE_MUSCLE_MAPPING = {
    # Push exercises (Chest, Shoulders, Triceps)
    "Seated Bench Press Machine": (MuscleGroup.CHEST, MuscleGroup.TRICEPS),
    "Shoulder Press Machine": (MuscleGroup.SHOULDERS, MuscleGroup.TRICEPS),
    "Chest Fly Machine": (MuscleGroup.CHEST, None),
    "Dumbbell Lateral Raise": (MuscleGroup.SHOULDERS, None),
    "Triceps Press Machine": (MuscleGroup.TRICEPS, None),
    "Triceps Cables": (MuscleGroup.TRICEPS, None),

    # Legs exercises
    "Machine Squats": (MuscleGroup.QUADRICEPS, MuscleGroup.GLUTES),
    "Legs Extension": (MuscleGroup.QUADRICEPS, None),
    "Seated Leg Curl": (MuscleGroup.HAMSTRINGS, None),
    "Good Mornings": (MuscleGroup.HAMSTRINGS, MuscleGroup.LOWER_BACK),
    "Calf Raise": (MuscleGroup.CALVES, None),
    "Dumbbell RDLs": (MuscleGroup.HAMSTRINGS, MuscleGroup.GLUTES),
    "Abdominal Machine Crunch": (MuscleGroup.ABDOMINALS, None),

    # Pull exercises (Back, Biceps)
    "Vertical Pull pronated grip": (MuscleGroup.BACK, MuscleGroup.BICEPS),
    "Seated Rows neutral grip": (MuscleGroup.BACK, MuscleGroup.BICEPS),
    "Seated Rows pronated grip": (MuscleGroup.BACK, MuscleGroup.BICEPS),
    "Reverse Crucifix machine": (MuscleGroup.BACK, MuscleGroup.SHOULDERS),
    "Biceps Curl Machine": (MuscleGroup.BICEPS, None),
    "Dumbbell Hammer Curl": (MuscleGroup.BICEPS, MuscleGroup.FOREARMS),
    "Pullup triangle": (MuscleGroup.BACK, MuscleGroup.BICEPS),

    # Rest
    "Descanso Ativo": (None, None),
}

# Equipment type mapping
EXERCISE_EQUIPMENT = {
    "Machine": ["Machine Squats", "Seated Bench Press Machine", "Shoulder Press Machine",
                "Chest Fly Machine", "Triceps Press Machine", "Legs Extension",
                "Seated Leg Curl", "Reverse Crucifix machine", "Biceps Curl Machine",
                "Abdominal Machine Crunch"],
    "Dumbbell": ["Dumbbell Lateral Raise", "Dumbbell RDLs", "Dumbbell Hammer Curl"],
    "Cable": ["Triceps Cables"],
    "Bodyweight": ["Good Mornings", "Pullup triangle", "Descanso Ativo"],
    "Other": ["Calf Raise"],
}

def get_equipment_type(exercise_name):
    """Determine equipment type based on exercise name"""
    for equipment, exercises in EXERCISE_EQUIPMENT.items():
        if exercise_name in exercises:
            return equipment
    return "Other"

def populate_exercises():
    """Populate exercises from workout-example.json"""
    db = SessionLocal()

    try:
        # Load workout example
        with open('workout-example.json', 'r') as f:
            workout_data = json.load(f)

        # Extract unique exercises
        unique_exercises = set()
        for day in workout_data.get('days', []):
            for exercise_data in day.get('exercises', []):
                exercise_name = exercise_data.get('exercise')
                if exercise_name:
                    unique_exercises.add(exercise_name)

        print(f"Found {len(unique_exercises)} unique exercises")

        # Create exercises
        created_count = 0
        skipped_count = 0

        for exercise_name in sorted(unique_exercises):
            # Check if exercise already exists
            existing = db.query(Exercise).filter(Exercise.name == exercise_name).first()

            if existing:
                print(f"⏭️  Skipped: {exercise_name} (already exists)")
                skipped_count += 1
                continue

            # Get muscle groups
            agonist, synergist = EXERCISE_MUSCLE_MAPPING.get(
                exercise_name,
                (None, None)
            )

            # Get equipment type
            equipment = get_equipment_type(exercise_name)

            # Create exercise
            exercise = Exercise(
                name=exercise_name,
                agonist_muscle_group=agonist.value if agonist else None,
                synergist_muscle_group=synergist.value if synergist else None,
                equipment_type=equipment
            )

            db.add(exercise)
            created_count += 1

            print(f"✅ Created: {exercise_name}")
            print(f"   - Agonist: {agonist.value if agonist else 'None'}")
            print(f"   - Synergist: {synergist.value if synergist else 'None'}")
            print(f"   - Equipment: {equipment}")

        db.commit()

        print(f"\n✨ Summary:")
        print(f"   Created: {created_count}")
        print(f"   Skipped: {skipped_count}")
        print(f"   Total in DB: {db.query(Exercise).count()}")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_exercises()
