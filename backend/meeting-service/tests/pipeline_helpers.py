"""Builders for AI result events, shared by the pipeline tests."""

from typing import Any

from app.events.envelope import EventEnvelope, EventType


def generated(meeting_id: int, revision: int = 1, **payload: Any) -> EventEnvelope:
    body: dict[str, Any] = {
        "meeting_id": meeting_id,
        "transcript_revision": revision,
        "provider": "mock",
        "overview": "Generated overview.",
        "keywords": ["Pricing", "pricing ", "Launch"],
        "topics": [
            {"title": "Pricing", "summary": "Discussed pricing.", "start_ms": 0},
            {"title": "Launch", "summary": "Planned the launch.", "start_ms": 12_000},
        ],
        "action_items": [
            {"title": "Send the invite list", "assignee_speaker_id": None, "start_ms": 30_000}
        ],
    }
    body.update(payload)
    return EventEnvelope(
        event_type=EventType.SUMMARY_GENERATED, aggregate_id=str(meeting_id), payload=body
    )


def failed(meeting_id: int, revision: int = 1, reason: str = "Model timed out") -> EventEnvelope:
    return EventEnvelope(
        event_type=EventType.SUMMARY_FAILED,
        aggregate_id=str(meeting_id),
        payload={
            "meeting_id": meeting_id,
            "transcript_revision": revision,
            "reason": reason,
            "attempts": 3,
        },
    )


def fake_ai(request: EventEnvelope) -> EventEnvelope:
    """Stands in for the AI service: answers a processing request with a result for the same
    meeting and revision. (The real service is a separate process — see tests/kafka.)"""
    first_speaker = request.payload["segments"][0]["speaker_id"]
    return generated(
        int(request.aggregate_id),
        request.payload["transcript_revision"],
        action_items=[{"title": "Follow up with the team", "assignee_speaker_id": first_speaker}],
    )
