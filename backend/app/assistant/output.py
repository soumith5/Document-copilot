from pydantic import BaseModel, Field


class Citation(BaseModel):
    """One claim in the answer, tied to the specific chunk that supports it.

    chunk_id is checked against the chunks actually retrieved during this
    turn by grounding/validator.py — an answer citing a chunk_id that was
    never retrieved is a hallucinated citation and must fail validation,
    not just be trusted because the model said so.
    """

    chunk_id: int
    claim: str = Field(description="The specific factual claim this citation supports.")


class GroundedAnswer(BaseModel):
    """Typed output for the assistant agent.

    sufficient_evidence=False is a first-class outcome, not an error case —
    per todos.md's trust contract, refusing when evidence is weak is
    required behavior, not a fallback. When False, answer should explain
    what's missing rather than attempt an ungrounded guess.
    """

    answer: str
    citations: list[Citation]
    sufficient_evidence: bool