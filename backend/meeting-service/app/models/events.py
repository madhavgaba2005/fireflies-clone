"""Infrastructure tables for the event pipeline (not part of the domain model)."""

from datetime import datetime

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.types import UTCDateTime, utcnow


class OutboxEvent(Base):
    """An event written in the same transaction as the change it describes (transactional outbox).

    The relay publishes rows where `published_at IS NULL` and then sets it (at-least-once).
    """

    __tablename__ = "outbox_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # = envelope event_id
    event_type: Mapped[str] = mapped_column(String(64))
    aggregate_id: Mapped[str] = mapped_column(String(64))
    envelope: Mapped[str] = mapped_column(Text)  # the serialized EventEnvelope, published as-is
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    published_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        # Partial index: the relay only ever scans unpublished rows.
        Index(
            "ix_outbox_unpublished",
            "created_at",
            sqlite_where=published_at.is_(None),
        ),
    )


class ProcessedEvent(Base):
    """Ids of result events already applied — makes the consumer idempotent."""

    __tablename__ = "processed_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64))
    outcome: Mapped[str] = mapped_column(String(32))  # applied | stale | meeting_missing
    processed_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
