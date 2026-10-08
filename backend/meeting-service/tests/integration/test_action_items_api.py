"""Action item CRUD: add, edit, complete/uncomplete, delete — and persistence across sessions."""

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import ActionItem


def participant_id(client: TestClient, meeting_id: int, name: str) -> int:
    meeting = client.get(f"/api/meetings/{meeting_id}").json()
    return int(next(p["id"] for p in meeting["participants"] if p["name"] == name))


def add(client: TestClient, meeting_id: int = 1, **fields: Any) -> dict[str, Any]:
    response = client.post(
        f"/api/meetings/{meeting_id}/action-items", json={"title": "Task", **fields}
    )
    assert response.status_code == 201, response.text
    data: dict[str, Any] = response.json()
    return data


def test_list_seeded_items(client: TestClient, seeded: Session) -> None:
    items = client.get("/api/meetings/1/action-items").json()
    assert len(items) == 6
    assert [i["id"] for i in items] == sorted(i["id"] for i in items)
    assert items[0]["assignee"]["name"] == "Sarah Chen"
    assert items[0]["source"] == "ai" and items[0]["start_ms"] is not None


def test_create_with_assignee_and_due_date(client: TestClient, seeded: Session) -> None:
    sarah = participant_id(client, 1, "Sarah Chen")
    item = add(
        client, title="  Review mocks  ", assignee_id=sarah, due_date="2026-10-20", description="d"
    )
    assert item["title"] == "Review mocks"
    assert item["assignee"]["name"] == "Sarah Chen"
    assert item["due_date"] == "2026-10-20"
    assert (
        item["source"] == "manual" and item["completed"] is False and item["completed_at"] is None
    )


def test_assignee_must_attend_the_meeting(client: TestClient, seeded: Session) -> None:
    tom = participant_id(client, 3, "Tom Becker")  # not in meeting 1
    response = client.post("/api/meetings/1/action-items", json={"title": "x", "assignee_id": tom})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_assignee"


def test_complete_and_uncomplete(client: TestClient, seeded: Session) -> None:
    item = add(client)
    done = client.patch(f"/api/action-items/{item['id']}", json={"completed": True}).json()
    assert done["completed"] is True and done["completed_at"] is not None
    again = client.patch(f"/api/action-items/{item['id']}", json={"completed": True}).json()
    assert again["completed_at"] == done["completed_at"]  # completing twice keeps the first time
    undone = client.patch(f"/api/action-items/{item['id']}", json={"completed": False}).json()
    assert undone["completed"] is False and undone["completed_at"] is None


def test_edit_only_sent_fields_and_unassign_with_null(client: TestClient, seeded: Session) -> None:
    sarah = participant_id(client, 1, "Sarah Chen")
    item = add(client, assignee_id=sarah, due_date="2026-10-20")
    edited = client.patch(f"/api/action-items/{item['id']}", json={"title": "Renamed"}).json()
    assert edited["title"] == "Renamed" and edited["assignee"]["id"] == sarah
    assert edited["due_date"] == "2026-10-20"
    unassigned = client.patch(
        f"/api/action-items/{item['id']}", json={"assignee_id": None, "due_date": None}
    ).json()
    assert unassigned["assignee"] is None and unassigned["due_date"] is None


def test_editing_an_ai_item_makes_it_manual(client: TestClient, seeded: Session) -> None:
    ai_item = client.get("/api/meetings/1/action-items").json()[0]
    assert ai_item["source"] == "ai"
    edited = client.patch(f"/api/action-items/{ai_item['id']}", json={"completed": True}).json()
    assert edited["source"] == "manual"


@pytest.mark.parametrize(
    "body",
    [
        {"title": ""},
        {"title": "x" * 501},
        {"description": "x" * 2001},
        {"due_date": "tomorrow"},
        {"assignee_id": 0},
    ],
)
def test_invalid_payloads(client: TestClient, seeded: Session, body: dict[str, Any]) -> None:
    item = add(client)
    assert client.patch(f"/api/action-items/{item['id']}", json=body).status_code == 422


def test_delete(client: TestClient, seeded: Session) -> None:
    item = add(client)
    assert client.delete(f"/api/action-items/{item['id']}").status_code == 204
    assert item["id"] not in [i["id"] for i in client.get("/api/meetings/1/action-items").json()]
    assert client.delete(f"/api/action-items/{item['id']}").status_code == 404


def test_missing_item_and_meeting(client: TestClient) -> None:
    assert client.patch("/api/action-items/999", json={"title": "x"}).json()["error"]["code"] == (
        "action_item_not_found"
    )
    assert client.post("/api/meetings/999/action-items", json={"title": "x"}).status_code == 404


def test_changes_persist_for_a_new_session(
    app: FastAPI, client: TestClient, seeded: Session
) -> None:
    item = add(client, title="Persist me")
    client.patch(f"/api/action-items/{item['id']}", json={"completed": True})
    with app.state.db.session_factory() as fresh:  # a brand-new connection, nothing cached
        stored = fresh.get(ActionItem, item["id"])
        assert stored is not None and stored.title == "Persist me" and stored.completed
