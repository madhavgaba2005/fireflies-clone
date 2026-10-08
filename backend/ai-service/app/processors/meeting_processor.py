"""request envelope → provider (with retries) → result envelope.

The one place processing logic lives: the Kafka consumer and the HTTP fallback both call it.
It never raises — every request produces summary.generated or summary.failed, so a bad
message can't block a Kafka partition.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import ValidationError

from app.events.envelope import EventEnvelope, EventType
from app.events.payloads import ProcessingRequestPayload, SummaryFailedPayload
from app.providers.base import ProviderError, SummaryProvider

logger = logging.getLogger(__name__)

REQUEST_EVENTS = frozenset(
    {EventType.MEETING_CREATED, EventType.TRANSCRIPT_UPDATED, EventType.SUMMARY_REQUESTED}
)


class MeetingProcessor:
    def __init__(
        self,
        provider: SummaryProvider,
        *,
        max_retries: int = 3,
        backoff_seconds: float = 1.0,
        sleep: Callable[[float], Awaitable[Any]] = asyncio.sleep,
    ) -> None:
        self.provider = provider
        self.max_retries = max(1, max_retries)
        self.backoff_seconds = backoff_seconds
        self.sleep = sleep

    async def process(self, event: EventEnvelope) -> EventEnvelope:
        try:
            request = ProcessingRequestPayload.model_validate(event.payload)
        except ValidationError:
            logger.error("Invalid processing request %s", event.event_id)
            revision = event.payload.get("transcript_revision")
            return self._failed(
                event,
                revision if isinstance(revision, int) else -1,
                "Invalid processing request",
                0,
            )

        reason = "Unknown error"
        for attempt in range(1, self.max_retries + 1):
            try:
                # Providers are synchronous (an LLM client would block on I/O): keep the loop free.
                result = await asyncio.to_thread(self.provider.generate, request)
            except ProviderError as exc:
                reason = str(exc)
                if not exc.retryable:
                    return self._failed(event, request.transcript_revision, reason, attempt)
            except Exception as exc:
                logger.exception("Provider failed for meeting %s", request.meeting_id)
                reason = f"{type(exc).__name__}: {exc}"
            else:
                logger.info("Generated summary for meeting %s", request.meeting_id)
                return EventEnvelope(
                    event_type=EventType.SUMMARY_GENERATED,
                    aggregate_id=event.aggregate_id,
                    payload=result.model_dump(),
                )
            if attempt < self.max_retries:
                await self.sleep(self.backoff_seconds * 2 ** (attempt - 1))
        return self._failed(event, request.transcript_revision, reason, self.max_retries)

    @staticmethod
    def _failed(event: EventEnvelope, revision: int, reason: str, attempts: int) -> EventEnvelope:
        payload = SummaryFailedPayload(
            meeting_id=int(event.aggregate_id) if event.aggregate_id.isdigit() else 0,
            transcript_revision=revision,
            reason=reason[:500],
            attempts=attempts,
        )
        return EventEnvelope(
            event_type=EventType.SUMMARY_FAILED,
            aggregate_id=event.aggregate_id,
            payload=payload.model_dump(),
        )
