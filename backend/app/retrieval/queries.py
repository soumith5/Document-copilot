from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.models.document_chunk import DocumentChunk
from app.database.models.source_document import SourceDocument


def semantic_search(
    db: Session, query_embedding: list[float], limit: int = 20, ticker: str | None = None
) -> list[DocumentChunk]:
    q = db.query(DocumentChunk)
    if ticker is not None:
        q = q.join(SourceDocument, DocumentChunk.document_id == SourceDocument.id).filter(
            SourceDocument.doc_metadata["ticker"].astext == ticker
        )
    return (
        q.order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(limit)
        .all()
    )


def full_text_search(
    db: Session, query: str, limit: int = 20, ticker: str | None = None
) -> list[DocumentChunk]:
    """Postgres full-text search over search_vector.

    Builds an OR query across the individual query terms rather than using
    plainto_tsquery's implicit AND. AND semantics require every term to
    co-occur in one chunk, which is far too strict for natural-language
    queries feeding an RRF-fused hybrid search — this path exists to widen
    keyword recall, not to gatekeep on exact phrase match.
    """
    words = query.split()
    or_query = " | ".join(words) if words else query
    ts_query = func.to_tsquery("english", or_query)

    q = db.query(DocumentChunk).filter(DocumentChunk.search_vector.op("@@")(ts_query))
    if ticker is not None:
        q = q.join(SourceDocument, DocumentChunk.document_id == SourceDocument.id).filter(
            SourceDocument.doc_metadata["ticker"].astext == ticker
        )
    return q.order_by(func.ts_rank(DocumentChunk.search_vector, ts_query).desc()).limit(limit).all()