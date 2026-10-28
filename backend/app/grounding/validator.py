from dataclasses import dataclass

from app.assistant.deps import AgentDeps
from app.assistant.output import GroundedAnswer


class GroundingError(Exception):
    """Raised when a GroundedAnswer's citations don't hold up against what
    was actually retrieved during the agent run. This is the fail-closed
    boundary: an answer that fails validation must never reach the user
    as-is — trusting the model's self-reported citations without checking
    them is exactly the gap this closes. See chat/orchestrator.py (Phase 7,
    still to be built) for where this gets called in the real request path.
    """


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]


def validate_grounding(deps: AgentDeps, output: GroundedAnswer) -> ValidationResult:
    """Checks a GroundedAnswer against what was actually retrieved this turn.

    Two checks:
    1. An affirmative answer (sufficient_evidence=True) must have at least
       one citation — an unconditional claim with zero citations is
       ungrounded by definition, regardless of whether it happens to be true.
    2. Every citation's chunk_id must be in deps.retrieved_chunk_ids — i.e.
       actually returned by search_filings/read_chunk/read_surrounding_chunks
       during this run, not merely asserted by the model. This catches
       hallucinated citations: the model claiming it cited chunk 54 when it
       never actually retrieved chunk 54 at all.
    """
    errors: list[str] = []

    if output.sufficient_evidence and not output.citations:
        errors.append(
            "sufficient_evidence=True but no citations were provided — "
            "an affirmative answer must be grounded in at least one cited chunk."
        )

    for citation in output.citations:
        if citation.chunk_id not in deps.retrieved_chunk_ids:
            errors.append(
                f"citation references chunk_id={citation.chunk_id}, which was never "
                "retrieved during this turn (not returned by search_filings, read_chunk, "
                "or read_surrounding_chunks) — likely a hallucinated citation."
            )

    return ValidationResult(valid=not errors, errors=errors)


def validate_grounding_or_raise(deps: AgentDeps, output: GroundedAnswer) -> None:
    result = validate_grounding(deps, output)
    if not result.valid:
        raise GroundingError("; ".join(result.errors))