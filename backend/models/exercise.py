from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class ExerciseDefinition(Base):
    __tablename__ = "exercise_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(50), default="strength")
    muscle_groups_primary: Mapped[str] = mapped_column(Text, default="[]")   # JSON array
    muscle_groups_secondary: Mapped[str] = mapped_column(Text, default="[]") # JSON array
    equipment: Mapped[str] = mapped_column(String(50), default="barbell")
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
