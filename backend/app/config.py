from functools import lru_cache
from typing import Literal

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Single source of truth for backend environment configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    supabase_url: HttpUrl
    supabase_anon_key: str
    supabase_service_role_key: str
    database_url: str = Field(
        description="Direct Postgres session URL for Alembic and backend DB access.",
    )

    # Embedding backend — see ingest/run.py and retrieval/embedding.py.
    embedding_backend: Literal["local", "openai"] = "local"
    local_embedding_model: str = "BAAI/bge-small-en-v1.5"

    # LLM backend for the Phase 7 agent (assistant/agent.py) — separate
    # concern from embedding_backend. Chosen after local Ollama models
    # (3B: failed structured tool-calling even under tool_choice="required";
    # 7B: exceeded available RAM and froze the machine) proved unworkable
    # on this hardware. Gemini's free tier gives real function-calling
    # support at zero cost, which is what this phase's grounding contract
    # depends on — see assistant/instructions.md.
    llm_backend: Literal["gemini", "openai"] = "gemini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.1-flash-lite"
    openai_llm_model: str = "gpt-4o-mini"

    # Optional because a local-embedding + Gemini-LLM run needs no OpenAI
    # key at all. Required in practice only when embedding_backend or
    # llm_backend == "openai" — enforced below.
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536

    allowed_origins: str = "http://localhost:5173"

    @field_validator("supabase_anon_key", "supabase_service_role_key")
    @classmethod
    def non_empty_secret(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be empty")
        return stripped

    @field_validator("openai_api_key", "gemini_api_key")
    @classmethod
    def non_empty_key_if_set(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be empty")
        return stripped

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        stripped = value.strip().strip('"').strip("'")
        if not stripped.startswith(("postgresql://", "postgres://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        if "pooler.supabase.com" in stripped and ":6543" in stripped:
            raise ValueError(
                "DATABASE_URL must use a session-mode connection (port 5432), "
                "not Supabase's transaction pooler (port 6543) — transaction "
                "mode doesn't support the full session semantics Alembic/SQLAlchemy need."
            )
        return stripped

    @field_validator("openai_embedding_dimensions")
    @classmethod
    def positive_embedding_dimensions(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("OPENAI_EMBEDDING_DIMENSIONS must be positive")
        return value

    @property
    def allowed_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]

    def model_post_init(self, __context) -> None:
        if self.embedding_backend == "openai" and not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when EMBEDDING_BACKEND=openai"
            )
        if self.llm_backend == "gemini" and not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when LLM_BACKEND=gemini")
        if self.llm_backend == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_BACKEND=openai")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def __getattr__(name: str) -> Settings:
    if name == "settings":
        return get_settings()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")