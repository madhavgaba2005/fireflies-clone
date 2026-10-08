"""SQLAlchemy ORM models (docs/DATABASE_DESIGN.md). Importing this package registers all tables."""

from app.database import Base
from app.models.events import OutboxEvent, ProcessedEvent
from app.models.meeting import (
    ActionItem,
    ActionItemSource,
    Meeting,
    MeetingSource,
    Participant,
    ProcessingStatus,
    Summary,
    SummaryKeyword,
    SummaryTopic,
    TranscriptSegment,
    meeting_participants,
)

__all__ = [
    "ActionItem",
    "ActionItemSource",
    "Base",
    "Meeting",
    "MeetingSource",
    "OutboxEvent",
    "Participant",
    "ProcessedEvent",
    "ProcessingStatus",
    "Summary",
    "SummaryKeyword",
    "SummaryTopic",
    "TranscriptSegment",
    "meeting_participants",
]
