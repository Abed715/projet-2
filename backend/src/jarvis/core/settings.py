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

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.env == "production"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide `Settings` singleton.

    Cached so every module observes the same configuration; tests that need
    a different configuration should call `get_settings.cache_clear()` after
    patching the environment.
    """
    return Settings()
