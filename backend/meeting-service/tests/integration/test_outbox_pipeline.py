"""Outbox relay, result consumer and the whole asynchronous pipeline, in-process.

API → outbox row → relay → publisher → (fake) AI → result → SummaryService → database.
"""

import asyncio
from dataclasses import dataclass
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.database import Database
from app.events.consumer import ResultConsumer, apply_result_in_new_session, handle_message
from app.events.envelope import EventEnvelope
from app.events.http_publisher import HttpEventPublisher
from app.events.publisher import InMemoryEventPublisher
from app.events.relay import OutboxRelay
from app.main import background_workers
from app.models import OutboxEvent
from tests.pipeline_helpers import fake_ai, generated

TRANSCRIPT = "[00:00] Priya: Kickoff.\n[00:10] Sam: I'll send the agenda by Friday."


def create_meeting(client: TestClient, title: str = "Kickoff") -> int:
    body = {"title": title, "meeting_date": "2026-10-08T09:00:00Z", "transcript_text": TRANSCRIPT}
    return int(client.post("/api/meetings", json=body).json()["id"])


def status(client: TestClient, meeting_id: int) -> str:
    return str(client.get(f"/api/meetings/{meeting_id}").json()["processing_status"])


class FailingPublisher(InMemoryEventPublisher):
    def __init__(self, failures: int) -> None:
        super().__init__()
        self.failures = failures

    async def publish(self, event: EventEnvelope) -> None:
        if self.failures:
            self.failures -= 1
            raise ConnectionError("broker unavailable")
        await super().publish(event)


# --- relay -----------------------------------------------------------------------------------


async def test_relay_publishes_in_order_and_marks_processing(
    app: FastAPI, client: TestClient, session: Session
) -> None:
    first, second = create_meeting(client, "First"), create_meeting(client, "Second")
    assert status(client, first) == "pending"
    publisher = InMemoryEventPublisher()
    relay = OutboxRelay(app.state.db, publisher)

    assert await relay.run_once() == 2
    assert [e.aggregate_id for e in publisher.published] == [str(first), str(second)]
    assert status(client, first) == "processing"
    assert all(
        row.published_at is not None and row.attempts == 1
        for row in session.scalars(select(OutboxEvent))
    )
    assert await relay.run_once() == 0  # nothing is published twice


async def test_failed_publish_keeps_the_row_for_retry(
    app: FastAPI, client: TestClient, session: Session
) -> None:
    meeting = create_meeting(client)
    relay = OutboxRelay(app.state.db, FailingPublisher(failures=1))
    with pytest.raises(ConnectionError):
        await relay.run_once()
    row = session.scalars(select(OutboxEvent)).one()
    assert row.published_at is None and row.attempts == 1
    assert "broker unavailable" in (row.last_error or "")
    assert status(client, meeting) == "pending"  # still queued, will be retried

    assert await relay.run_once() == 1
    session.expire_all()
    assert row.published_at is not None and row.last_error is None
    assert status(client, meeting) == "processing"


async def test_run_forever_retries_with_backoff_then_stops(
    app: FastAPI, client: TestClient
) -> None:
    meeting = create_meeting(client)
    publisher = FailingPublisher(failures=2)
    relay = OutboxRelay(app.state.db, publisher, poll_interval=0.01, max_backoff=0.02)
    stop = asyncio.Event()
    task = asyncio.create_task(relay.run_forever(stop))
    for _ in range(200):
        if publisher.published:
            break
        await asyncio.sleep(0.01)
    stop.set()
    await asyncio.wait_for(task, timeout=2)
    assert [e.aggregate_id for e in publisher.published] == [str(meeting)]


async def test_result_already_applied_is_not_overwritten_by_processing(
    app: FastAPI, client: TestClient
) -> None:
    """HTTP mode applies the result *during* publish; the relay must not then set 'processing'."""
    meeting = create_meeting(client)
    database: Database = app.state.db

    class AnsweringPublisher(InMemoryEventPublisher):
        async def publish(self, event: EventEnvelope) -> None:
            await asyncio.to_thread(apply_result_in_new_session, database, fake_ai(event))

    await OutboxRelay(database, AnsweringPublisher()).run_once()
    assert status(client, meeting) == "completed"


# --- full pipeline over the HTTP fallback transport --------------------------------------------


