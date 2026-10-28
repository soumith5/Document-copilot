from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.session import Base


class UserNote(Base):
    __tablename__ = "user_notes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=False), nullable=False, index=True)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False, server_default="")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())