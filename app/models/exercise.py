from sqlalchemy import Column, Integer, String
from models.base import Base

class Exercise(Base):
    __tablename__ = 'exercises'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) 
    muscle_group = Column(String, nullable=True) 
    equipment_type = Column(String, nullable=True)