import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.events.envelope import ENVELOPE_VERSION, EventEnvelope, EventType

CONTRACT = Path(__file__).parents[1] / "contract" / "envelope_v1.schema.json"


def make_event() -> EventEnvelope:
    return EventEnvelope(
        event_type=EventType.MEETING_CREATED, aggregate_id="42", payload={"meeting_id": 42}
    )


def test_defaults_fill_id_version_and_timestamp() -> None:
    event = make_event()
    assert event.version == ENVELOPE_VERSION
    assert event.occurred_at.tzinfo is not None
    assert event.event_id != make_event().event_id


def test_bytes_round_trip_preserves_everything() -> None:
    event = make_event()
    assert EventEnvelope.from_bytes(event.to_bytes()) == event


def test_unknown_fields_and_event_types_are_rejected() -> None:
    raw = json.loads(make_event().to_bytes())
    with pytest.raises(ValidationError):
        EventEnvelope.model_validate({**raw, "unexpected": True})
    with pytest.raises(ValidationError):
        EventEnvelope.model_validate({**raw, "event_type": "meeting.exploded"})


def test_empty_aggregate_id_is_rejected() -> None:
    with pytest.raises(ValidationError):
        EventEnvelope(event_type=EventType.SUMMARY_FAILED, aggregate_id="", payload={})


def test_schema_matches_committed_contract() -> None:
    """If this fails, the event contract changed: bump the version and update BOTH services."""
    assert EventEnvelope.model_json_schema() == json.loads(CONTRACT.read_text())
