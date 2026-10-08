"""Builds AI processing requests and queues them in the outbox (never published directly)."""

from sqlalchemy.orm import Session

from app.events.envelope import EventEnvelope, EventType
from app.events.payloads import ParticipantPayload, ProcessingRequestPayload, SegmentPayload
from app.models import Meeting, ProcessingStatus, TranscriptSegment
from app.repositories.outbox import OutboxRepository


def processing_request(
    meeting: Meeting, segments: list[TranscriptSegment], event_type: EventType
) -> EventEnvelope:
    """Event-carried state transfer: the transcript travels in the event, so the AI service
    never calls back into the Meeting Service and stays stateless."""
    payload = ProcessingRequestPayload(
        meeting_id=meeting.id,
        transcript_revision=meeting.transcript_revision,
        title=meeting.title,
        participants=[ParticipantPayload(id=p.id, name=p.name) for p in meeting.participants],
        segments=[
            SegmentPayload(
                speaker_id=segment.speaker_id,
                speaker=segment.speaker.name,
                start_ms=segment.start_ms,
                end_ms=segment.end_ms,
                text=segment.text,
            )
            for segment in segments
        ],
    )
    return EventEnvelope(
        event_type=event_type, aggregate_id=str(meeting.id), payload=payload.model_dump()
    )


def queue_processing(
    session: Session, meeting: Meeting, segments: list[TranscriptSegment], event_type: EventType
) -> None:
    """Mark the meeting pending and queue the request in the outbox, in the caller's transaction."""
    meeting.processing_status = ProcessingStatus.PENDING
    meeting.processing_error = None
    OutboxRepository(session).add(processing_request(meeting, segments, event_type))
