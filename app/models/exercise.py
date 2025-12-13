"""Exercise model using SQLAlchemy 2.0 syntax."""
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Exercise(Base):
    """Represents an exercise in the gym tracking system.
    
    Attributes:
        id: Primary key identifier
        name: Unique exercise name (e.g., 'Bench Press')
        muscle_group: Target muscle group (e.g., 'Chest', 'Legs')
        equipment_type: Required equipment (e.g., 'Barbell', 'Dumbbell')
    """
    __tablename__ = 'exercises'
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)
    muscle_group: Mapped[Optional[str]] = mapped_column(default=None)
    equipment_type: Mapped[Optional[str]] = mapped_column(default=None)