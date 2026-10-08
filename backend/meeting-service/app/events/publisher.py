"""The EventPublisher interface and its in-memory implementation.

The outbox relay (Phase 5) depends only on this protocol, so the transport can change
(kafka | http | in-memory) without touching business code.
"""

from collections.abc import Awaitable, Callable
from typing import Protocol

from app.events.envelope import EventEnvelope

# Applies a result event (summary.generated / summary.failed) — used by the HTTP fallback,
# which receives the result in the response instead of from the ai.events topic.
ResultHandler = Callable[[EventEnvelope], Awaitable[None]]


class EventPublisher(Protocol):
    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def publish(self, event: EventEnvelope) -> None: ...


class InMemoryEventPublisher:
    """Records events instead of sending them. Tests only (PROCESSING_MODE=inline-test)."""

    def __init__(self) -> None:
        self.published: list[EventEnvelope] = []

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    async def publish(self, event: EventEnvelope) -> None:
        self.published.append(event)
