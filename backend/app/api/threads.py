from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.models.chat_message import ChatMessage
from app.database.models.chat_thread import ChatThread
from app.database.models.document_chunk import DocumentChunk
from app.database.models.message_citation import MessageCitation
from app.database.models.source_document import SourceDocument
from app.database.session import get_db

router = APIRouter(prefix="/threads", tags=["threads"])


class ThreadCreate(BaseModel):
    title: str | None = None


class ThreadUpdate(BaseModel):
    title: str


class ThreadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str | None
    created_at: datetime


class CitationOut(BaseModel):
    chunk_id: int
    ticker: str | None
    company: str | None
    filing_type: str | None
    filing_date: str | None
    item: str | None
    item_title: str | None
    page_start: int | None
    page_end: int | None
    excerpt: str


class MessageOut(BaseModel):
    id: int
    thread_id: int
    role: str
    content: str
    created_at: datetime
    citations: list[CitationOut] = []


EXCERPT_LENGTH = 300


def _citations_for_message(db: Session, message_id: int) -> list[CitationOut]:
    """Joins message_citations -> document_chunks -> source_documents to
    build display data for citation footnotes. Ordered by MessageCitation.id
    (insertion order) so this matches the order the agent originally
    listed citations in — the frontend maps inline [1][2] markers to this
    same order, deduplicated by chunk_id.
    """
    rows = (
        db.query(MessageCitation, DocumentChunk, SourceDocument)
        .join(DocumentChunk, MessageCitation.chunk_id == DocumentChunk.id)
        .join(SourceDocument, DocumentChunk.document_id == SourceDocument.id)
        .filter(MessageCitation.message_id == message_id)
        .order_by(MessageCitation.id.asc())
        .all()
    )

    citations = []
    for _, chunk, document in rows:
        doc_meta = document.doc_metadata or {}
        chunk_meta = chunk.chunk_metadata or {}
        citations.append(
            CitationOut(
                chunk_id=chunk.id,
                ticker=doc_meta.get("ticker"),
                company=doc_meta.get("company"),
                filing_type=doc_meta.get("filing_type"),
                filing_date=doc_meta.get("filing_date"),
                item=chunk_meta.get("item"),
                item_title=chunk_meta.get("item_title"),
                page_start=chunk_meta.get("page_start"),
                page_end=chunk_meta.get("page_end"),
                excerpt=chunk.content[:EXCERPT_LENGTH],
            )
        )
    return citations


def _get_owned_thread(db: Session, thread_id: int, user_id: str) -> ChatThread:
    thread = (
        db.query(ChatThread)
        .filter(ChatThread.id == thread_id, ChatThread.user_id == user_id)
        .first()
    )
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    return thread


@router.post("", response_model=ThreadOut, status_code=status.HTTP_201_CREATED)
def create_thread(
    body: ThreadCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    thread = ChatThread(user_id=user.id, title=body.title)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    return thread


@router.get("", response_model=list[ThreadOut])
def list_threads(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(ChatThread)
        .filter(ChatThread.user_id == user.id)
        .order_by(ChatThread.created_at.desc())
        .all()
    )


@router.patch("/{thread_id}", response_model=ThreadOut)
def rename_thread(
    thread_id: int,
    body: ThreadUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    thread = _get_owned_thread(db, thread_id, user.id)
    thread.title = body.title
    db.commit()
    db.refresh(thread)
    return thread


@router.delete("/{thread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_thread(
    thread_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    thread = _get_owned_thread(db, thread_id, user.id)

    message_ids = [
        row.id for row in db.query(ChatMessage.id).filter(ChatMessage.thread_id == thread_id)
    ]
    if message_ids:
        db.query(MessageCitation).filter(MessageCitation.message_id.in_(message_ids)).delete(
            synchronize_session=False
        )
        db.query(ChatMessage).filter(ChatMessage.thread_id == thread_id).delete(
            synchronize_session=False
        )
    db.delete(thread)
    db.commit()


@router.get("/{thread_id}/messages", response_model=list[MessageOut])
def get_thread_messages(
    thread_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    thread = _get_owned_thread(db, thread_id, user.id)

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.thread_id == thread_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    result = []
    for message in messages:
        citations = (
            _citations_for_message(db, message.id) if message.role == "assistant" else []
        )
        result.append(
            MessageOut(
                id=message.id,
                thread_id=message.thread_id,
                role=message.role,
                content=message.content,
                created_at=message.created_at,
                citations=citations,
            )
        )
    return result