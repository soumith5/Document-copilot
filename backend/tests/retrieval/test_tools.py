from app.database.models.document_chunk import DocumentChunk
from app.retrieval import tools


def _chunk(chunk_id: int, document_id: int, content: str) -> DocumentChunk:
    return DocumentChunk(id=chunk_id, document_id=document_id, content=content, chunk_metadata={})


class TestSearchFilings:
    def test_delegates_to_retrieve_with_same_arguments(self, monkeypatch):
        received = {}

        def fake_retrieve(db, query, top_k=8, ticker=None):
            received["query"] = query
            received["top_k"] = top_k
            received["ticker"] = ticker
            return [_chunk(1, 1, "result")]

        monkeypatch.setattr(tools, "retrieve", fake_retrieve)

        results = tools.search_filings(object(), "Apple Services revenue mix", ticker="AAPL", top_k=3)

        assert received == {"query": "Apple Services revenue mix", "top_k": 3, "ticker": "AAPL"}
        assert len(results) == 1


class TestReadChunk:
    def test_returns_none_for_missing_chunk(self, monkeypatch):
        class FakeDb:
            def get(self, model, chunk_id):
                return None

        assert tools.read_chunk(FakeDb(), 999) is None

    def test_returns_the_chunk_when_found(self, monkeypatch):
        expected = _chunk(5, 1, "some content")

        class FakeDb:
            def get(self, model, chunk_id):
                return expected if chunk_id == 5 else None

        assert tools.read_chunk(FakeDb(), 5) is expected


class TestReadSurroundingChunks:
    def test_returns_empty_list_for_missing_chunk(self, monkeypatch):
        class FakeDb:
            def get(self, model, chunk_id):
                return None

        assert tools.read_surrounding_chunks(FakeDb(), 999) == []

    def test_delegates_to_with_neighboring_context(self, monkeypatch):
        target = _chunk(5, 1, "target")
        neighbors = [_chunk(4, 1, "before"), _chunk(6, 1, "after")]

        class FakeDb:
            def get(self, model, chunk_id):
                return target if chunk_id == 5 else None

        monkeypatch.setattr(
            tools, "with_neighboring_context", lambda db, chunks: {5: neighbors}
        )

        result = tools.read_surrounding_chunks(FakeDb(), 5)
        assert result == neighbors