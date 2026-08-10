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
