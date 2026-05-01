from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.crud import conversation as conv_crud
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.claude_service import get_claude_response

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(data: ChatRequest, db: Session = Depends(get_db)):
    reply, tools_used, session_id = await get_claude_response(db, data.message, data.session_id)
    return ChatResponse(reply=reply, tool_calls_executed=tools_used, session_id=session_id)


@router.get("/history")
def chat_history(
    limit: int = Query(50, ge=1, le=200),
    before_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    messages = conv_crud.get_history(db, limit=limit, before_id=before_id)
    return {
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "message_type": m.message_type,
                "tool_name": m.tool_name,
                "created_at": m.created_at,
            }
            for m in reversed(messages)
        ]
    }


@router.delete("/history")
def clear_history(db: Session = Depends(get_db)):
    count = conv_crud.clear_history(db)
    return {"deleted_count": count}
