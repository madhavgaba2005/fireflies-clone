"""Applies AI results to the database — idempotently and safely against stale results.

Used by the Kafka result consumer and by the HTTP fallback; both deliver the same envelope.
"""

import logging

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.events.envelope import EventEnvelope, EventType
from app.events.payloads import SummaryFailedPayload, SummaryGeneratedPayload
from app.models import (
    ActionItem,
    ActionItemSource,
    Meeting,
    ProcessingStatus,
    Summary,
    SummaryKeyword,
    SummaryTopic,
)
from app.models.types import utcnow
from app.repositories.outbox import ProcessedEventRepository

logger = logging.getLogger(__name__)

RESULT_EVENTS = {EventType.SUMMARY_GENERATED, EventType.SUMMARY_FAILED}


class SummaryService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.processed = ProcessedEventRepository(session)

    def apply_result(self, event: EventEnvelope) -> str:
        """Outcome: applied | duplicate | stale | meeting_missing | invalid | ignored."""
        if event.event_type not in RESULT_EVENTS:
            return "ignored"
        if self.processed.exists(str(event.event_id)):
            return "duplicate"  # at-least-once delivery: this exact event was already applied
        outcome = self._apply(event)
        self.processed.add(event, outcome)  # same transaction as the change itself
        self.session.commit()
        logger.info("Applied %s for meeting %s: %s", event.event_type, event.aggregate_id, outcome)
        return outcome

    def _apply(self, event: EventEnvelope) -> str:
        meeting = self.session.get(Meeting, int(event.aggregate_id))
        if meeting is None:
            return "meeting_missing"  # deleted while the AI was working
        if event.payload.get("transcript_revision") != meeting.transcript_revision:
            return "stale"  # the transcript changed after this request; a newer result will come

        if event.event_type == EventType.SUMMARY_FAILED:
            try:
                reason = SummaryFailedPayload.model_validate(event.payload).reason
            except ValidationError:
                reason = "Summary generation failed"
            self._fail(meeting, reason)
            return "applied"

        try:
            result = SummaryGeneratedPayload.model_validate(event.payload)
        except ValidationError:
            logger.exception("Invalid summary.generated payload for meeting %s", meeting.id)
            self._fail(meeting, "The AI service returned an invalid result")
            return "invalid"
        self._store(meeting, result)
        return "applied"

    @staticmethod
    def _fail(meeting: Meeting, reason: str) -> None:
        meeting.processing_status = ProcessingStatus.FAILED
        meeting.processing_error = reason[:2000]

    def _store(self, meeting: Meeting, result: SummaryGeneratedPayload) -> None:
        summary = meeting.summary
        if summary is None:
            # Attach from the parent side: SQLAlchemy 2.x doesn't cascade a new object into the
            # session through a backref, so Summary(meeting=meeting) would silently not be saved.
            summary = Summary(overview="", provider="", transcript_revision=0)
            meeting.summary = summary
        else:
            # Clear children first: their (summary_id, sequence/keyword) uniqueness would otherwise
            # collide with the replacements inside the same flush.
            summary.topics.clear()
            summary.keywords.clear()
            self.session.flush()
        summary.overview = result.overview
        summary.provider = result.provider
        summary.transcript_revision = result.transcript_revision
        summary.generated_at = utcnow()
        summary.topics = [
            SummaryTopic(sequence=i, title=t.title, summary=t.summary, start_ms=t.start_ms)
            for i, t in enumerate(result.topics)
        ]
        unique_keywords: dict[str, str] = {}  # case-insensitive de-duplication, first spelling wins
        for keyword in (k.strip() for k in result.keywords):
            if keyword:
                unique_keywords.setdefault(keyword.casefold(), keyword[:64])
        summary.keywords = [SummaryKeyword(keyword=k) for k in unique_keywords.values()]

        # Replace only AI-extracted items: anything the user created or edited is "manual" and kept.
        attendees = {p.id for p in meeting.participants}
        meeting.action_items = [i for i in meeting.action_items if i.source != ActionItemSource.AI]
        meeting.action_items.extend(
            ActionItem(
                title=item.title,
                assignee_id=item.assignee_speaker_id
                if item.assignee_speaker_id in attendees
                else None,
                start_ms=item.start_ms,
                source=ActionItemSource.AI,
            )
            for item in result.action_items
        )
        meeting.processing_status = ProcessingStatus.COMPLETED
        meeting.processing_error = None
