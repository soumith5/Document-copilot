from pydantic import BaseModel, ConfigDict


class UIMessagePart(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    text: str | None = None


class UIMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    role: str
    parts: list[UIMessagePart] = []


class ChatStreamRequest(BaseModel):
    thread_id: int
    messages: list[UIMessage]


def extract_last_user_text(messages: list[UIMessage]) -> str:
    """Finds the most recent user message and joins its text parts."""
    for message in reversed(messages):
        if message.role == "user":
            return "".join(
                part.text or "" for part in message.parts if part.type == "text"
            )
    return ""