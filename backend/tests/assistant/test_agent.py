import pytest

from app.assistant.agent import agent
from app.assistant.deps import AgentDeps
from app.database.session import SessionLocal
from app.grounding.validator import validate_grounding

pytestmark = pytest.mark.integration


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class TestAgentGrounding:
    def test_well_covered_question_returns_grounded_answer(self, db):
        deps = AgentDeps(db=db)
        result = agent.run_sync(
            "What was Apple's Services revenue in fiscal year 2025?", deps=deps
        )
        output = result.output

        assert output.sufficient_evidence is True
        assert len(output.citations) > 0
        assert "109" in output.answer  # $109,158 million — the real figure, verified manually earlier

        validation = validate_grounding(deps, output)
        assert validation.valid, validation.errors

    def test_unanswerable_future_question_triggers_refusal(self, db):
        deps = AgentDeps(db=db)
        result = agent.run_sync(
            "What will Apple's Services revenue be in fiscal year 2030?", deps=deps
        )
        output = result.output

        assert output.sufficient_evidence is False

        validation = validate_grounding(deps, output)
        assert validation.valid, validation.errors

    def test_wrong_company_question_does_not_leak_other_companies_data(self, db):
        # Regression check for the ticker-filter behavior built into
        # retrieval/queries.py — the agent should scope search_filings to
        # the named company and not accidentally surface, e.g., Microsoft
        # data when asked about Apple.
        deps = AgentDeps(db=db)
        result = agent.run_sync(
            "What was Apple's Services revenue in fiscal year 2025?", deps=deps
        )
        output = result.output

        assert "Xbox" not in output.answer
        assert "Microsoft" not in output.answer