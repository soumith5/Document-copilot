import json
from pathlib import Path

import sec2md
import structlog
from openai import OpenAI

from app.config import get_settings
from app.database.models.document_chunk import DocumentChunk
from app.database.models.source_document import SourceDocument
from app.database.session import SessionLocal

log = structlog.get_logger()

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
MANIFEST_PATH = DATA_DIR / "downloads" / "manifest.json"

# Manifest only has tickers, not full company names — small local lookup.
COMPANY_NAMES = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "NVDA": "NVIDIA Corporation",
    "AMZN": "Amazon.com, Inc.",
    "GOOGL": "Alphabet Inc.",
}

EMBEDDING_BATCH_SIZE = 100

# Lazily constructed so a local-only run never needs an OpenAI key, and an
# OpenAI-only run never pulls in sentence-transformers/torch at import time.
_local_model = None


def find_section_for_page(sections: list, page_number: int) -> dict | None:
    """Finds which extracted section (Item 1, Item 1A, etc.) a given page
    belongs to, by checking page-range containment."""
    for section in sections:
        start, end = section.page_range
        if start <= page_number <= end:
            return {"item": section.item, "item_title": section.item_title}
    return None


def _get_local_model(model_name: str):
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer

        log.info("loading_local_embedding_model", model=model_name)
        _local_model = SentenceTransformer(model_name)
    return _local_model


def embed_texts_openai(client: OpenAI, texts: list[str], model: str) -> list[list[float]]:
    """Embeds a list of texts in batches via the OpenAI API, preserving order."""
    embeddings: list[list[float]] = []
    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch = texts[i : i + EMBEDDING_BATCH_SIZE]
        response = client.embeddings.create(model=model, input=batch)
        embeddings.extend(item.embedding for item in response.data)
    return embeddings


def embed_texts_local(texts: list[str], model_name: str) -> list[list[float]]:
    """Embeds a list of texts locally via sentence-transformers, preserving order.

    No API key, no network call, no per-token cost. bge models are trained
    to work well with normalized (cosine) similarity, which matches the
    vector_cosine_ops HNSW index already used for the embedding column.
    """
    model = _get_local_model(model_name)
    embeddings = model.encode(
        texts,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return embeddings.tolist()


def embed_texts(client: OpenAI | None, texts: list[str], settings) -> list[list[float]]:
    """Dispatches to the configured embedding backend."""
    if settings.embedding_backend == "local":
        return embed_texts_local(texts, settings.local_embedding_model)
    return embed_texts_openai(client, texts, settings.openai_embedding_model)


def ingest_filing(db, client: OpenAI | None, settings, filing: dict) -> None:
    ticker = filing["ticker"]
    accession = filing["accession_number"]

    existing = (
        db.query(SourceDocument)
        .filter(SourceDocument.doc_metadata["accession_number"].astext == accession)
        .first()
    )
    if existing:
        log.info("skip_already_ingested", ticker=ticker, accession=accession)
        return

    html_path = DATA_DIR / "downloads" / filing["local_path"]
    html = html_path.read_text(encoding="utf-8")

    parser = sec2md.Parser(html)
    pages = parser.get_pages()
    sections = sec2md.extract_sections(pages, filing_type="10-K")
    chunks = sec2md.chunk_pages(pages, chunk_size=512)

    document = SourceDocument(
        title=f"{ticker} 10-K — fiscal year {filing['report_date'][:4]}",
        source_url=filing["source_url"],
        doc_metadata={
            "ticker": ticker,
            "company": COMPANY_NAMES.get(ticker, ticker),
            "filing_type": filing["form"],
            "year": filing["report_date"][:4],
            "accession_number": accession,
            "filing_date": filing["filing_date"],
            "report_date": filing["report_date"],
        },
    )
    db.add(document)
    db.flush()  # populates document.id without a full commit yet

    texts = [chunk.content for chunk in chunks]
    embeddings = embed_texts(client, texts, settings)

    for chunk, embedding in zip(chunks, embeddings, strict=True):
        page_start, page_end = chunk.page_range
        section_info = find_section_for_page(sections, page_start)

        db.add(
            DocumentChunk(
                document_id=document.id,
                content=chunk.content,
                embedding=embedding,
                chunk_metadata={
                    "page_start": page_start,
                    "page_end": page_end,
                    "has_table": chunk.has_table,
                    "tags": chunk.tags,
                    **(section_info or {}),
                },
            )
        )

    db.commit()
    log.info(
        "filing_ingested",
        ticker=ticker,
        accession=accession,
        chunk_count=len(chunks),
        embedding_backend=settings.embedding_backend,
    )


def main() -> None:
    settings = get_settings()
    # No OpenAI client needed at all for a local-only run.
    client = OpenAI(api_key=settings.openai_api_key) if settings.embedding_backend == "openai" else None
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    log.info("ingestion_starting", embedding_backend=settings.embedding_backend)

    db = SessionLocal()
    try:
        for filing in manifest["filings"]:
            ingest_filing(db, client, settings, filing)
    finally:
        db.close()


if __name__ == "__main__":
    main()
