from pathlib import Path

import pytest
from pydantic import ValidationError

from jarvis.core.settings import Settings, get_settings


def test_defaults_are_safe_for_local_dev() -> None:
    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.env == "development"
    assert settings.api_port == 8000
    assert settings.workspace_dir == Path("./workspace")
    assert settings.cors_origins == ["http://localhost:3000"]


def test_cors_origins_accepts_csv_string() -> None:
    settings = Settings(_env_file=None, cors_origins="http://a.com, http://b.com")  # type: ignore[call-arg]

    assert settings.cors_origins == ["http://a.com", "http://b.com"]


def test_is_production_flag() -> None:
    dev = Settings(_env_file=None, env="development")  # type: ignore[call-arg]
    prod = Settings(_env_file=None, env="production")  # type: ignore[call-arg]

    assert dev.is_production is False
    assert prod.is_production is True


def test_get_settings_is_memoized() -> None:
    get_settings.cache_clear()
    try:
        assert get_settings() is get_settings()
    finally:
        get_settings.cache_clear()


@pytest.mark.parametrize("bad_env", ["staging", "prod", ""])
def test_invalid_env_literal_rejected(bad_env: str) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, env=bad_env)  # type: ignore[call-arg]


def test_postgres_dsn_built_from_parts() -> None:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        postgres_host="db.internal",
        postgres_port=5433,
        postgres_db="jarvisdb",
        postgres_user="jarvis_user",
        postgres_password="s3cr3t",
    )

    assert settings.postgres_dsn == (
        "postgresql+asyncpg://jarvis_user:s3cr3t@db.internal:5433/jarvisdb"
    )


def test_redis_url_built_from_parts() -> None:
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        redis_host="cache.internal",
        redis_port=6380,
        redis_db=2,
    )

    assert settings.redis_url == "redis://cache.internal:6380/2"


def test_postgres_and_redis_settings_are_unprefixed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POSTGRES_HOST", "env-host")
    monkeypatch.setenv("REDIS_PORT", "7000")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.postgres_host == "env-host"
    assert settings.redis_port == 7000


def test_llm_api_keys_default_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    # Isolate from the ambient environment: some sandboxes/CI runners set
    # ANTHROPIC_BASE_URL themselves for unrelated reasons.
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.anthropic_api_key is None
    assert settings.anthropic_base_url is None
    assert settings.openai_api_key is None
    assert settings.default_llm_provider == "anthropic"


def test_anthropic_base_url_reads_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "http://localhost:9999")

    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.anthropic_base_url == "http://localhost:9999"
