from sqlalchemy import Column, Integer, ForeignKey, Float, Text, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from models.base import Base
from models.exercise import Exercise # Importa Exercise para o ForeignKey

class WorkoutSession(Base):
    __tablename__ = 'workout_sessions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, default=1)
    date = Column(Date, default=datetime.utcnow().date())
    duration_minutes = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    exercises_done = relationship("LogExercise", back_populates="session")

class LogExercise(Base):
    __tablename__ = 'log_exercises'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('workout_sessions.id'))
    exercise_id = Column(Integer, ForeignKey('exercises.id')) 
    
    sets_completed = Column(Integer)
    top_weight = Column(Float)
    total_reps = Column(Integer)
    
    session = relationship("WorkoutSession", back_populates="exercises_done")
    exercise = relationship("Exercise")