from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Computed, DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.sql import func

from app.database.session import Base

# Embedding dimension depends on which backend produced it (see app.config.EMBEDDING_BACKEND):
#   - local (BAAI/bge-small-en-v1.5): 384
#   - openai (text-embedding-3-small): 1536
# These are not interchangeable in the same column — switching backends requires a migration
# to resize this column AND re-running ingestion, since old vectors from the other backend are
# not valid at the new dimension. Currently set for the local backend (384) per the A/B plan:
# run local end-to-end first, evaluate, and only migrate back to 1536 + OpenAI if needed.
EMBEDDING_DIM = 384


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("source_documents.id"), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIM), nullable=True)
    search_vector = Column(
        TSVECTOR,
        Computed("to_tsvector('english', content)", persisted=True),
        nullable=True,
    )
    # Chunk-level facts sec2md gives us: page_start, page_end, item,
    # item_title, tags (XBRL concepts). Document-level facts (ticker,
    # company, filing year) live on SourceDocument.doc_metadata instead —
    # this is specifically per-chunk data that varies within one filing.
    chunk_metadata = Column(JSONB)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index(
            "ix_document_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index(
            "ix_document_chunks_search_vector_gin",
            "search_vector",
            postgresql_using="gin",
        ),
        Index(
            "ix_document_chunks_chunk_metadata_gin",
            "chunk_metadata",
            postgresql_using="gin",
        ),
    )
