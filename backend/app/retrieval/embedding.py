from app.config import get_settings

_local_model = None

# bge-small-en-v1.5 was trained to prepend this instruction to queries
# (not to the documents being searched). Skipping it measurably hurts
# retrieval quality with BGE models specifically — irrelevant for OpenAI's
# embedding models, which take queries and documents identically.
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def _get_local_model(model_name: str):
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer

        _local_model = SentenceTransformer(model_name)
    return _local_model


def embed_query(query: str) -> list[float]:
    """Embeds a single search query using the configured backend.

    Mirrors ingest/run.py's backend dispatch, but query-shaped: one string
    in, one vector out, with the BGE query prefix applied when relevant.
    """
    settings = get_settings()

    if settings.embedding_backend == "local":
        model = _get_local_model(settings.local_embedding_model)
        prefixed = BGE_QUERY_PREFIX + query
        return model.encode(prefixed, normalize_embeddings=True).tolist()

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(
        model=settings.openai_embedding_model, input=[query]
    )
    return response.data[0].embedding