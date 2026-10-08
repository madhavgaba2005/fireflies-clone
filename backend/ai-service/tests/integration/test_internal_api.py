"""POST /internal/process — the HTTP fallback transport."""

from fastapi.testclient import TestClient

from app.events.envelope import EventEnvelope, EventType
from tests.conftest import request_event

JSON = {"Content-Type": "application/json"}  # what HttpEventPublisher sends
HEADERS = {**JSON, "X-Internal-Token": "test-token"}


def test_returns_the_result_envelope(http_client: TestClient) -> None:
    response = http_client.post(
        "/internal/process", content=request_event().to_bytes(), headers=HEADERS
    )
    assert response.status_code == 200
    result = EventEnvelope.model_validate(response.json())
    assert result.event_type == EventType.SUMMARY_GENERATED and result.aggregate_id == "42"


def test_rejects_missing_or_wrong_token(http_client: TestClient) -> None:
    body = request_event().to_bytes()
    assert http_client.post("/internal/process", content=body, headers=JSON).status_code == 401
    wrong = {**JSON, "X-Internal-Token": "nope"}
    assert http_client.post("/internal/process", content=body, headers=wrong).status_code == 401


def test_rejects_result_events_and_malformed_envelopes(http_client: TestClient) -> None:
    result = EventEnvelope(event_type=EventType.SUMMARY_GENERATED, aggregate_id="1", payload={})
    response = http_client.post("/internal/process", content=result.to_bytes(), headers=HEADERS)
    assert response.status_code == 422
    assert (
        http_client.post("/internal/process", json={"nope": 1}, headers=HEADERS).status_code == 422
    )


def test_endpoint_does_not_exist_in_kafka_mode(client: TestClient) -> None:
    response = client.post("/internal/process", content=request_event().to_bytes(), headers=HEADERS)
    assert response.status_code == 404
