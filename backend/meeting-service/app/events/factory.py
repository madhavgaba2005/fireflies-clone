"""Chooses the EventPublisher implementation from PROCESSING_MODE."""

from app.config import Settings
from app.events.http_publisher import HttpEventPublisher
from app.events.kafka_publisher import KafkaEventPublisher
from app.events.publisher import EventPublisher, InMemoryEventPublisher, ResultHandler


def build_publisher(settings: Settings, on_result: ResultHandler) -> EventPublisher:
    if settings.processing_mode == "kafka":
        return KafkaEventPublisher(settings.kafka_bootstrap_servers, settings.kafka_request_topic)
    if settings.processing_mode == "http":
        return HttpEventPublisher(settings.ai_service_url, settings.internal_api_token, on_result)
    return InMemoryEventPublisher()
