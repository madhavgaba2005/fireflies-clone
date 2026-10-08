"""Service configuration, read from environment variables (and an optional local .env file)."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI Processing Service"
    environment: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"

    # kafka: consume meeting.events, publish ai.events (reference)
    # http:  serve POST /internal/process for the Meeting Service's fallback mode
    processing_mode: Literal["kafka", "http"] = "kafka"
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_request_topic: str = "meeting.events"
    kafka_result_topic: str = "ai.events"
    kafka_consumer_group: str = "ai-service"
    internal_api_token: str = ""

    summary_provider: Literal["mock", "llm"] = "mock"
    llm_api_key: str = ""
    max_retries: int = 3

    @model_validator(mode="after")
    def _check_required_secrets(self) -> Self:
        if self.processing_mode == "http" and not self.internal_api_token:
            raise ValueError("INTERNAL_API_TOKEN is required when PROCESSING_MODE=http")
        if self.summary_provider == "llm" and not self.llm_api_key:
            raise ValueError("LLM_API_KEY is required when SUMMARY_PROVIDER=llm")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
