from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("workout_sessions.id"), nullable=True)
    role: Mapped[str] = mapped_column(String(20))           # user | assistant | tool
    content: Mapped[str] = mapped_column(Text)              # text or JSON
    message_type: Mapped[str] = mapped_column(String(30), default="text")  # text | tool_use | tool_result
    tool_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tool_use_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
