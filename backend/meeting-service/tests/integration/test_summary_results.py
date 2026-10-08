"""SummaryService.apply_result: idempotent, stale-safe, never destroys the user's manual items."""

from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import Database
from app.events.consumer import apply_result_in_new_session
from app.events.envelope import EventEnvelope, EventType
from app.models import Meeting, ProcessedEvent
from tests.pipeline_helpers import failed, generated

TRANSCRIPT = "[00:00] Priya: Let's plan the launch.\n[00:10] Sam: I'll draft the email by Friday."


def new_meeting(client: TestClient) -> dict[str, Any]:
    body = {
        "title": "Launch sync",
        "meeting_date": "2026-10-08T09:00:00Z",
        "transcript_text": TRANSCRIPT,
    }
    data: dict[str, Any] = client.post("/api/meetings", json=body).json()
    return data


def apply(session: Session, event: EventEnvelope) -> str:
    """Like production: every result is applied in a fresh session (no stale identity map)."""
    database = Database(str(session.get_bind().url))
    try:
        return apply_result_in_new_session(database, event)
    finally:
        database.dispose()


def test_generated_result_creates_summary_and_completes(
    client: TestClient, session: Session
) -> None:
    meeting = new_meeting(client)
    assert apply(session, generated(meeting["id"])) == "applied"

    detail = client.get(f"/api/meetings/{meeting['id']}").json()
    assert detail["processing_status"] == "completed" and detail["processing_error"] is None
    response = client.get(f"/api/meetings/{meeting['id']}/summary")
    assert response.status_code == 200, response.text
    summary = response.json()
    assert summary["overview"] == "Generated overview." and summary["provider"] == "mock"
    assert [t["title"] for t in summary["topics"]] == ["Pricing", "Launch"]
    assert summary["keywords"] == ["Pricing", "Launch"]  # case-insensitive duplicates collapsed
    items = client.get(f"/api/meetings/{meeting['id']}/action-items").json()
    assert [(i["title"], i["source"]) for i in items] == [("Send the invite list", "ai")]


def test_duplicate_delivery_is_applied_once(client: TestClient, session: Session) -> None:
    meeting = new_meeting(client)
    event = generated(meeting["id"])
    assert apply(session, event) == "applied"
    assert apply(session, event) == "duplicate"
    assert len(client.get(f"/api/meetings/{meeting['id']}/action-items").json()) == 1
    assert session.scalar(select(func.count()).select_from(ProcessedEvent)) == 1


def test_regeneration_replaces_ai_items_but_keeps_manual_ones(
    client: TestClient, session: Session
) -> None:
    meeting = new_meeting(client)
    apply(session, generated(meeting["id"]))
    manual = client.post(
        f"/api/meetings/{meeting['id']}/action-items", json={"title": "My own task"}
    ).json()
    ai_item = next(
        i
        for i in client.get(f"/api/meetings/{meeting['id']}/action-items").json()
        if i["source"] == "ai"
    )
    client.patch(f"/api/action-items/{ai_item['id']}", json={"completed": True})  # now manual

    second = generated(
        meeting["id"],
        overview="Second pass.",
        topics=[{"title": "Only topic", "summary": "s", "start_ms": 0}],
        keywords=["Pricing"],
        action_items=[{"title": "Brand new AI item"}],
    )
    assert apply(session, second) == "applied"
    titles = {i["title"] for i in client.get(f"/api/meetings/{meeting['id']}/action-items").json()}
    assert titles == {"My own task", "Send the invite list", "Brand new AI item"}
    assert manual["source"] == "manual"
    summary = client.get(f"/api/meetings/{meeting['id']}/summary").json()
    assert summary["overview"] == "Second pass." and [t["sequence"] for t in summary["topics"]] == [
        0
    ]


def test_assignee_is_kept_only_if_they_attend(client: TestClient, session: Session) -> None:
    meeting = new_meeting(client)
    speaker_id = meeting["participants"][0]["id"]
    event = generated(
        meeting["id"],
        action_items=[
            {"title": "Attendee task", "assignee_speaker_id": speaker_id},
            {"title": "Stranger task", "assignee_speaker_id": 9999},
        ],
    )
    apply(session, event)
    items = {
        i["title"]: i["assignee"]
        for i in client.get(f"/api/meetings/{meeting['id']}/action-items").json()
    }
    assert items["Attendee task"]["id"] == speaker_id and items["Stranger task"] is None


def test_stale_result_for_an_older_revision_is_ignored(
    client: TestClient, session: Session
) -> None:
    meeting = new_meeting(client)  # revision 1
    assert apply(session, generated(meeting["id"], revision=0)) == "stale"
    assert client.get(f"/api/meetings/{meeting['id']}").json()["processing_status"] == "pending"


def test_result_for_a_deleted_meeting_is_recorded_and_dropped(session: Session) -> None:
    assert apply(session, generated(12345)) == "meeting_missing"
    assert session.scalar(select(func.count()).select_from(ProcessedEvent)) == 1


def test_failure_marks_meeting_failed_with_reason(client: TestClient, session: Session) -> None:
    meeting = new_meeting(client)
    assert apply(session, failed(meeting["id"])) == "applied"
    detail = client.get(f"/api/meetings/{meeting['id']}").json()
    assert detail["processing_status"] == "failed"
    assert detail["processing_error"] == "Model timed out"


def test_malformed_failure_payload_still_fails_safely(client: TestClient, session: Session) -> None:
    meeting = new_meeting(client)
    event = EventEnvelope(
        event_type=EventType.SUMMARY_FAILED,
        aggregate_id=str(meeting["id"]),
        payload={"transcript_revision": 1},
    )
    assert apply(session, event) == "applied"
    assert session.get(Meeting, meeting["id"]).processing_error == "Summary generation failed"  # type: ignore[union-attr]


def test_invalid_generated_payload_marks_failed(client: TestClient, session: Session) -> None:
    meeting = new_meeting(client)
    event = generated(meeting["id"], topics=[{"title": "", "summary": "x"}])
    assert apply(session, event) == "invalid"
    detail = client.get(f"/api/meetings/{meeting['id']}").json()
    assert detail["processing_status"] == "failed"


def test_request_events_are_ignored_by_the_result_handler(session: Session) -> None:
    event = EventEnvelope(event_type=EventType.MEETING_CREATED, aggregate_id="1", payload={})
    assert apply(session, event) == "ignored"


def test_retry_after_failure_succeeds(client: TestClient, session: Session) -> None:
    meeting = new_meeting(client)
    apply(session, failed(meeting["id"]))
    assert client.post(f"/api/meetings/{meeting['id']}/summary/regenerate").status_code == 202
    apply(session, generated(meeting["id"]))
    assert client.get(f"/api/meetings/{meeting['id']}").json()["processing_status"] == "completed"