async def test_http_fallback_pipeline_end_to_end(app: FastAPI, client: TestClient) -> None:
    meeting = create_meeting(client)
    database: Database = app.state.db
    seen_tokens: list[str] = []

    def ai_service(request: httpx.Request) -> httpx.Response:
        seen_tokens.append(request.headers["X-Internal-Token"])
        return httpx.Response(
            200, content=fake_ai(EventEnvelope.from_bytes(request.content)).to_bytes()
        )

    async def on_result(event: EventEnvelope) -> None:
        await asyncio.to_thread(apply_result_in_new_session, database, event)

    publisher = HttpEventPublisher(
        "http://ai",
        "secret",
        on_result,
        client=httpx.AsyncClient(transport=httpx.MockTransport(ai_service), base_url="http://ai"),
    )
    assert await OutboxRelay(database, publisher).run_once() == 1
    await publisher.stop()

    assert seen_tokens == ["secret"]
    assert status(client, meeting) == "completed"
    items = client.get(f"/api/meetings/{meeting}/action-items").json()
    assert (
        items[0]["title"] == "Follow up with the team" and items[0]["assignee"]["name"] == "Priya"
    )


# --- result consumer -------------------------------------------------------------------------


@dataclass
class Message:
    value: bytes


class FakeKafkaConsumer:
    def __init__(self, batch: list[bytes], stop: asyncio.Event, fail_start: bool = False) -> None:
        self.batch, self.stop_event, self.fail_start = batch, stop, fail_start
        self.commits = 0
        self.stopped = False

    async def start(self) -> None:
        if self.fail_start:
            raise ConnectionError("no broker")

    async def stop(self) -> None:
        self.stopped = True

    async def getmany(self, timeout_ms: int) -> dict[str, list[Message]]:
        batch, self.batch = self.batch, []
        if not batch:
            self.stop_event.set()
            return {}
        return {"tp": [Message(raw) for raw in batch]}

    async def commit(self) -> None:
        self.commits += 1


async def test_consumer_applies_results_and_commits_after_storing(
    app: FastAPI, client: TestClient
) -> None:
    meeting = create_meeting(client)
    stop = asyncio.Event()
    result = generated(meeting).to_bytes()
    broken = FakeKafkaConsumer([], stop, fail_start=True)
    healthy = FakeKafkaConsumer([result, b"garbage", result], stop)  # duplicate on purpose
    consumers = iter([broken, healthy])
    consumer = ResultConsumer(
        app.state.db,
        "broker",
        "ai.events",
        consumer_factory=lambda *_: next(consumers),
        max_backoff=0.01,
    )
    await consumer.run_forever(stop)

    assert broken.stopped and healthy.commits == 1
    assert status(client, meeting) == "completed"
    assert len(client.get(f"/api/meetings/{meeting}/action-items").json()) == 1  # applied once


async def test_handle_message_outcomes(app: FastAPI, client: TestClient) -> None:
    meeting = create_meeting(client)
    assert await handle_message(app.state.db, b"{not json") == "malformed"
    assert await handle_message(app.state.db, generated(meeting).to_bytes()) == "applied"


async def test_handle_message_gives_up_after_repeated_database_errors(
    app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(*_: Any) -> str:
        raise RuntimeError("database is locked")

    monkeypatch.setattr("app.events.consumer.apply_result_in_new_session", broken)
    real_sleep = asyncio.sleep
    monkeypatch.setattr("app.events.consumer.asyncio.sleep", lambda _s: real_sleep(0))
    assert await handle_message(app.state.db, generated(1).to_bytes()) == "gave_up"


# --- lifespan wiring -------------------------------------------------------------------------


@pytest.mark.parametrize(("mode", "count"), [("inline-test", 0), ("http", 1), ("kafka", 2)])
def test_background_workers_per_processing_mode(app: FastAPI, mode: str, count: int) -> None:
    settings = Settings(_env_file=None, processing_mode=mode, internal_api_token="t")  # type: ignore[arg-type]
    workers = background_workers(settings, app.state.db, asyncio.Event())
    assert len(workers) == count
    for worker in workers:
        worker.close()  # never awaited in this test


def test_app_with_background_workers_starts_and_stops(tmp_path: Any) -> None:
    from app.main import create_app

    settings = Settings(  # type: ignore[call-arg]
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'k.db'}",
        processing_mode="kafka",
        kafka_bootstrap_servers="127.0.0.1:1",  # unreachable: workers keep retrying quietly
    )
    with TestClient(create_app(settings)) as kafka_client:
        assert kafka_client.get("/health/ready").status_code == 200
