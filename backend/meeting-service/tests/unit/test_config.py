import pytest
from pydantic import ValidationError

from app.config import Settings


def make(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)  # type: ignore[arg-type]


def test_defaults_use_kafka_and_local_sqlite() -> None:
    settings = make()
    assert settings.processing_mode == "kafka"
    assert settings.database_url.startswith("sqlite:///")


def test_cors_origins_are_split_and_trimmed() -> None:
    settings = make(cors_origins=" http://a.test , https://b.test,, ")
    assert settings.cors_origin_list == ["http://a.test", "https://b.test"]


def test_http_mode_requires_internal_token() -> None:
    with pytest.raises(ValidationError, match="INTERNAL_API_TOKEN"):
        make(processing_mode="http")
    assert make(processing_mode="http", internal_api_token="secret").processing_mode == "http"


def test_unknown_processing_mode_is_rejected() -> None:
    with pytest.raises(ValidationError):
        make(processing_mode="carrier-pigeon")


def test_settings_read_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROCESSING_MODE", "inline-test")
    monkeypatch.setenv("CORS_ORIGINS", "http://x.test")
    settings = make()
    assert settings.processing_mode == "inline-test"
    assert settings.cors_origin_list == ["http://x.test"]
