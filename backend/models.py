from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from database import Base

class Exercise(Base):
    __tablename__ = "exercises"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    muscle_group = Column(String) # "Chest", "Back", etc.
    equipment = Column(String)
    difficulty = Column(String)
    description = Column(String)
    technique = Column(String)
    tips = Column(String)
    image_url = Column(String)
    muscle_map_url = Column(String)
    muscle_highlights = Column(String) # For specific muscle highlighting data

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    clerk_id = Column(String, unique=True, index=True, nullable=True)
    username = Column(String, unique=True, index=True)
    weight_kg = Column(Float)
    height_cm = Column(Float)
    unit_preference = Column(String, default="kg") # kg, lbs
    measure_unit = Column(String, default="cm") # cm, inch
    theme = Column(String, default="dark") # dark, light, premium


class Routine(Base):
    __tablename__ = "routines"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    exercises = relationship("RoutineExercise", back_populates="routine")

class RoutineExercise(Base):
    __tablename__ = "routine_exercises"
    id = Column(Integer, primary_key=True, index=True)
    routine_id = Column(Integer, ForeignKey("routines.id"))
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    order_index = Column(Integer)
    template_data = Column(String) # JSON
    routine = relationship("Routine", back_populates="exercises")
    exercise = relationship("Exercise")

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    routine_id = Column(Integer, ForeignKey("routines.id"), nullable=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    total_volume = Column(Float)
    calories_burned = Column(Float)

class Set(Base):
    __tablename__ = "sets"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    reps = Column(Integer)
    weight = Column(Float)
    is_failure = Column(Boolean, default=False)
    exercise = relationship("Exercise")
    avg_rms = Column(Float)
    mnf_drop_pct = Column(Float)
    set_duration_sec = Column(Float)
