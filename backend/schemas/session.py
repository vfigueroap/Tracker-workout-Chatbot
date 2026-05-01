from datetime import datetime
from pydantic import BaseModel


class ExerciseSetOut(BaseModel):
    id: int
    set_number: int
    reps: int | None
    weight_kg: float | None
    duration_seconds: int | None
    rpe: float | None
    is_warmup: bool
    logged_at: datetime

    class Config:
        from_attributes = True


class SessionExerciseOut(BaseModel):
    id: int
    exercise_id: int
    exercise_name: str = ""
    order_performed: int
    notes: str | None
    sets: list[ExerciseSetOut] = []

    class Config:
        from_attributes = True


class WorkoutSessionOut(BaseModel):
    id: int
    routine_id: int | None
    routine_day_id: int | None
    routine_day_name: str | None = None
    started_at: datetime
    ended_at: datetime | None
    status: str
    overall_feeling: int | None
    notes: str | None
    ai_summary: str | None
    total_volume_kg: float
    exercises: list[SessionExerciseOut] = []

    class Config:
        from_attributes = True


class SessionCreate(BaseModel):
    routine_id: int | None = None
    routine_day_id: int | None = None
    notes: str | None = None


class SessionUpdate(BaseModel):
    status: str | None = None
    overall_feeling: int | None = None
    notes: str | None = None
    ai_summary: str | None = None


class ExerciseSetCreate(BaseModel):
    set_number: int
    reps: int | None = None
    weight_kg: float | None = None
    duration_seconds: int | None = None
    rpe: float | None = None
    is_warmup: bool = False


class LogExerciseRequest(BaseModel):
    exercise_id: int | None = None
    exercise_name: str | None = None
    sets: list[ExerciseSetCreate]
    notes: str | None = None
