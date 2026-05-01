from datetime import datetime
from pydantic import BaseModel


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    message_type: str
    tool_name: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    session_id: int | None = None


class ChatResponse(BaseModel):
    reply: str
    tool_calls_executed: list[str] = []
    session_id: int | None = None
