"""
All SQLAlchemy models live one-per-file in this package. This __init__
imports every one of them so that importing `app.database.models` (as
alembic/env.py does) populates `Base.metadata` completely — forgetting to
import a model here means Alembic silently won't see that table.
"""

from app.database.session import Base
from app.database.models.profile import Profile
from app.database.models.chat_thread import ChatThread
from app.database.models.chat_message import ChatMessage
from app.database.models.source_document import SourceDocument
from app.database.models.document_chunk import DocumentChunk
from app.database.models.message_citation import MessageCitation

__all__ = [
    "Base",
    "Profile",
    "ChatThread",
    "ChatMessage",
    "SourceDocument",
    "DocumentChunk",
    "MessageCitation",
]
