from sqlalchemy import Column, DateTime, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database.session import Base


class SourceDocument(Base):
    __tablename__ = "source_documents"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    source_url = Column(String)
    # Renamed from `metadata` -> collides with SQLAlchemy's reserved
    # Base.metadata attribute and raises InvalidRequestError at import time.
    # jsonb (not json) so it can be GIN-indexed.
    doc_metadata = Column(JSONB)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index(
            "ix_source_documents_doc_metadata_gin",
            "doc_metadata",
            postgresql_using="gin",
        ),
    )
