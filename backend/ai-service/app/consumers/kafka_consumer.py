"""Kafka loop: consume meeting.events → process → produce the result to ai.events → commit.

The offset is committed only after the result is published, so a crash re-processes the request
(at-least-once). That's safe: the Meeting Service de-duplicates results.
"""

import asyncio
import contextlib
import logging
from collections.abc import Callable
from typing import Any

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from pydantic import ValidationError

from app.events.envelope import EventEnvelope
from app.processors.meeting_processor import REQUEST_EVENTS, MeetingProcessor

logger = logging.getLogger(__name__)


def _default_consumer(topic: str, bootstrap_servers: str, group_id: str) -> Any:
    return AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
    )


def _default_producer(bootstrap_servers: str) -> Any:
    return AIOKafkaProducer(
        bootstrap_servers=bootstrap_servers, acks="all", enable_idempotence=True
    )


async def sleep_unless_stopped(stop: asyncio.Event, seconds: float) -> None:
    with contextlib.suppress(TimeoutError):
        await asyncio.wait_for(stop.wait(), timeout=seconds)


class RequestConsumer:
    def __init__(
        self,
        processor: MeetingProcessor,
        bootstrap_servers: str,
        request_topic: str,
        result_topic: str,
        group_id: str,
        consumer_factory: Callable[[str, str, str], Any] = _default_consumer,
        producer_factory: Callable[[str], Any] = _default_producer,
        max_backoff: float = 30.0,
    ) -> None:
        self.processor = processor
        self.bootstrap_servers = bootstrap_servers
        self.request_topic = request_topic
        self.result_topic = result_topic
        self.group_id = group_id
        self.consumer_factory = consumer_factory
        self.producer_factory = producer_factory
        self.max_backoff = max_backoff

    async def handle(self, raw: bytes, producer: Any) -> str:
        try:
            event = EventEnvelope.from_bytes(raw)
        except ValidationError:
            logger.error("Skipping malformed event: %r", raw[:200])
            return "malformed"
        if event.event_type not in REQUEST_EVENTS:
            return "ignored"
        result = await self.processor.process(event)
        await producer.send_and_wait(
            self.result_topic, value=result.to_bytes(), key=result.aggregate_id.encode()
        )
        return result.event_type.value

    async def run_forever(self, stop: asyncio.Event) -> None:
        backoff = 1.0
        while not stop.is_set():
            consumer = self.consumer_factory(
                self.request_topic, self.bootstrap_servers, self.group_id
            )
            producer = self.producer_factory(self.bootstrap_servers)
            try:
                await producer.start()
                await consumer.start()
                logger.info("Consuming %s", self.request_topic)
                backoff = 1.0
                while not stop.is_set():
                    batches = await consumer.getmany(timeout_ms=1000)
                    for messages in batches.values():
                        for message in messages:
                            await self.handle(message.value, producer)
                    if batches:
                        await consumer.commit()
            except Exception:
                logger.exception("Kafka consumer error; reconnecting in %.0fs", backoff)
                await sleep_unless_stopped(stop, backoff)
                backoff = min(backoff * 2, self.max_backoff)
            finally:
                await consumer.stop()
                await producer.stop()
