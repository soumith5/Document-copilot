import pytest

from app.assistant.deps import AgentDeps
from app.assistant.output import Citation, GroundedAnswer
from app.grounding.validator import GroundingError, validate_grounding, validate_grounding_or_raise


def _deps(retrieved_ids: set[int]) -> AgentDeps:
    # db is never touched by the validator, so None is a safe stand-in here.
    return AgentDeps(db=None, retrieved_chunk_ids=retrieved_ids)


class TestValidateGrounding:
    def test_valid_answer_with_real_citation_passes(self):
        deps = _deps({54, 519})
        output = GroundedAnswer(
            answer="Apple's Services net sales were $109,158 million in FY2025.",
            citations=[Citation(chunk_id=54, claim="Services net sales were $109,158 million.")],
            sufficient_evidence=True,
        )
        result = validate_grounding(deps, output)
        assert result.valid
        assert result.errors == []

    def test_citation_to_never_retrieved_chunk_fails(self):
        deps = _deps({54})
        output = GroundedAnswer(
            answer="Apple's Services net sales were $109,158 million in FY2025.",
            citations=[Citation(chunk_id=999, claim="Services net sales were $109,158 million.")],
            sufficient_evidence=True,
        )
        result = validate_grounding(deps, output)
        assert not result.valid
        assert "chunk_id=999" in result.errors[0]

    def test_affirmative_answer_with_no_citations_fails(self):
        deps = _deps({54})
        output = GroundedAnswer(
            answer="Apple's Services net sales were $109,158 million in FY2025.",
            citations=[],
            sufficient_evidence=True,
        )
        result = validate_grounding(deps, output)
        assert not result.valid
        assert "no citations" in result.errors[0]

    def test_refusal_with_no_citations_is_valid(self):
        # sufficient_evidence=False is a legitimate outcome and doesn't
        # require citations the way an affirmative answer does.
        deps = _deps(set())
        output = GroundedAnswer(
            answer="The filings don't contain a 2030 revenue projection.",
            citations=[],
            sufficient_evidence=False,
        )
        result = validate_grounding(deps, output)
        assert result.valid

    def test_refusal_can_still_cite_real_retrieved_chunks(self):
        # Matches the real observed behavior: a refusal citing the
        # historical chunks that were checked (and found insufficient).
        deps = _deps({181, 289})
        output = GroundedAnswer(
            answer="The filings only contain historical data through 2024, not a 2030 projection.",
            citations=[
                Citation(chunk_id=181, claim="Historical net sales data through 2024."),
                Citation(chunk_id=289, claim="Historical net sales data through 2023."),
            ],
            sufficient_evidence=False,
        )
        result = validate_grounding(deps, output)
        assert result.valid

    def test_multiple_errors_are_all_reported(self):
        deps = _deps({54})
        output = GroundedAnswer(
            answer="...",
            citations=[Citation(chunk_id=999, claim="...")],
            sufficient_evidence=True,
        )
        result = validate_grounding(deps, output)
        assert len(result.errors) == 1  # only the bad citation; citations list is non-empty


class TestValidateGroundingOrRaise:
    def test_raises_grounding_error_on_invalid_answer(self):
        deps = _deps({54})
        output = GroundedAnswer(
            answer="...",
            citations=[Citation(chunk_id=999, claim="...")],
            sufficient_evidence=True,
        )
        with pytest.raises(GroundingError):
            validate_grounding_or_raise(deps, output)

    def test_does_not_raise_on_valid_answer(self):
        deps = _deps({54})
        output = GroundedAnswer(
            answer="...",
            citations=[Citation(chunk_id=54, claim="...")],
            sufficient_evidence=True,
        )
        validate_grounding_or_raise(deps, output)  # should not raise