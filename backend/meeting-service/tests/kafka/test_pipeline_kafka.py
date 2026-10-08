"""Full asynchronous pipeline through a real broker and the real AI service.

Needs:  docker compose up -d --wait kafka ai-service      Run:  pytest -m kafka
API → outbox → relay → Kafka (meeting.events) → AI service → Kafka (ai.events) → consumer → SQLite
"""

import os
import time
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

pytestmark = pytest.mark.kafka

BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TIMEOUT_SECONDS = 90

TRANSCRIPT = """[00:00] Priya Sharma: Let's finalize the pricing launch plan for next month.
[00:12] Arjun Mehta: The checkout integration still fails for annual plans.
[00:25] Priya Sharma: Arjun, can you fix the annual checkout before Friday?
[00:34] Arjun Mehta: Yes. I'll fix the annual plan checkout and add regression tests.
[00:46] Sarah Chen: I'll share the pricing page illustrations with the team tomorrow."""


def test_meeting_summary_is_generated_through_kafka(tmp_path: Path) -> None:
    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'kafka.db'}",
        processing_mode="kafka",
        kafka_bootstrap_servers=BOOTSTRAP,
        kafka_consumer_group=f"meeting-service-test-{uuid4().hex[:8]}",
        outbox_poll_interval=0.2,
    )
    with TestClient(create_app(settings)) as client:
        created = client.post(
            "/api/meetings",
            json={
                "title": "Pricing launch",
                "meeting_date": "2026-10-08T09:00:00Z",
                "transcript_text": TRANSCRIPT,
            },
        ).json()
        assert created["processing_status"] == "pending"

        seen = {"pending"}
        deadline = time.monotonic() + TIMEOUT_SECONDS
        meeting = created
        while time.monotonic() < deadline:
            meeting = client.get(f"/api/meetings/{created['id']}").json()
            seen.add(meeting["processing_status"])
            if meeting["processing_status"] in {"completed", "failed"}:
                break
            time.sleep(0.25)

        assert meeting["processing_status"] == "completed", meeting
        summary = client.get(f"/api/meetings/{created['id']}/summary").json()
        assert summary["provider"] == "mock" and summary["topics"] and summary["keywords"]
        items = client.get(f"/api/meetings/{created['id']}/action-items").json()
        assert {i["assignee"]["name"] for i in items if i["assignee"]} >= {"Arjun Mehta"}
        assert all(i["source"] == "ai" for i in items)
