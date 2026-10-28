import time
from collections.abc import Iterator

from app.database.models.chat_message import ChatMessage
from app.database.session import SessionLocal

STUB_RESPONSE = (
    "This is a stubbed assistant response. Real retrieval and grounding "
    "will replace this in Phase 7."
)


def stream_stub_response(thread_id: int) -> Iterator[str]:
    """Yields the stub response in small chunks (simulating token-by-token
    streaming), then persists the complete assistant message using a
    fresh DB session — the request-scoped session may already be closed
    by the time this generator finishes iterating."""
    chunk_size = 8
    for i in range(0, len(STUB_RESPONSE), chunk_size):
        yield STUB_RESPONSE[i : i + chunk_size]
        time.sleep(0.05)

    db = SessionLocal()
    try:
        db.add(ChatMessage(thread_id=thread_id, role="assistant", content=STUB_RESPONSE))
        db.commit()
    finally:
        db.close()