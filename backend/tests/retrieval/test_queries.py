import pytest

from app.database.models.source_document import SourceDocument
from app.database.session import SessionLocal
from app.retrieval.embedding import embed_query
from app.retrieval.queries import full_text_search, semantic_search
from app.retrieval.retriever import retrieve

pytestmark = pytest.mark.integration


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class TestSemanticSearch:
    def test_returns_results_for_a_real_query(self, db):
        query_embedding = embed_query("Apple Services revenue mix")
        results = semantic_search(db, query_embedding, limit=10)
        assert len(results) == 10

    def test_ticker_filter_returns_only_that_companys_chunks(self, db):
        query_embedding = embed_query("revenue")
        results = semantic_search(db, query_embedding, limit=10, ticker="AAPL")
        for chunk in results:
            document = db.get(SourceDocument, chunk.document_id)
            assert document.doc_metadata["ticker"] == "AAPL"


class TestFullTextSearch:
    def test_or_semantics_return_multiple_results_for_a_multiword_query(self, db):
        # Regression test for the AND-vs-OR bug: plainto_tsquery required
        # every word to co-occur in one chunk and returned almost nothing
        # for natural-language queries. This should return several results.
        results = full_text_search(db, "Apple Services revenue mix", limit=10)
        assert len(results) > 1

    def test_ticker_filter_returns_only_that_companys_chunks(self, db):
        results = full_text_search(db, "revenue", limit=10, ticker="AAPL")
        assert len(results) > 0
        for chunk in results:
            document = db.get(SourceDocument, chunk.document_id)
            assert document.doc_metadata["ticker"] == "AAPL"


class TestRetrieveEndToEnd:
    def test_apple_services_revenue_query_returns_grounded_relevant_results(self, db):
        results = retrieve(db, "Apple Services revenue mix", top_k=5, ticker="AAPL")

        assert len(results) == 5
        for chunk in results:
            document = db.get(SourceDocument, chunk.document_id)
            assert document.doc_metadata["ticker"] == "AAPL"

        # At least one result should carry real financial substance (a
        # dollar figure), not purely qualitative boilerplate — concrete
        # regression check for "did we actually find the real table."
        assert any("$" in chunk.content for chunk in results)

    def test_no_exact_duplicate_content_in_results(self, db):
        results = retrieve(db, "Apple Services revenue mix", top_k=5, ticker="AAPL")
        fingerprints = [c.content.strip().lower()[:300] for c in results]
        assert len(fingerprints) == len(set(fingerprints))