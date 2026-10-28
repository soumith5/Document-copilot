from dataclasses import dataclass, field

from sqlalchemy.orm import Session


@dataclass
class AgentDeps:
    """Runtime dependencies injected into the agent.

    retrieved_chunk_ids accumulates every chunk_id actually returned by
    search_filings_tool/read_chunk_tool/read_surrounding_chunks_tool during
    a single agent run. grounding/validator.py checks the final answer's
    citations against this set — a citation to a chunk_id never in this
    set means the model cited something it never actually retrieved.
    """

    db: Session
    retrieved_chunk_ids: set[int] = field(default_factory=set)