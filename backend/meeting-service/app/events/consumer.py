"""Consumes AI results from Kafka (`ai.events`) and applies them through SummaryService.

Offsets are committed only after the result is stored, so a crash means re-delivery, never loss;
re-delivery is harmless because SummaryService.apply_result is idempotent.
"""

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from aiokafka import AIOKafkaConsumer
from pydantic import ValidationError

from app.database import Database
from app.events.envelope import EventEnvelope
from app.events.relay import sleep_unless_stopped
from app.services.summaries import SummaryService

logger = logging.getLogger(__name__)

APPLY_ATTEMPTS = 3


def _default_consumer(topic: str, bootstrap_servers: str, group_id: str) -> Any:
    return AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
        enable_auto_commit=False,  # commit manually, after the database commit
        auto_offset_reset="earliest",  # a new consumer group must not skip results already sent
    )


def apply_result_in_new_session(database: Database, event: EventEnvelope) -> str:
    with database.session_factory() as session:
        return SummaryService(session).apply_result(event)


async def handle_message(database: Database, raw: bytes) -> str:
    """Parse and apply one message. Malformed messages are logged and skipped (a production
    system would route them to a dead-letter topic)."""
    try:
        event = EventEnvelope.from_bytes(raw)
    except ValidationError:
        logger.error("Skipping malformed event: %r", raw[:200])
        return "malformed"
    for attempt in range(1, APPLY_ATTEMPTS + 1):
        try:
            return await asyncio.to_thread(apply_result_in_new_session, database, event)
        except Exception:
            logger.exception("Applying %s failed (attempt %d)", event.event_id, attempt)
            await asyncio.sleep(0.5 * attempt)
    return "gave_up"


class ResultConsumer:
    def __init__(
        self,
        database: Database,
        bootstrap_servers: str,
        topic: str,
        group_id: str = "meeting-service",
        consumer_factory: Callable[[str, str, str], Any] = _default_consumer,
        max_backoff: float = 30.0,
    ) -> None:
        self.database = database
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self.consumer_factory = consumer_factory
        self.max_backoff = max_backoff

    async def run_forever(self, stop: asyncio.Event) -> None:
        backoff = 1.0
        while not stop.is_set():
            consumer = self.consumer_factory(self.topic, self.bootstrap_servers, self.group_id)
            try:
                await consumer.start()
                logger.info("Result consumer subscribed to %s", self.topic)
                backoff = 1.0
                await self._consume(consumer, stop)
            except Exception:
                logger.exception("Result consumer error; reconnecting in %.0fs", backoff)
                await sleep_unless_stopped(stop, backoff)
                backoff = min(backoff * 2, self.max_backoff)
            finally:
                await consumer.stop()

    async def _consume(self, consumer: Any, stop: asyncio.Event) -> None:
        while not stop.is_set():
            batches = await consumer.getmany(timeout_ms=1000)
            for messages in batches.values():
                for message in messages:
                    await handle_message(self.database, message.value)
            if batches:
                await consumer.commit()
