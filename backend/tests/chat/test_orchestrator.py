import pytest

from app.chat.orchestrator import stream_agent_response
from app.database.models.chat_message import ChatMessage
from app.database.models.chat_thread import ChatThread
from app.database.models.message_citation import MessageCitation
from app.database.session import SessionLocal

pytestmark = pytest.mark.integration


@pytest.fixture
def thread():
    """Creates a real throwaway thread and cleans up all rows it creates
    afterward, regardless of whether the test passes or fails.
    """
    db = SessionLocal()
    test_user_id = "949f3439-1741-4b5e-b14b-76bb7ed27054"
    thread = ChatThread(user_id=test_user_id, title="orchestrator test thread")
    db.add(thread)
    db.commit()
    db.refresh(thread)
    thread_id = thread.id
    db.close()

    yield thread_id

    cleanup_db = SessionLocal()
    try:
        cleanup_db.query(MessageCitation).filter(
            MessageCitation.message_id.in_(
                cleanup_db.query(ChatMessage.id).filter(ChatMessage.thread_id == thread_id)
            )
        ).delete(synchronize_session=False)
        cleanup_db.query(ChatMessage).filter(ChatMessage.thread_id == thread_id).delete()
        cleanup_db.query(ChatThread).filter(ChatThread.id == thread_id).delete()
        cleanup_db.commit()
    finally:
        cleanup_db.close()


class TestStreamAgentResponse:
    def test_persists_assistant_message_and_citations(self, thread):
        thread_id = thread

        chunks = list(
            stream_agent_response(thread_id, "What was Apple's Services revenue in fiscal year 2025?")
        )
        full_text = "".join(chunks)
        assert len(full_text) > 0
        assert "109" in full_text  # the real figure, verified manually earlier in this project

        db = SessionLocal()
        try:
            assistant_message = (
                db.query(ChatMessage)
                .filter(ChatMessage.thread_id == thread_id, ChatMessage.role == "assistant")
                .first()
            )
            assert assistant_message is not None
            assert assistant_message.content == full_text

            citations = (
                db.query(MessageCitation)
                .filter(MessageCitation.message_id == assistant_message.id)
                .all()
            )
            assert len(citations) > 0
        finally:
            db.close()