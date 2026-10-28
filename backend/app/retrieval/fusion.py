def reciprocal_rank_fusion(
    ranked_id_lists: list[list[int]], k: int = 60
) -> dict[int, float]:
    """Combines multiple ranked ID lists into one fused score per ID.

    Standard RRF: score(id) = sum over lists containing id of 1 / (k + rank).
    k=60 is the commonly used default from the original RRF paper — it
    dampens the effect of any single list's exact rank ordering.
    """
    scores: dict[int, float] = {}
    for ranked_ids in ranked_id_lists:
        for rank, chunk_id in enumerate(ranked_ids):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)
    return scores