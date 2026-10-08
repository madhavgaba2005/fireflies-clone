"""Versioned event envelope — the only contract between the Meeting Service and the AI service.

The AI service keeps an identical copy (services share no code). Both copies are pinned by
tests/contract/envelope_v1.schema.json, and CI fails if the two schema files differ.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

ENVELOPE_VERSION = 1


class EventType(StrEnum):
    MEETING_CREATED = "meeting.created"
    TRANSCRIPT_UPDATED = "transcript.updated"
    SUMMARY_REQUESTED = "summary.requested"
    SUMMARY_GENERATED = "summary.generated"
    SUMMARY_FAILED = "summary.failed"


class EventEnvelope(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    version: int = ENVELOPE_VERSION
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    aggregate_id: str = Field(min_length=1)  # meeting id; also the Kafka partition key
    payload: dict[str, Any]

    def to_bytes(self) -> bytes:
        return self.model_dump_json().encode()

    @classmethod
    def from_bytes(cls, raw: bytes) -> "EventEnvelope":
        return cls.model_validate_json(raw)
