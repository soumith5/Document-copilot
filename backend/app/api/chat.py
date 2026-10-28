from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.chat.messages import ChatStreamRequest, extract_last_user_text
from app.chat.orchestrator import stream_agent_response
from app.database.models.chat_message import ChatMessage
from app.database.models.chat_thread import ChatThread
from app.database.session import get_db

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/stream")
def chat_stream(
    body: ChatStreamRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    thread = (
        db.query(ChatThread)
        .filter(ChatThread.id == body.thread_id, ChatThread.user_id == user.id)
        .first()
    )
    if thread is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found"
        )

    user_text = extract_last_user_text(body.messages)
    db.add(ChatMessage(thread_id=thread.id, role="user", content=user_text))
    db.commit()

    return StreamingResponse(
        stream_agent_response(thread.id, user_text),
        media_type="text/plain",
    )