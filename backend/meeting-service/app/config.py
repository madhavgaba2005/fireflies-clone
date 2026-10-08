"""Service configuration, read from environment variables (and an optional local .env file)."""

from functools import lru_cache
from typing import Literal, Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# kafka       — real broker (reference implementation, used locally and in CI)
# http        — documented fallback for hosts that cannot run a broker
# inline-test — in-memory publisher for automated tests only
ProcessingMode = Literal["kafka", "http", "inline-test"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Meeting Service"
    environment: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"

    database_url: str = "sqlite:///./data/meetings.db"
    run_migrations_on_startup: bool = True
    # Load the demo meetings when the database is empty (handy for fresh deployments).
    seed_on_startup: bool = False
    # Comma-separated list, e.g. "http://localhost:3000,https://app.example.com"
    cors_origins: str = "http://localhost:3000"

    processing_mode: ProcessingMode = "kafka"
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_request_topic: str = "meeting.events"
    kafka_result_topic: str = "ai.events"
    kafka_consumer_group: str = "meeting-service"
    outbox_poll_interval: float = 1.0
    ai_service_url: str = "http://localhost:8001"
    internal_api_token: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def _require_token_in_http_mode(self) -> Self:
        if self.processing_mode == "http" and not self.internal_api_token:
            raise ValueError("INTERNAL_API_TOKEN is required when PROCESSING_MODE=http")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
