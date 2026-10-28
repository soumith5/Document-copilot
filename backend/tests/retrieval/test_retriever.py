from app.database.models.document_chunk import DocumentChunk
from app.retrieval import retriever

# The real boilerplate paragraph that was found duplicated across four
# fiscal years' filings during manual testing — this is what triggered the
# dedup fix, so it's the fixture for the regression test.
CLOUD_SERVICES_BOILERPLATE = (
    "Cloud Services\nThe Company's cloud services store and keep customers' "
    "content up-to-date and available across multiple Apple devices and "
    "Windows personal computers."
)


def _chunk(chunk_id: int, document_id: int, content: str) -> DocumentChunk:
    """Builds a DocumentChunk without touching the DB — retrieve() only
    reads .id and .content off what the search functions return, so a
    bare, unsaved instance is a faithful, DB-free stand-in for these tests.
    """
    return DocumentChunk(id=chunk_id, document_id=document_id, content=content, chunk_metadata={})


class TestContentFingerprint:
    def test_normalizes_whitespace_and_case(self):
        a = retriever._content_fingerprint("Hello   World\n\nFoo")
        b = retriever._content_fingerprint("hello world foo")
        assert a == b

    def test_different_content_has_different_fingerprint(self):
        a = retriever._content_fingerprint("Apple Services revenue increased.")
        b = retriever._content_fingerprint("Microsoft Xbox revenue increased.")
        assert a != b

    def test_truncates_to_prefix_length(self):
        fingerprint = retriever._content_fingerprint("a" * 1000)
        assert len(fingerprint) == retriever.DEDUP_PREFIX_LEN


class TestRetrieve:
    def test_dedupes_near_identical_content_across_documents(self, monkeypatch):
        # Regression test for the real bug: the same boilerplate paragraph
        # repeated across four fiscal years (four different document_ids)
        # was dominating results before the dedup fix.
        duplicates = [
            _chunk(336, 5, CLOUD_SERVICES_BOILERPLATE),
            _chunk(8, 2, CLOUD_SERVICES_BOILERPLATE),
            _chunk(229, 4, CLOUD_SERVICES_BOILERPLATE),
            _chunk(119, 3, CLOUD_SERVICES_BOILERPLATE),
        ]
        unique = _chunk(404, 5, "Note 2 - Revenue. Net sales disaggregated by product...")

        monkeypatch.setattr(retriever, "embed_query", lambda query: [0.0])
        monkeypatch.setattr(retriever, "semantic_search", lambda *a, **k: duplicates + [unique])
        monkeypatch.setattr(retriever, "full_text_search", lambda *a, **k: [])

        results = retriever.retrieve(object(), "Apple Services revenue mix", top_k=5)

        boilerplate_hits = [c for c in results if c.content == CLOUD_SERVICES_BOILERPLATE]
        assert len(boilerplate_hits) == 1
        assert unique.id in [c.id for c in results]

    def test_respects_top_k(self, monkeypatch):
        chunks = [_chunk(i, 1, f"Unique content number {i}") for i in range(10)]

        monkeypatch.setattr(retriever, "embed_query", lambda query: [0.0])
        monkeypatch.setattr(retriever, "semantic_search", lambda *a, **k: chunks)
        monkeypatch.setattr(retriever, "full_text_search", lambda *a, **k: [])

        results = retriever.retrieve(object(), "any query", top_k=3)
        assert len(results) == 3

    def test_passes_ticker_through_to_both_search_functions(self, monkeypatch):
        received = {}

        def fake_semantic_search(db, query_embedding, limit=20, ticker=None):
            received["semantic_ticker"] = ticker
            return []

        def fake_full_text_search(db, query, limit=20, ticker=None):
            received["fulltext_ticker"] = ticker
            return []

        monkeypatch.setattr(retriever, "embed_query", lambda query: [0.0])
        monkeypatch.setattr(retriever, "semantic_search", fake_semantic_search)
        monkeypatch.setattr(retriever, "full_text_search", fake_full_text_search)

        retriever.retrieve(object(), "Apple Services revenue mix", top_k=5, ticker="AAPL")

        assert received["semantic_ticker"] == "AAPL"
        assert received["fulltext_ticker"] == "AAPL"

    def test_prioritizes_chunks_ranked_in_both_search_paths(self, monkeypatch):
        both = _chunk(1, 1, "appears in both searches")
        semantic_only = _chunk(2, 1, "appears only in semantic search")
        fulltext_only = _chunk(3, 1, "appears only in full text search")

        monkeypatch.setattr(retriever, "embed_query", lambda query: [0.0])
        monkeypatch.setattr(retriever, "semantic_search", lambda *a, **k: [both, semantic_only])
        monkeypatch.setattr(retriever, "full_text_search", lambda *a, **k: [both, fulltext_only])

        results = retriever.retrieve(object(), "any query", top_k=3)
        assert results[0].id == both.id