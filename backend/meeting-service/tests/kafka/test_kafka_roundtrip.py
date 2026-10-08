"""Real-broker check of the Kafka transport. Run: pytest -m kafka (needs the compose broker)."""

import os
from uuid import uuid4

import pytest
from aiokafka import AIOKafkaConsumer

from app.events.envelope import EventEnvelope, EventType
from app.events.kafka_publisher import KafkaEventPublisher

pytestmark = pytest.mark.kafka

BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


async def test_published_envelope_is_consumed_unchanged_with_meeting_key() -> None:
    topic = f"test.meeting.events.{uuid4().hex[:8]}"  # isolated topic per run (auto-created)
    event = EventEnvelope(
        event_type=EventType.MEETING_CREATED, aggregate_id="42", payload={"meeting_id": 42}
    )

    publisher = KafkaEventPublisher(BOOTSTRAP, topic)
    await publisher.start()
    try:
        await publisher.publish(event)
    finally:
        await publisher.stop()

    consumer = AIOKafkaConsumer(
        topic, bootstrap_servers=BOOTSTRAP, auto_offset_reset="earliest", group_id=None
    )
    await consumer.start()
    try:
        message = await consumer.getone()
    finally:
        await consumer.stop()

    assert message.key == b"42"
    assert EventEnvelope.from_bytes(message.value) == event
