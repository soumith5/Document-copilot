import re

from sqlalchemy.orm import Session

from app.database.models.document_chunk import DocumentChunk
from app.retrieval.embedding import embed_query
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.queries import full_text_search, semantic_search

CANDIDATE_POOL_SIZE = 20
NEIGHBOR_WINDOW = 1  # chunks before/after each retrieved chunk, same document
DEDUP_PREFIX_LEN = 300  # chars of normalized content compared for near-duplicate detection


def _content_fingerprint(content: str) -> str:
    """Normalizes whitespace/case and takes a leading slice as a cheap
    near-duplicate signal. Boilerplate reused across filing years (e.g. the
    same 'Cloud Services' product description repeated in every 10-K) is
    word-for-word identical at the start of the chunk, so this catches the
    real-world duplication pattern without needing a fuzzy-match library.
    """
    normalized = re.sub(r"\s+", " ", content.strip().lower())
    return normalized[:DEDUP_PREFIX_LEN]


def retrieve(
    db: Session, query: str, top_k: int = 8, ticker: str | None = None
) -> list[DocumentChunk]:
    """One retrieval turn: embed -> semantic + full-text search -> RRF fuse
    -> dedupe near-identical content -> top_k.

    ticker, when given, strictly scopes results to that company (e.g.
    "AAPL"). This is deliberately strict, not a soft ranking boost — a
    grounded QA tool returning the wrong company's numbers is a worse
    failure than returning fewer results, given the trust contract in
    todos.md Phase 7 (cite only retrieved passages, refuse when evidence
    is weak). The Phase 7 agent tool is expected to parse company mentions
    out of the user's question and pass ticker here rather than relying on
    company names surviving as free-text search terms.
    """
    query_embedding = embed_query(query)

    semantic_results = semantic_search(db, query_embedding, limit=CANDIDATE_POOL_SIZE, ticker=ticker)
    fulltext_results = full_text_search(db, query, limit=CANDIDATE_POOL_SIZE, ticker=ticker)

    semantic_ids = [chunk.id for chunk in semantic_results]
    fulltext_ids = [chunk.id for chunk in fulltext_results]
    fused_scores = reciprocal_rank_fusion([semantic_ids, fulltext_ids])

    by_id = {chunk.id: chunk for chunk in semantic_results + fulltext_results}
    ranked_ids = sorted(fused_scores, key=lambda cid: fused_scores[cid], reverse=True)

    deduped: list[DocumentChunk] = []
    seen_fingerprints: set[str] = set()
    for cid in ranked_ids:
        chunk = by_id[cid]
        fingerprint = _content_fingerprint(chunk.content)
        if fingerprint in seen_fingerprints:
            continue
        seen_fingerprints.add(fingerprint)
        deduped.append(chunk)
        if len(deduped) == top_k:
            break

    return deduped


def with_neighboring_context(db: Session, chunks: list[DocumentChunk]) -> dict[int, list[DocumentChunk]]:
    """For each retrieved chunk, fetch the chunks immediately before/after it
    in the same document (by primary key order, which matches ingestion
    order — see ingest/run.py) to give the LLM surrounding context.
    """
    context: dict[int, list[DocumentChunk]] = {}
    for chunk in chunks:
        neighbors = (
            db.query(DocumentChunk)
            .filter(
                DocumentChunk.document_id == chunk.document_id,
                DocumentChunk.id.between(
                    chunk.id - NEIGHBOR_WINDOW, chunk.id + NEIGHBOR_WINDOW
                ),
                DocumentChunk.id != chunk.id,
            )
            .order_by(DocumentChunk.id)
            .all()
        )
        context[chunk.id] = neighbors
    return context