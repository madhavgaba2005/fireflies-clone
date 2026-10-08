import json
from typing import Any

import httpx
import pytest

from app.config import Settings
from app.events.envelope import EventEnvelope, EventType
from app.events.factory import build_publisher
from app.events.http_publisher import PROCESS_PATH, TOKEN_HEADER, HttpEventPublisher
from app.events.kafka_publisher import KafkaEventPublisher
from app.events.publisher import InMemoryEventPublisher


def make_event(event_type: EventType = EventType.MEETING_CREATED) -> EventEnvelope:
    return EventEnvelope(event_type=event_type, aggregate_id="7", payload={"meeting_id": 7})


async def ignore_result(_event: EventEnvelope) -> None:
    return None


# --- in-memory -------------------------------------------------------------------------------


async def test_in_memory_publisher_records_events() -> None:
    publisher = InMemoryEventPublisher()
    await publisher.start()
    event = make_event()
    await publisher.publish(event)
    await publisher.stop()
    assert publisher.published == [event]


# --- kafka (fake producer; the real broker is covered by tests/kafka) ------------------------


class FakeProducer:
    def __init__(self, bootstrap_servers: str) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.started = False
        self.sent: list[tuple[str, bytes, bytes]] = []

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.started = False

    async def send_and_wait(self, topic: str, value: bytes, key: bytes) -> Any:
        self.sent.append((topic, value, key))


async def test_kafka_publisher_sends_to_topic_keyed_by_meeting() -> None:
    producers: list[FakeProducer] = []

    def factory(servers: str) -> FakeProducer:
        producers.append(FakeProducer(servers))
        return producers[-1]

    publisher = KafkaEventPublisher("broker:9092", "meeting.events", producer_factory=factory)
    await publisher.start()
    event = make_event()
    await publisher.publish(event)

    producer = producers[0]
    assert producer.bootstrap_servers == "broker:9092" and producer.started
    topic, value, key = producer.sent[0]
    assert (topic, key) == ("meeting.events", b"7")
    assert EventEnvelope.from_bytes(value) == event

    await publisher.stop()
    assert not producer.started


async def test_kafka_publisher_refuses_to_publish_before_start() -> None:
    publisher = KafkaEventPublisher("broker:9092", "meeting.events", producer_factory=FakeProducer)
    with pytest.raises(RuntimeError, match="before start"):
        await publisher.publish(make_event())
    await publisher.stop()  # stopping a never-started publisher is a no-op


# --- http fallback -----------------------------------------------------------------------------


async def test_http_publisher_posts_envelope_and_applies_returned_result() -> None:
    request_seen: dict[str, Any] = {}
    result = make_event(EventType.SUMMARY_GENERATED)

    def handler(request: httpx.Request) -> httpx.Response:
        request_seen["path"] = request.url.path
        request_seen["token"] = request.headers[TOKEN_HEADER]
        request_seen["body"] = json.loads(request.content)
        return httpx.Response(200, content=result.to_bytes())

    applied: list[EventEnvelope] = []

    async def on_result(event: EventEnvelope) -> None:
        applied.append(event)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://ai")
    publisher = HttpEventPublisher("http://ai", "s3cret", on_result, client=client)
    await publisher.start()
    event = make_event()
    await publisher.publish(event)
    await publisher.stop()

    assert request_seen["path"] == PROCESS_PATH
    assert request_seen["token"] == "s3cret"
    assert request_seen["body"]["event_id"] == str(event.event_id)
    assert applied == [result]


async def test_http_publisher_raises_on_error_so_the_relay_can_retry() -> None:
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _r: httpx.Response(503)), base_url="http://ai"
    )
    publisher = HttpEventPublisher("http://ai", "t", ignore_result, client=client)
    with pytest.raises(httpx.HTTPStatusError):
        await publisher.publish(make_event())
    await publisher.stop()


async def test_http_publisher_creates_and_closes_its_own_client() -> None:
    publisher = HttpEventPublisher("http://ai", "t", ignore_result)
    with pytest.raises(RuntimeError, match="before start"):
        await publisher.publish(make_event())
    await publisher.start()
    await publisher.stop()


# --- factory -----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("kafka", KafkaEventPublisher),
        ("http", HttpEventPublisher),
        ("inline-test", InMemoryEventPublisher),
    ],
)
def test_factory_selects_publisher_from_processing_mode(mode: str, expected: type) -> None:
    settings = Settings(_env_file=None, processing_mode=mode, internal_api_token="t")  # type: ignore[arg-type]
    assert isinstance(build_publisher(settings, ignore_result), expected)
