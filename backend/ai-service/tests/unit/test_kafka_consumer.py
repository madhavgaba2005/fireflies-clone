"""The Kafka loop with fake clients (the real broker path is covered by the Kafka CI job)."""

import asyncio
from dataclasses import dataclass
from typing import Any

from app.consumers.kafka_consumer import RequestConsumer
from app.events.envelope import EventEnvelope, EventType
from app.processors.meeting_processor import MeetingProcessor
from app.providers.mock import MockSummaryProvider
from tests.conftest import request_event


@dataclass
class Message:
    value: bytes


class FakeProducer:
    def __init__(self, servers: str = "") -> None:
        self.sent: list[tuple[str, bytes, bytes]] = []
        self.stopped = False

    async def start(self) -> None: ...

    async def stop(self) -> None:
        self.stopped = True

    async def send_and_wait(self, topic: str, value: bytes, key: bytes) -> None:
        self.sent.append((topic, value, key))


class FakeConsumer:
    """Delivers one batch, then signals the loop to stop."""

    def __init__(self, batch: list[bytes], stop: asyncio.Event, fail_start: bool = False) -> None:
        self.batch = batch
        self.stop_event = stop
        self.fail_start = fail_start
        self.commits = 0
        self.stopped = False

    async def start(self) -> None:
        if self.fail_start:
            raise ConnectionError("broker unavailable")

    async def stop(self) -> None:
        self.stopped = True

    async def getmany(self, timeout_ms: int) -> dict[str, list[Message]]:
        batch, self.batch = self.batch, []
        if not batch:
            self.stop_event.set()
            return {}
        return {"partition-0": [Message(raw) for raw in batch]}

    async def commit(self) -> None:
        self.commits += 1


def make_consumer(consumers: list[Any], producer: FakeProducer) -> RequestConsumer:
    processor = MeetingProcessor(MockSummaryProvider())
    queue = iter(consumers)
    return RequestConsumer(
        processor,
        "broker:9092",
        "meeting.events",
        "ai.events",
        "ai-service",
        consumer_factory=lambda *_: next(queue),
        producer_factory=lambda _servers: producer,
        max_backoff=0.01,
    )


async def test_requests_are_processed_published_keyed_and_committed() -> None:
    stop = asyncio.Event()
    ignored = EventEnvelope(event_type=EventType.SUMMARY_GENERATED, aggregate_id="9", payload={})
    consumer = FakeConsumer([request_event().to_bytes(), b"not json", ignored.to_bytes()], stop)
    producer = FakeProducer()
    await make_consumer([consumer], producer).run_forever(stop)

    assert len(producer.sent) == 1  # malformed and non-request events are skipped
    topic, value, key = producer.sent[0]
    assert (topic, key) == ("ai.events", b"42")
    assert EventEnvelope.from_bytes(value).event_type == EventType.SUMMARY_GENERATED
    assert consumer.commits == 1 and consumer.stopped and producer.stopped


async def test_reconnects_after_connection_failure() -> None:
    stop = asyncio.Event()
    broken = FakeConsumer([], stop, fail_start=True)
    healthy = FakeConsumer([request_event().to_bytes()], stop)
    producer = FakeProducer()
    await make_consumer([broken, healthy], producer).run_forever(stop)
    assert broken.stopped and len(producer.sent) == 1


async def test_handle_reports_outcomes() -> None:
    consumer = make_consumer([], FakeProducer())
    producer = FakeProducer()
    assert await consumer.handle(b"{", producer) == "malformed"
    assert await consumer.handle(request_event().to_bytes(), producer) == "summary.generated"
