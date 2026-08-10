"""Environment-driven configuration shared across the whole backend."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process-wide configuration, populated from environment variables.

    Every field has a safe development-mode default so the app boots with no
    `.env` file at all; production deployments are expected to override via
    real environment variables (see `.env.example`).
    """

    model_config = SettingsConfigDict(
        env_prefix="JARVIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me-to-a-random-value"
    workspace_dir: Path = Path("./workspace")

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # --- Postgres (unprefixed env vars, shared with plain `psql`/tooling) ---
    postgres_host: str = Field("localhost", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(5432, validation_alias="POSTGRES_PORT")
    postgres_db: str = Field("jarvis", validation_alias="POSTGRES_DB")
    postgres_user: str = Field("jarvis", validation_alias="POSTGRES_USER")
    postgres_password: str = Field("jarvis", validation_alias="POSTGRES_PASSWORD")

    # --- Redis ---
    redis_host: str = Field("localhost", validation_alias="REDIS_HOST")
    redis_port: int = Field(6379, validation_alias="REDIS_PORT")
    redis_db: int = Field(0, validation_alias="REDIS_DB")

    # --- ChromaDB ---
    chroma_host: str = Field("localhost", validation_alias="CHROMA_HOST")
    chroma_port: int = Field(8001, validation_alias="CHROMA_PORT")

    # --- LLM providers ---
    anthropic_api_key: str | None = Field(None, validation_alias="ANTHROPIC_API_KEY")
    openai_api_key: str | None = Field(None, validation_alias="OPENAI_API_KEY")
    ollama_base_url: str = Field(
        "http://localhost:11434", validation_alias="OLLAMA_BASE_URL"
    )
    default_llm_provider: str = "anthropic"
    anthropic_model: str = "claude-opus-5"

    # --- Voice (STT/TTS, Phase 5) ---
    whisper_model_size: str = "small"
    piper_voice_model_path: Path | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def postgres_dsn(self) -> str:
        """Async SQLAlchemy DSN (asyncpg driver)."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide `Settings` singleton.

    Cached so every module observes the same configuration; tests that need
    a different configuration should call `get_settings.cache_clear()` after
    patching the environment.
    """
    return Settings()
