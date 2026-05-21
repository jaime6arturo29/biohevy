from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Ejercicios
class Exercise(BaseModel):
    id: int
    name: str
    muscle_group: str
    equipment: str
    difficulty: str
    description: Optional[str] = None
    technique: Optional[str] = None
    tips: Optional[str] = None
    image_url: Optional[str] = None
    muscle_map_url: Optional[str] = None
    muscle_highlights: Optional[str] = None

    class Config:
        from_attributes = True

# Rutinas
class RoutineExerciseCreate(BaseModel):
    exercise_id: int
    order_index: int
    template_data: Optional[str] = None # JSON string de series sugeridas

class RoutineCreate(BaseModel):
    name: str
    user_id: int
    exercises: List[RoutineExerciseCreate]

class RoutineUpdate(BaseModel):
    name: Optional[str] = None
    exercises: Optional[List[RoutineExerciseCreate]] = None

class Routine(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

# Sesiones y Series
class SetCreate(BaseModel):
    exercise_id: int
    reps: int
    weight: float
    rpe: Optional[int] = None
    is_failure: bool = False

class SessionCreate(BaseModel):
    user_id: int
    routine_id: Optional[int] = None
    start_time: datetime

class SessionEnd(BaseModel):
    end_time: datetime
    sets: List[SetCreate]

# Usuario
class UserBase(BaseModel):
    username: str
    weight_kg: float
    height_cm: float
    unit_preference: str = "kg"
    measure_unit: str = "cm"
    theme: str = "dark"

class User(UserBase):
    id: int
    class Config:
        from_attributes = True
