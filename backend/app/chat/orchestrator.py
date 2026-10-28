import structlog
from collections.abc import Iterator

from app.assistant.agent import agent
from app.assistant.deps import AgentDeps
from app.database.models.chat_message import ChatMessage
from app.database.models.message_citation import MessageCitation
from app.database.session import SessionLocal
from app.grounding.validator import validate_grounding

log = structlog.get_logger()

STREAM_CHUNK_SIZE = 8

FALLBACK_MESSAGE = (
    "I found some information but couldn't verify it was properly grounded "
    "in the source filings, so I'm not able to share it as-is. Could you "
    "try rephrasing the question?"
)

AGENT_ERROR_MESSAGE = (
    "Something went wrong while generating this answer — this can happen "
    "with complex, multi-part questions that need several searches, "
    "especially if the AI provider's rate limit was hit. Please try again "
    "in a moment, or try breaking the question into smaller parts."
)


def stream_agent_response(thread_id: int, user_text: str) -> Iterator[str]:
    db = SessionLocal()
    try:
        deps = AgentDeps(db=db)

        try:
            result = agent.run_sync(user_text, deps=deps)
            output = result.output
        except Exception:
            # Covers rate limits, timeouts, and any other transient failure
            # from the underlying LLM call. Without this, an exception here
            # silently ends the stream with zero bytes yielded and nothing
            # persisted — the user sees a blank assistant reply with no
            # explanation, which is worse than a clearly-labeled failure.
            log.exception("agent_run_failed", thread_id=thread_id)
            answer_text = AGENT_ERROR_MESSAGE
            citations = []
            for i in range(0, len(answer_text), STREAM_CHUNK_SIZE):
                yield answer_text[i : i + STREAM_CHUNK_SIZE]

            message = ChatMessage(thread_id=thread_id, role="assistant", content=answer_text)
            db.add(message)
            db.commit()
            return

        validation = validate_grounding(deps, output)
        if not validation.valid:
            log.warning("grounding_validation_failed", thread_id=thread_id, errors=validation.errors)
            answer_text = FALLBACK_MESSAGE
            citations = []
        else:
            answer_text = output.answer
            citations = output.citations

        for i in range(0, len(answer_text), STREAM_CHUNK_SIZE):
            yield answer_text[i : i + STREAM_CHUNK_SIZE]

        message = ChatMessage(thread_id=thread_id, role="assistant", content=answer_text)
        db.add(message)
        db.flush()

        for citation in citations:
            db.add(MessageCitation(message_id=message.id, chunk_id=citation.chunk_id))

        db.commit()
    finally:
        db.close()