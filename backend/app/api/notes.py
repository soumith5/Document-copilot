from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.models.user_note import UserNote
from app.database.session import get_db

router = APIRouter(prefix="/notes", tags=["notes"])


class NoteCreate(BaseModel):
    title: str | None = None


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str | None
    content: str
    created_at: datetime
    updated_at: datetime


def _get_owned_note(db: Session, note_id: int, user_id: str) -> UserNote:
    note = db.query(UserNote).filter(UserNote.id == note_id, UserNote.user_id == user_id).first()
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


@router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(
    body: NoteCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = UserNote(user_id=user.id, title=body.title, content="")
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get("", response_model=list[NoteOut])
def list_notes(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(UserNote)
        .filter(UserNote.user_id == user.id)
        .order_by(UserNote.updated_at.desc())
        .all()
    )


@router.patch("/{note_id}", response_model=NoteOut)
def update_note(
    note_id: int,
    body: NoteUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = _get_owned_note(db, note_id, user.id)
    if body.title is not None:
        note.title = body.title
    if body.content is not None:
        note.content = body.content
    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    note = _get_owned_note(db, note_id, user.id)
    db.delete(note)
    db.commit()