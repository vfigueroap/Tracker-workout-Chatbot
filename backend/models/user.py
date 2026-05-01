from datetime import datetime
from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), default="Athlete")
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    fitness_level: Mapped[str] = mapped_column(String(20), default="intermediate")
    primary_goal: Mapped[str] = mapped_column(String(100), default="general fitness")
    secondary_goals: Mapped[str] = mapped_column(Text, default="[]")  # JSON array
    injuries_limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_workout_days: Mapped[str | None] = mapped_column(String(50), nullable=True)
    session_duration_min: Mapped[int] = mapped_column(Integer, default=60)
    equipment_available: Mapped[str] = mapped_column(Text, default='["barbell","dumbbell","cable"]')  # JSON array
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
