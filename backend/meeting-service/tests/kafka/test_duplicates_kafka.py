"""At-least-once delivery through a real broker: a result event delivered twice is applied once.

Needs:  docker compose up -d --wait kafka      Run:  pytest -m kafka
Topics are unique per run, so no other producer or consumer touches these events.
"""

import asyncio
import os
import sqlite3
import time
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.events.envelope import EventEnvelope, EventType
from app.events.kafka_publisher import KafkaEventPublisher
from app.main import create_app

pytestmark = pytest.mark.kafka

BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TIMEOUT_SECONDS = 60

TRANSCRIPT = """[00:00] Priya Sharma: Let's review the launch.
[00:10] Arjun Mehta: I'll fix the checkout bug before Friday."""


async def publish(topic: str, *events: EventEnvelope) -> None:
    publisher = KafkaEventPublisher(BOOTSTRAP, topic)
    await publisher.start()
    try:
        for event in events:
            await publisher.publish(event)
    finally:
        await publisher.stop()


def wait_for(condition, what: str) -> None:  # type: ignore[no-untyped-def]
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if condition():
            return
        time.sleep(0.25)
    raise AssertionError(f"timed out waiting for {what}")


def test_duplicate_result_event_is_applied_exactly_once(tmp_path: Path) -> None:
    run = uuid4().hex[:8]
    db_file = tmp_path / "dup.db"
    result_topic = f"test.ai.events.{run}"
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        database_url=f"sqlite:///{db_file}",
        processing_mode="kafka",
        kafka_bootstrap_servers=BOOTSTRAP,
        kafka_request_topic=f"test.meeting.events.{run}",
        kafka_result_topic=result_topic,
        kafka_consumer_group=f"meeting-service-dup-{run}",
        outbox_poll_interval=0.2,
    )
    with TestClient(create_app(settings)) as client:
        meeting = client.post(
            "/api/meetings",
            json={
                "title": "Duplicates",
                "meeting_date": "2026-10-08T09:00:00Z",
                "transcript_text": TRANSCRIPT,
            },
        ).json()
        meeting_id = meeting["id"]
        wait_for(  # the relay published the request to Kafka
            lambda: (
                client.get(f"/api/meetings/{meeting_id}").json()["processing_status"]
                == "processing"
            ),
            "the request to be published",
        )

        detail = client.get(f"/api/meetings/{meeting_id}").json()
        speaker_id = next(p["id"] for p in detail["participants"] if p["name"] == "Arjun Mehta")
        result = EventEnvelope(
            event_type=EventType.SUMMARY_GENERATED,
            aggregate_id=str(meeting_id),
            payload={
                "meeting_id": meeting_id,
                "transcript_revision": detail["transcript_revision"],
                "provider": "mock",
                "overview": "Launch review.",
                "keywords": ["Launch"],
                "topics": [{"title": "Checkout", "summary": "Bug fix", "start_ms": 10_000}],
                "action_items": [
                    {
                        "title": "Fix the checkout bug",
                        "assignee_speaker_id": speaker_id,
                        "start_ms": 10_000,
                    }
                ],
            },
        )
        # Same key (meeting id) → same partition → consumed in order after both copies.
        sentinel = EventEnvelope(
            event_type=EventType.SUMMARY_FAILED,
            aggregate_id=str(meeting_id),
            payload={
                "meeting_id": meeting_id,
                "transcript_revision": 0,
                "reason": "x",
                "attempts": 1,
            },
        )
        asyncio.run(publish(result_topic, result, result, sentinel))

        def outcomes() -> dict[str, str]:
            with sqlite3.connect(db_file) as connection:
                return dict(connection.execute("SELECT event_id, outcome FROM processed_events"))

        wait_for(lambda: str(sentinel.event_id) in outcomes(), "the sentinel to be consumed")

        assert outcomes() == {str(result.event_id): "applied", str(sentinel.event_id): "stale"}
        assert client.get(f"/api/meetings/{meeting_id}").json()["processing_status"] == "completed"
        summary = client.get(f"/api/meetings/{meeting_id}/summary").json()
        assert [t["title"] for t in summary["topics"]] == ["Checkout"]  # not doubled
        items = client.get(f"/api/meetings/{meeting_id}/action-items").json()
        assert [i["title"] for i in items] == ["Fix the checkout bug"]
