"""Meeting endpoints: list/search/filter/sort, create (form/paste/upload), read, update, delete."""

import json
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.events.envelope import EventEnvelope, EventType
from app.models import Meeting, OutboxEvent, Participant, TranscriptSegment

TRANSCRIPT = (
    "[00:00] Priya Sharma: Let's review the launch plan.\n"
    "[00:12] Sam Rivera: The beta opens on Monday.\n"
    "[00:30] Priya Sharma: I'll send the invite list by Friday."
)


def create(client: TestClient, **overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"title": "Launch review", "meeting_date": "2026-10-08T09:00:00Z"}
    body.update(overrides)
    response = client.post("/api/meetings", json=body)
    assert response.status_code == 201, response.text
    data: dict[str, Any] = response.json()
    return data


def titles(response_json: dict[str, Any]) -> list[str]:
    return [item["title"] for item in response_json["items"]]


# --- list, search, filter, sort --------------------------------------------------------------


def test_list_returns_required_fields_newest_first(client: TestClient, seeded: Session) -> None:
    body = client.get("/api/meetings").json()
    assert body["total"] == 7 and len(body["items"]) == 7
    first = body["items"][0]
    assert first["title"] == "Weekly Product Sync"
    assert {"title", "meeting_date", "duration_seconds", "participants"} <= first.keys()
    assert first["duration_seconds"] > 0
    assert [p["name"] for p in first["participants"]] == sorted(
        p["name"] for p in first["participants"]
    )
    assert first["keywords"] and first["action_item_count"] >= first["open_action_item_count"]
    dates = [item["meeting_date"] for item in body["items"]]
    assert dates == sorted(dates, reverse=True)


def test_sort_oldest_first(client: TestClient, seeded: Session) -> None:
    body = client.get("/api/meetings", params={"sort": "meeting_date"}).json()
    assert body["items"][0]["title"] == "Q1 Planning Kickoff"


def test_search_by_title_is_case_insensitive(client: TestClient, seeded: Session) -> None:
    assert titles(client.get("/api/meetings", params={"q": "PLANNING"}).json()) == [
        "Q1 Planning Kickoff"
    ]
    assert titles(client.get("/api/meetings", params={"q": "q"}).json()) == [
        "Q4 Marketing Strategy",
        "Q1 Planning Kickoff",
    ]


def test_search_treats_like_wildcards_literally(client: TestClient, seeded: Session) -> None:
    assert client.get("/api/meetings", params={"q": "%"}).json()["total"] == 0
    assert client.get("/api/meetings", params={"q": "_"}).json()["total"] == 0


def test_filter_by_participant_any_of(client: TestClient, seeded: Session) -> None:
    people = {p["name"]: p["id"] for p in client.get("/api/participants").json()}
    tom = titles(
        client.get("/api/meetings", params={"participant_id": people["Tom Becker"]}).json()
    )
    assert tom == ["Discovery Call — Brightline Logistics"]
    both = client.get(
        "/api/meetings",
        params={"participant_id": [people["Tom Becker"], people["Aisha Patel"]]},
    ).json()
    assert set(titles(both)) == {
        "Discovery Call — Brightline Logistics",
        "Senior Backend Engineer — Hiring Debrief",
    }


def test_filter_by_date_range_is_inclusive(client: TestClient, seeded: Session) -> None:
    # Seed dates (SEED_NOW = 2026-10-09): product sync 10-08, sprint review 10-06, discovery 10-04
    one_day = client.get(
        "/api/meetings", params={"date_from": "2026-10-08", "date_to": "2026-10-08"}
    )
    assert titles(one_day.json()) == ["Weekly Product Sync"]
    since = client.get("/api/meetings", params={"date_from": "2026-10-04"}).json()
    assert since["total"] == 3
    until = client.get("/api/meetings", params={"date_to": "2026-09-16"}).json()
    assert titles(until) == ["Q1 Planning Kickoff"]


