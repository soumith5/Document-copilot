from app.database.models.document_chunk import DocumentChunk
from app.retrieval.retriever import retrieve, with_neighboring_context
from sqlalchemy.orm import Session


def search_filings(
    db: Session, query: str, ticker: str | None = None, top_k: int = 8
) -> list[DocumentChunk]:
    """Bounded retrieval tool: hybrid search over the filing corpus.

    ticker, when given, strictly scopes results to that company (e.g.
    "AAPL") — see retriever.retrieve for why this is strict rather than a
    soft ranking boost. In Phase 7 the agent is expected to extract ticker
    from the user's question (company name/symbol mentions) before calling
    this — this function does no such parsing itself.
    """
    return retrieve(db, query, top_k=top_k, ticker=ticker)


def read_chunk(db: Session, chunk_id: int) -> DocumentChunk | None:
    """Bounded tool: fetch one chunk by id, e.g. to let the agent pull the
    full text behind a citation it already has a chunk_id for.
    """
    return db.get(DocumentChunk, chunk_id)


def read_surrounding_chunks(db: Session, chunk_id: int) -> list[DocumentChunk]:
    """Bounded tool: fetch the chunks immediately before/after the given
    chunk in its source document, for when a retrieved passage alone isn't
    enough context to ground an answer confidently.
    """
    chunk = db.get(DocumentChunk, chunk_id)
    if chunk is None:
        return []
    context = with_neighboring_context(db, [chunk])
    return context[chunk.id]