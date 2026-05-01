from sqlalchemy.orm import Session

from backend.models.conversation import ConversationMessage


def add_message(db: Session, role: str, content: str, session_id: int | None = None,
                message_type: str = "text", tool_name: str | None = None,
                tool_use_id: str | None = None) -> ConversationMessage:
    msg = ConversationMessage(
        role=role,
        content=content,
        session_id=session_id,
        message_type=message_type,
        tool_name=tool_name,
        tool_use_id=tool_use_id,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_history(db: Session, limit: int = 40, before_id: int | None = None) -> list[ConversationMessage]:
    q = db.query(ConversationMessage)
    if before_id:
        q = q.filter(ConversationMessage.id < before_id)
    return q.order_by(ConversationMessage.created_at.desc()).limit(limit).all()


def get_recent_messages(db: Session, limit: int = 30) -> list[ConversationMessage]:
    msgs = (
        db.query(ConversationMessage)
        .order_by(ConversationMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(msgs))


def clear_history(db: Session) -> int:
    count = db.query(ConversationMessage).count()
    db.query(ConversationMessage).delete()
    db.commit()
    return count
