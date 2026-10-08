from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.events.envelope import EventEnvelope, EventType
from app.main import create_app

LINES = [
    (
        "Priya Sharma",
        "Morning everyone. Today we review the pricing launch and the onboarding checklist.",
    ),
    (
        "Arjun Mehta",
        "The pricing page is ready, but the checkout integration still fails for annual plans.",
    ),
    ("Priya Sharma", "Arjun, can you fix the checkout integration before Friday?"),
    ("Arjun Mehta", "Yes. I'll fix the annual plan checkout and add tests for it."),
    ("Sarah Chen", "The onboarding checklist needs new illustrations for the pricing step."),
    ("Sarah Chen", "I'll share the onboarding illustrations with the team tomorrow."),
    ("Priya Sharma", "We need to announce the pricing change by next week."),
    ("Arjun Mehta", "Sure."),
]
PEOPLE = {"Priya Sharma": 1, "Arjun Mehta": 2, "Sarah Chen": 3}


def request_payload(lines: list[tuple[str, str]] = LINES, revision: int = 3) -> dict[str, Any]:
    segments = [
        {
            "speaker_id": PEOPLE[speaker],
            "speaker": speaker,
            "start_ms": i * 10_000,
            "end_ms": i * 10_000 + 9000,
            "text": text,
        }
        for i, (speaker, text) in enumerate(lines)
    ]
    return {
        "meeting_id": 42,
        "transcript_revision": revision,
        "title": "Pricing launch sync",
        "participants": [{"id": pid, "name": name} for name, pid in PEOPLE.items()],
        "segments": segments,
    }


def request_event(payload: dict[str, Any] | None = None) -> EventEnvelope:
    return EventEnvelope(
        event_type=EventType.MEETING_CREATED,
        aggregate_id="42",
        payload=request_payload() if payload is None else payload,
    )


@pytest.fixture
def settings() -> Settings:
    """Default (kafka) settings — used without starting the lifespan, so no broker is needed."""
    return Settings(environment="test", _env_file=None)  # type: ignore[call-arg]


@pytest.fixture
def client(settings: Settings) -> TestClient:
    # No `with`: the lifespan (Kafka consumer) doesn't start; the tests only need the routes.
    return TestClient(create_app(settings))


@pytest.fixture
def http_client() -> Iterator[TestClient]:
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        processing_mode="http",
        internal_api_token="test-token",
        retry_backoff_seconds=0,
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client
