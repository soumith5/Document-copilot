from pathlib import Path

from pydantic_ai import Agent, RunContext

from app.assistant.deps import AgentDeps
from app.assistant.output import GroundedAnswer
from app.config import get_settings
from app.retrieval.tools import read_chunk, read_surrounding_chunks, search_filings

INSTRUCTIONS = (Path(__file__).parent / "instructions.md").read_text(encoding="utf-8")


def _build_model():
    """Picks the LLM backend per settings.llm_backend.

    Gemini is the default after local Ollama models (3B: failed structured
    tool-calling even under tool_choice="required"; 7B: exceeded available
    RAM) proved unworkable on this hardware — see config.py's llm_backend
    docstring. OpenAI stays available as a fallback/comparison path.
    """
    settings = get_settings()
    if settings.llm_backend == "gemini":
        from pydantic_ai.models.google import GoogleModel
        from pydantic_ai.providers.google import GoogleProvider

        provider = GoogleProvider(api_key=settings.gemini_api_key)
        return GoogleModel(settings.gemini_model, provider=provider)

    from pydantic_ai.models.openai import OpenAIModel

    return OpenAIModel(settings.openai_llm_model, api_key=settings.openai_api_key)


agent = Agent(
    _build_model(),
    deps_type=AgentDeps,
    output_type=GroundedAnswer,
    instructions=INSTRUCTIONS,
)


def _chunk_to_dict(chunk, ticker: str, company: str) -> dict:
    """Shapes a DocumentChunk into what the LLM actually needs to reason
    about and cite it: id (for citations), content, and the metadata that
    tells it what it's looking at. Kept in agent.py rather than
    retrieval/tools.py deliberately — this is an LLM-facing serialization
    concern, not a retrieval concern; retrieval/tools.py stays pure.
    """
    metadata = chunk.chunk_metadata or {}
    return {
        "chunk_id": chunk.id,
        "content": chunk.content,
        "ticker": ticker,
        "company": company,
        "item": metadata.get("item"),
        "item_title": metadata.get("item_title"),
        "page_start": metadata.get("page_start"),
        "page_end": metadata.get("page_end"),
    }


@agent.tool
def search_filings_tool(
    ctx: RunContext[AgentDeps], query: str, ticker: str | None = None, top_k: int = 8
) -> list[dict]:
    """Hybrid search over the 10-K corpus. Pass ticker (e.g. "AAPL") whenever
    the question names a specific company — results are strictly scoped to
    that company when given, and mixed-company results otherwise.
    """
    from app.database.models.source_document import SourceDocument

    chunks = search_filings(ctx.deps.db, query, ticker=ticker, top_k=top_k)
    result = []
    for chunk in chunks:
        ctx.deps.retrieved_chunk_ids.add(chunk.id)
        document = ctx.deps.db.get(SourceDocument, chunk.document_id)
        doc_meta = document.doc_metadata or {}
        result.append(_chunk_to_dict(chunk, doc_meta.get("ticker", ""), doc_meta.get("company", "")))
    return result


@agent.tool
def read_chunk_tool(ctx: RunContext[AgentDeps], chunk_id: int) -> dict | None:
    """Fetch one chunk's full content by id."""
    from app.database.models.source_document import SourceDocument

    chunk = read_chunk(ctx.deps.db, chunk_id)
    if chunk is None:
        return None
    ctx.deps.retrieved_chunk_ids.add(chunk.id)
    document = ctx.deps.db.get(SourceDocument, chunk.document_id)
    doc_meta = document.doc_metadata or {}
    return _chunk_to_dict(chunk, doc_meta.get("ticker", ""), doc_meta.get("company", ""))


@agent.tool
def read_surrounding_chunks_tool(ctx: RunContext[AgentDeps], chunk_id: int) -> list[dict]:
    """Fetch the chunks immediately before/after a given chunk, for extra
    context when a passage alone isn't enough to interpret confidently.
    """
    from app.database.models.source_document import SourceDocument

    chunks = read_surrounding_chunks(ctx.deps.db, chunk_id)
    result = []
    for chunk in chunks:
        ctx.deps.retrieved_chunk_ids.add(chunk.id)
        document = ctx.deps.db.get(SourceDocument, chunk.document_id)
        doc_meta = document.doc_metadata or {}
        result.append(_chunk_to_dict(chunk, doc_meta.get("ticker", ""), doc_meta.get("company", "")))
    return result