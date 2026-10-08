"""Kafka transport (the reference implementation): publishes envelopes keyed by meeting id."""

from typing import Any, Protocol

from aiokafka import AIOKafkaProducer

from app.events.envelope import EventEnvelope


class _Producer(Protocol):
    async def start(self) -> None: ...

    async def stop(self) -> None: ...

    async def send_and_wait(self, topic: str, value: bytes, key: bytes) -> Any: ...


def _default_producer(bootstrap_servers: str) -> _Producer:
    # acks="all" + idempotence: the broker confirms the write and retries can't duplicate it.
    producer: _Producer = AIOKafkaProducer(
        bootstrap_servers=bootstrap_servers, acks="all", enable_idempotence=True
    )
    return producer


class KafkaEventPublisher:
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        producer_factory: Any = _default_producer,
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._producer_factory = producer_factory
        self._producer: _Producer | None = None

    async def start(self) -> None:
        producer = self._producer_factory(self._bootstrap_servers)
        await producer.start()
        self._producer = producer

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None

    async def publish(self, event: EventEnvelope) -> None:
        if self._producer is None:
            raise RuntimeError("KafkaEventPublisher.publish() called before start()")
        # Same key → same partition → events for one meeting are consumed in order.
        await self._producer.send_and_wait(
            self._topic, value=event.to_bytes(), key=event.aggregate_id.encode()
        )
