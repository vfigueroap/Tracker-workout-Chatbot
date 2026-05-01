from datetime import datetime
from pydantic import BaseModel


class UserProfileOut(BaseModel):
    id: int
    name: str
    age: int | None
    weight_kg: float | None
    height_cm: float | None
    fitness_level: str
    primary_goal: str
    secondary_goals: str
    injuries_limitations: str | None
    preferred_workout_days: str | None
    session_duration_min: int
    equipment_available: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    weight_kg: float | None = None
    height_cm: float | None = None
    fitness_level: str | None = None
    primary_goal: str | None = None
    secondary_goals: str | None = None
    injuries_limitations: str | None = None
    preferred_workout_days: str | None = None
    session_duration_min: int | None = None
    equipment_available: str | None = None
