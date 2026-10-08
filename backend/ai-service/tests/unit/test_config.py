import pytest
from pydantic import ValidationError

from app.config import Settings


def make(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)  # type: ignore[arg-type]


def test_defaults_are_kafka_and_mock_provider() -> None:
    settings = make()
    assert (settings.processing_mode, settings.summary_provider) == ("kafka", "mock")


def test_http_mode_requires_internal_token() -> None:
    with pytest.raises(ValidationError, match="INTERNAL_API_TOKEN"):
        make(processing_mode="http")
    assert make(processing_mode="http", internal_api_token="t").processing_mode == "http"


def test_llm_provider_requires_api_key() -> None:
    with pytest.raises(ValidationError, match="LLM_API_KEY"):
        make(summary_provider="llm")
    assert make(summary_provider="llm", llm_api_key="k").summary_provider == "llm"


def test_inline_test_mode_is_not_valid_for_the_ai_service() -> None:
    with pytest.raises(ValidationError):
        make(processing_mode="inline-test")