def test_inverted_date_range_is_rejected(client: TestClient) -> None:
    response = client.get(
        "/api/meetings", params={"date_from": "2026-10-09", "date_to": "2026-10-01"}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_date_range"


def test_filters_combine(client: TestClient, seeded: Session) -> None:
    people = {p["name"]: p["id"] for p in client.get("/api/participants").json()}
    body = client.get(
        "/api/meetings",
        params={
            "q": "review",
            "participant_id": people["Noah Williams"],
            "date_from": "2026-10-01",
        },
    ).json()
    assert titles(body) == [
        "Engineering Sprint 14 Review",
        "Route Planner Mobile Redesign — Design Review",
    ]


def test_filter_by_keyword_tag(client: TestClient, seeded: Session) -> None:
    body = client.get("/api/meetings", params={"keyword": "activation"}).json()
    assert set(titles(body)) == {"Weekly Product Sync", "Q1 Planning Kickoff"}


def test_pagination(client: TestClient, seeded: Session) -> None:
    page = client.get("/api/meetings", params={"limit": 2, "offset": 2}).json()
    assert page["total"] == 7 and page["limit"] == 2 and page["offset"] == 2
    assert titles(page) == [
        "Discovery Call — Brightline Logistics",
        "Route Planner Mobile Redesign — Design Review",
    ]


@pytest.mark.parametrize(
    "params", [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"sort": "title"}]
)
def test_invalid_list_parameters(client: TestClient, params: dict[str, Any]) -> None:
    response = client.get("/api/meetings", params=params)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_empty_library(client: TestClient) -> None:
    assert client.get("/api/meetings").json() == {"items": [], "total": 0, "limit": 50, "offset": 0}


# --- detail / transcript / summary ------------------------------------------------------------


def test_detail_includes_speaker_talk_time(client: TestClient, seeded: Session) -> None:
    detail = client.get("/api/meetings/1").json()
    assert detail["title"] == "Weekly Product Sync"
    assert detail["processing_status"] == "completed"
    stats = detail["speaker_stats"]
    assert {s["name"] for s in stats} == {p["name"] for p in detail["participants"]}
    assert sum(s["percentage"] for s in stats) == pytest.approx(100, abs=0.5)
    assert stats == sorted(stats, key=lambda s: s["talk_time_ms"], reverse=True)


def test_transcript_is_ordered_with_speaker_and_times(client: TestClient, seeded: Session) -> None:
    body = client.get("/api/meetings/1/transcript").json()
    segments = body["segments"]
    assert body["revision"] == 1 and len(segments) == 30
    assert [s["sequence"] for s in segments] == list(range(30))
    assert segments[0]["speaker"]["name"] == "Priya Sharma"
    assert all(s["start_ms"] <= s["end_ms"] for s in segments)
    assert all(a["end_ms"] <= b["start_ms"] for a, b in zip(segments, segments[1:], strict=False))


def test_summary_has_overview_topics_and_keywords(client: TestClient, seeded: Session) -> None:
    summary = client.get("/api/meetings/1/summary").json()
    assert summary["overview"].startswith("The team reviewed release 2.4")
    assert [t["sequence"] for t in summary["topics"]] == [0, 1, 2, 3]
    assert summary["topics"][1]["start_ms"] > summary["topics"][0]["start_ms"]
    assert "Activation" in summary["keywords"]


