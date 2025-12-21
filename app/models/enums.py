"""Enums for the application."""
from enum import Enum


class MuscleGroup(str, Enum):
    """Valid muscle groups for exercises."""
    CHEST = "Chest"
    BACK = "Back"
    SHOULDERS = "Shoulders"
    BICEPS = "Biceps"
    TRICEPS = "Triceps"
    FOREARMS = "Forearms"
    QUADRICEPS = "Quadriceps"
    HAMSTRINGS = "Hamstrings"
    GLUTES = "Glutes"
    CALVES = "Calves"
    ABDOMINALS = "Abdominals"
    LOWER_BACK = "Lower Back"

    @classmethod
    def values(cls):
        """Return list of all muscle group values."""
        return [member.value for member in cls]
