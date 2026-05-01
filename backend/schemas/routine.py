from datetime import datetime
from pydantic import BaseModel


class RoutineExerciseOut(BaseModel):
    id: int
    exercise_id: int
    exercise_name: str = ""
    order_index: int
    target_sets: int
    target_reps_min: int | None
    target_reps_max: int | None
    target_weight_kg: float | None
    target_rpe: float | None
    rest_seconds: int
    notes: str | None

    class Config:
        from_attributes = True


class RoutineDayOut(BaseModel):
    id: int
    day_number: int
    name: str
    day_of_week: str | None
    exercises: list[RoutineExerciseOut] = []

    class Config:
        from_attributes = True


class RoutineOut(BaseModel):
    id: int
    name: str
    description: str | None
    goal: str
    frequency_per_week: int
    is_active: bool
    source: str
    created_at: datetime
    updated_at: datetime
    days: list[RoutineDayOut] = []

    class Config:
        from_attributes = True


class RoutineExerciseCreate(BaseModel):
    exercise_name: str
    order_index: int = 0
    target_sets: int = 3
    target_reps_min: int | None = None
    target_reps_max: int | None = None
    target_weight_kg: float | None = None
    target_rpe: float | None = None
    rest_seconds: int = 90
    notes: str | None = None


class RoutineDayCreate(BaseModel):
    day_number: int
    name: str
    day_of_week: str | None = None
    exercises: list[RoutineExerciseCreate] = []


class RoutineCreate(BaseModel):
    name: str
    description: str | None = None
    goal: str = "general fitness"
    frequency_per_week: int = 3
    source: str = "user_created"
    raw_upload: str | None = None
    days: list[RoutineDayCreate] = []


class RoutineUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    goal: str | None = None
    frequency_per_week: int | None = None
