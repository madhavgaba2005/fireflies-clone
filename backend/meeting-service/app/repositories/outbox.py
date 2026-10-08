from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.events.envelope import EventEnvelope
from app.models import OutboxEvent, ProcessedEvent


class OutboxRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, event: EventEnvelope) -> OutboxEvent:
        """Called inside the same transaction as the change the event describes."""
        row = OutboxEvent(
            id=str(event.event_id),
            event_type=event.event_type.value,
            aggregate_id=event.aggregate_id,
            envelope=event.model_dump_json(),
        )
        self.session.add(row)
        return row

    def unpublished(self, limit: int) -> list[OutboxEvent]:
        return list(
            self.session.scalars(
                select(OutboxEvent)
                .where(OutboxEvent.published_at.is_(None))
                .order_by(OutboxEvent.created_at, OutboxEvent.id)
                .limit(limit)
            )
        )

    def get(self, event_id: str) -> OutboxEvent | None:
        return self.session.get(OutboxEvent, event_id)

    def mark_published(self, row: OutboxEvent, at: datetime) -> None:
        row.published_at = at
        row.attempts += 1
        row.last_error = None

    def mark_failed(self, row: OutboxEvent, error: str) -> None:
        row.attempts += 1
        row.last_error = error[:2000]


class ProcessedEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def exists(self, event_id: str) -> bool:
        return self.session.get(ProcessedEvent, event_id) is not None

    def add(self, event: EventEnvelope, outcome: str) -> None:
        self.session.add(
            ProcessedEvent(
                event_id=str(event.event_id), event_type=event.event_type.value, outcome=outcome
            )
        )
