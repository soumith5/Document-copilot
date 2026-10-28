from sqlalchemy import Column, ForeignKey, Integer

from app.database.session import Base


class MessageCitation(Base):
    __tablename__ = "message_citations"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=False)
    chunk_id = Column(Integer, ForeignKey("document_chunks.id"), nullable=False)
