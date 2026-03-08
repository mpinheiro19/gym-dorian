"""User authentication and profile models using SQLAlchemy 2.0 syntax."""
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, _utcnow
import enum

if TYPE_CHECKING:
    from app.models.log import WorkoutSession
    from app.models.template import WorkoutTemplate
    from app.models.plan import WorkoutPlan


class User(Base):
    """Represents a user account in the system.

    This model handles user authentication and basic profile information.
    Password is stored as a bcrypt hash, never in plain text.

    Attributes:
        id: Primary key identifier
        email: Unique email address for login
        password_hash: Bcrypt hashed password
        full_name: User's full name
        is_active: Whether the user account is active
        is_superuser: Whether the user has admin privileges
        created_at: Timestamp when account was created
        updated_at: Timestamp when account was last updated
        last_login: Timestamp of last successful login
        settings: Relationship to UserSettings (one-to-one)
        goals: Relationship to UserGoals (one-to-many)
        workout_sessions: Relationship to WorkoutSession records
    """
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), default=None)

    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=None
    )

    # Relationships
    settings: Mapped[Optional["UserSettings"]] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    goals: Mapped[list["UserGoal"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    workout_sessions: Mapped[list["WorkoutSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    workout_templates: Mapped[list["WorkoutTemplate"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    workout_plans: Mapped[list["WorkoutPlan"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


class WeightUnit(str, enum.Enum):
    """Enumeration for weight units."""
    KILOGRAMS = "kg"
    POUNDS = "lbs"


class DistanceUnit(str, enum.Enum):
    """Enumeration for distance units."""
    KILOMETERS = "km"
    MILES = "miles"


class UserSettings(Base):
    """User preferences and settings.

    Stores user-specific configuration for the application,
    such as preferred units of measurement and privacy settings.

    Attributes:
        id: Primary key identifier
        user_id: Foreign key to User (one-to-one)
        weight_unit: Preferred unit for weight (kg or lbs)
        distance_unit: Preferred unit for distance (km or miles)
        default_rest_time: Default rest time between sets in seconds
        private_profile: Whether user profile is private
        email_notifications: Whether to send email notifications
        user: Relationship to User
    """
    __tablename__ = 'user_settings'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        unique=True,
        nullable=False
    )

    # Measurement preferences
    weight_unit: Mapped[WeightUnit] = mapped_column(
        SQLEnum(WeightUnit, native_enum=False, length=10),
        default=WeightUnit.KILOGRAMS,
        nullable=False
    )
    distance_unit: Mapped[DistanceUnit] = mapped_column(
        SQLEnum(DistanceUnit, native_enum=False, length=10),
        default=DistanceUnit.KILOMETERS,
        nullable=False
    )

    # Workout preferences
    default_rest_time: Mapped[int] = mapped_column(default=90, nullable=False)  # seconds

    # Privacy settings
    private_profile: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="settings")


class GoalType(str, enum.Enum):
    """Enumeration for different types of fitness goals."""
    STRENGTH = "strength"  # Increase max weight
    MUSCLE_GAIN = "muscle_gain"  # Build muscle mass
    WEIGHT_LOSS = "weight_loss"  # Lose body weight
    ENDURANCE = "endurance"  # Improve cardiovascular endurance
    CONSISTENCY = "consistency"  # Maintain workout routine
    CUSTOM = "custom"  # User-defined goal


class GoalStatus(str, enum.Enum):
    """Enumeration for goal completion status."""
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class UserGoal(Base):
    """User fitness goals and targets.

    Tracks user-defined fitness goals such as target weights,
    body composition, or workout frequency targets.

    Attributes:
        id: Primary key identifier
        user_id: Foreign key to User
        goal_type: Type of goal (strength, weight loss, etc.)
        title: Short description of the goal
        description: Detailed description
        target_value: Numeric target (e.g., target weight, body fat %)
        current_value: Current progress value
        target_date: Optional deadline for the goal
        status: Goal status (active, completed, abandoned)
        created_at: When the goal was created
        updated_at: When the goal was last updated
        completed_at: When the goal was completed
        user: Relationship to User
    """
    __tablename__ = 'user_goals'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Goal details
    goal_type: Mapped[GoalType] = mapped_column(
        SQLEnum(GoalType, native_enum=False, length=20),
        nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), default=None)

    # Progress tracking
    target_value: Mapped[Optional[float]] = mapped_column(default=None)
    current_value: Mapped[Optional[float]] = mapped_column(default=None)
    target_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=None
    )

    # Status
    status: Mapped[GoalStatus] = mapped_column(
        SQLEnum(GoalStatus, native_enum=False, length=20),
        default=GoalStatus.ACTIVE,
        nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=None
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="goals")