@pytest.mark.parametrize("path", ["", "/transcript", "/summary", "/action-items"])
def test_missing_meeting_is_404_everywhere(client: TestClient, path: str) -> None:
    response = client.get(f"/api/meetings/999{path}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "meeting_not_found"


def test_summary_404_before_generation(client: TestClient) -> None:
    meeting = create(client)
    response = client.get(f"/api/meetings/{meeting['id']}/summary")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "summary_not_found"


# --- create ---------------------------------------------------------------------------------


def test_create_via_form_without_transcript(client: TestClient, session: Session) -> None:
    meeting = create(
        client,
        participants=[
            {"name": "Ada Lovelace", "email": "ada@example.com"},
            {"name": "Alan Turing"},
        ],
        duration_seconds=1800,
    )
    assert meeting["source"] == "form"
    assert meeting["processing_status"] == "not_requested"
    assert meeting["duration_seconds"] == 1800
    assert {p["name"] for p in meeting["participants"]} == {"Ada Lovelace", "Alan Turing"}
    assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 0


def test_create_with_pasted_transcript_queues_processing(
    client: TestClient, session: Session
) -> None:
    meeting = create(client, transcript_text=TRANSCRIPT, source="paste")
    assert meeting["processing_status"] == "pending"
    assert meeting["transcript_revision"] == 1
    assert meeting["duration_seconds"] == 33  # last line starts at 30 s, ~3 s long
    assert {p["name"] for p in meeting["participants"]} == {"Priya Sharma", "Sam Rivera"}

    transcript = client.get(f"/api/meetings/{meeting['id']}/transcript").json()["segments"]
    assert [s["speaker"]["name"] for s in transcript] == [
        "Priya Sharma",
        "Sam Rivera",
        "Priya Sharma",
    ]

    (row,) = session.scalars(select(OutboxEvent)).all()
    event = EventEnvelope.model_validate_json(row.envelope)
    assert event.event_type == EventType.MEETING_CREATED
    assert event.aggregate_id == str(meeting["id"])
    assert event.payload["transcript_revision"] == 1
    assert [s["text"] for s in event.payload["segments"]][1] == "The beta opens on Monday."
    assert row.published_at is None  # publishing is the relay's job, not the request's


def test_create_from_uploaded_vtt_and_json(client: TestClient) -> None:
    vtt = "WEBVTT\n\n00:00:01.000 --> 00:00:03.000\n<v Kim>Hello there.</v>\n"
    from_vtt = create(client, transcript_text=vtt, transcript_format="vtt", source="upload")
    assert from_vtt["source"] == "upload" and from_vtt["participants"][0]["name"] == "Kim"
    segments = json.dumps([{"speaker": "Lee", "start": 0, "end": 4.5, "text": "Hi"}])
    from_json = create(client, transcript_text=segments, transcript_format="json")
    assert from_json["duration_seconds"] == 5


def test_speakers_resolve_to_existing_people_case_insensitively(
    client: TestClient, seeded: Session
) -> None:
    meeting = create(
        client, transcript_text="[00:00] priya sharma: hello", participants=[{"id": 2}]
    )
    names = {p["name"] for p in meeting["participants"]}
    assert names == {"Priya Sharma", "Arjun Mehta"}
    assert seeded.scalar(select(func.count()).select_from(Participant)) == 11  # nobody duplicated


def test_malformed_transcript_is_400_with_line_number(client: TestClient, session: Session) -> None:
    response = client.post(
        "/api/meetings",
        json={
            "title": "Bad",
            "meeting_date": "2026-10-08T09:00:00Z",
            "transcript_text": "[00:10] A: later\n[00:05] B: earlier",
        },
    )
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "transcript_invalid" and error["details"] == {"line": 2}
    assert session.scalar(select(func.count()).select_from(Meeting)) == 0  # nothing half-saved


@pytest.mark.parametrize(
    "body",
    [
        {"meeting_date": "2026-10-08T09:00:00Z"},
        {"title": "   ", "meeting_date": "2026-10-08T09:00:00Z"},
        {"title": "x" * 201, "meeting_date": "2026-10-08T09:00:00Z"},
        {"title": "No timezone", "meeting_date": "2026-10-08T09:00:00"},
        {"title": "T", "meeting_date": "2026-10-08T09:00:00Z", "participants": [{}]},
        {
            "title": "T",
            "meeting_date": "2026-10-08T09:00:00Z",
            "participants": [{"name": "A", "email": "nope"}],
        },
        {"title": "T", "meeting_date": "2026-10-08T09:00:00Z", "duration_seconds": -1},
        {"title": "T", "meeting_date": "2026-10-08T09:00:00Z", "transcript_format": "docx"},
        {"title": "T", "meeting_date": "2026-10-08T09:00:00Z", "transcript_text": "x" * 300_001},
    ],
)
def test_invalid_create_payloads_are_422(client: TestClient, body: dict[str, Any]) -> None:
    response = client.post("/api/meetings", json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_unknown_participant_id_is_422(client: TestClient) -> None:
    response = client.post(
        "/api/meetings",
        json={"title": "T", "meeting_date": "2026-10-08T09:00:00Z", "participants": [{"id": 42}]},
    )
    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "participant_not_found",
        "message": "Unknown participant id(s)",
        "details": {"ids": [42]},
    }


# --- update ---------------------------------------------------------------------------------


def test_update_title_date_and_participants_persists(client: TestClient, seeded: Session) -> None:
    people = {p["name"]: p["id"] for p in client.get("/api/participants").json()}
    original = client.get("/api/meetings/6").json()  # Q4 Marketing Strategy
    keep = [{"id": p["id"]} for p in original["participants"]]
    response = client.patch(
        "/api/meetings/6",
        json={
            "title": "  Q4 Marketing Strategy (revised)  ",
            "meeting_date": "2026-09-23T15:00:00+05:30",
            "participants": [*keep, {"id": people["Sarah Chen"]}, {"name": "New Person"}],
        },
    )
    assert response.status_code == 200
    reloaded = client.get("/api/meetings/6").json()
    assert reloaded["title"] == "Q4 Marketing Strategy (revised)"
    assert reloaded["meeting_date"].startswith("2026-09-23T09:30:00")
    assert {"Sarah Chen", "New Person"} <= {p["name"] for p in reloaded["participants"]}


def test_partial_update_leaves_other_fields(client: TestClient, seeded: Session) -> None:
    before = client.get("/api/meetings/2").json()
    after = client.patch("/api/meetings/2", json={"title": "Sprint 14 Review"}).json()
    assert after["title"] == "Sprint 14 Review"
    assert after["meeting_date"] == before["meeting_date"]
    assert after["participants"] == before["participants"]


def test_removing_a_speaker_is_a_conflict(client: TestClient, seeded: Session) -> None:
    meeting = client.get("/api/meetings/5").json()  # hiring debrief: everyone speaks
    response = client.patch(
        "/api/meetings/5", json={"participants": [{"id": meeting["participants"][0]["id"]}]}
    )
    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "participant_has_transcript_lines"
    assert len(error["details"]["participants"]) == 2


def test_removing_a_silent_participant_unassigns_their_items(client: TestClient) -> None:
    meeting = create(client, transcript_text="[00:00] Ann: hello", participants=[{"name": "Bob"}])
    bob = next(p for p in meeting["participants"] if p["name"] == "Bob")
    item = client.post(
        f"/api/meetings/{meeting['id']}/action-items",
        json={"title": "Task", "assignee_id": bob["id"]},
    ).json()
    ann = next(p for p in meeting["participants"] if p["name"] == "Ann")
    response = client.patch(
        f"/api/meetings/{meeting['id']}", json={"participants": [{"id": ann["id"]}]}
    )
    assert response.status_code == 200
    items = client.get(f"/api/meetings/{meeting['id']}/action-items").json()
    assert items[0]["id"] == item["id"] and items[0]["assignee"] is None


def test_update_missing_meeting_is_404(client: TestClient) -> None:
    assert client.patch("/api/meetings/999", json={"title": "x"}).status_code == 404


def test_update_with_blank_title_is_422(client: TestClient, seeded: Session) -> None:
    assert client.patch("/api/meetings/1", json={"title": "  "}).status_code == 422


# --- delete ---------------------------------------------------------------------------------


def test_delete_removes_meeting_and_children(client: TestClient, seeded: Session) -> None:
    assert client.delete("/api/meetings/1").status_code == 204
    assert client.get("/api/meetings/1").status_code == 404
    assert client.get("/api/meetings").json()["total"] == 6
    remaining = seeded.scalar(
        select(func.count()).select_from(TranscriptSegment).where(TranscriptSegment.meeting_id == 1)
    )
    assert remaining == 0
    assert client.delete("/api/meetings/1").status_code == 404


# --- regenerate -----------------------------------------------------------------------------


def test_regenerate_queues_a_summary_request(client: TestClient, seeded: Session) -> None:
    response = client.post("/api/meetings/3/summary/regenerate")
    assert response.status_code == 202
    assert response.json() == {"meeting_id": 3, "processing_status": "pending"}
    row = seeded.scalars(select(OutboxEvent)).one()
    assert row.event_type == "summary.requested"


def test_regenerate_without_transcript_is_409(client: TestClient) -> None:
    meeting = create(client)
    response = client.post(f"/api/meetings/{meeting['id']}/summary/regenerate")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "no_transcript"


def test_participants_list_with_counts(client: TestClient, seeded: Session) -> None:
    people = client.get("/api/participants").json()
    assert len(people) == 11
    assert [p["name"] for p in people] == sorted(p["name"] for p in people)
    priya = next(p for p in people if p["name"] == "Priya Sharma")
    assert priya["meeting_count"] == 6 and priya["email"] == "priya.sharma@northwind.io"
