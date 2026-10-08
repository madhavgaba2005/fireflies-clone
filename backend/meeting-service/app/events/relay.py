"""Transactional-outbox relay: publishes committed outbox rows, oldest first, at least once.

Requests never talk to Kafka. They commit an outbox row with their data; this loop publishes it.
If the broker is down, rows simply wait and are retried with exponential backoff.
"""

import asyncio
import contextlib
import logging

from app.database import Database
from app.events.envelope import EventEnvelope
from app.events.publisher import EventPublisher
from app.models import Meeting, OutboxEvent, ProcessingStatus
from app.models.types import utcnow
from app.repositories.outbox import OutboxRepository

logger = logging.getLogger(__name__)


async def sleep_unless_stopped(stop: asyncio.Event, seconds: float) -> None:
    """Wait `seconds`, but return immediately when shutdown is requested."""
    with contextlib.suppress(TimeoutError):
        await asyncio.wait_for(stop.wait(), timeout=seconds)


class OutboxRelay:
    def __init__(
        self,
        database: Database,
        publisher: EventPublisher,
        *,
        poll_interval: float = 1.0,
        batch_size: int = 20,
        max_backoff: float = 30.0,
    ) -> None:
        self.database = database
        self.publisher = publisher
        self.poll_interval = poll_interval
        self.batch_size = batch_size
        self.max_backoff = max_backoff

    async def run_once(self) -> int:
        """Publish one batch. Stops at the first failure so per-meeting order is preserved.
        Returns the number of events published."""
        rows = await asyncio.to_thread(self._load_batch)
        published = 0
        for event_id, envelope in rows:
            try:
                await self.publisher.publish(EventEnvelope.model_validate_json(envelope))
            except Exception as exc:  # broker down, timeout, HTTP error … — retry later
                logger.warning("Publishing %s failed: %s", event_id, exc)
                await asyncio.to_thread(
                    self._record_failure, event_id, f"{type(exc).__name__}: {exc}"
                )
                raise
            await asyncio.to_thread(self._record_success, event_id)
            published += 1
        return published

    async def run_forever(self, stop: asyncio.Event) -> None:
        backoff = self.poll_interval
        started = False
        while not stop.is_set():
            try:
                if not started:
                    await self.publisher.start()
                    started = True
                    logger.info("Outbox relay connected")
                published = await self.run_once()
                backoff = self.poll_interval
                delay = 0.0 if published == self.batch_size else self.poll_interval
            except Exception:
                logger.exception("Outbox relay error; retrying in %.1fs", backoff)
                delay = backoff
                backoff = min(backoff * 2, self.max_backoff)
            await sleep_unless_stopped(stop, delay)
        if started:
            await self.publisher.stop()

    # --- database work (runs in a worker thread; SQLAlchemy sessions here are synchronous) -------

    def _load_batch(self) -> list[tuple[str, str]]:
        with self.database.session_factory() as session:
            rows = OutboxRepository(session).unpublished(self.batch_size)
            return [(row.id, row.envelope) for row in rows]

    def _record_success(self, event_id: str) -> None:
        with self.database.session_factory() as session:
            row = session.get(OutboxEvent, event_id)
            if row is None:
                return
            OutboxRepository(session).mark_published(row, utcnow())
            meeting = session.get(Meeting, int(row.aggregate_id))
            # Only pending → processing: in HTTP mode the result may already have been applied.
            if meeting is not None and meeting.processing_status == ProcessingStatus.PENDING:
                meeting.processing_status = ProcessingStatus.PROCESSING
            session.commit()

    def _record_failure(self, event_id: str, error: str) -> None:
        with self.database.session_factory() as session:
            row = session.get(OutboxEvent, event_id)
            if row is not None:
                OutboxRepository(session).mark_failed(row, error)
                session.commit()
