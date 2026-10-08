"""Global search across titles and transcripts (bonus B3)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.search import snippet


def test_finds_transcript_moments_across_meetings(client: TestClient, seeded: Session) -> None:
    body = client.get("/api/search", params={"q": "webhook"}).json()
    assert body["query"] == "webhook" and not body["truncated"]
    titles = [r["title"] for r in body["results"]]
    assert "Engineering Sprint 14 Review" in titles
    assert "Discovery Call — Brightline Logistics" in titles  # "webhooks for exactly that"
    sprint = next(r for r in body["results"] if r["title"] == "Engineering Sprint 14 Review")
    assert sprint["title_match"] is False and len(sprint["hits"]) >= 3
    hit = sprint["hits"][0]
    assert {"segment_id", "start_ms", "speaker", "snippet"} <= hit.keys()
    assert "webhook" in hit["snippet"].lower()
    assert body["total_hits"] == sum(len(r["hits"]) for r in body["results"])
    starts = [h["start_ms"] for h in sprint["hits"]]
    assert starts == sorted(starts)  # in transcript order


def test_title_matches_are_included_and_flagged(client: TestClient, seeded: Session) -> None:
    body = client.get("/api/search", params={"q": "hiring"}).json()
    debrief = next(r for r in body["results"] if r["title"].startswith("Senior Backend"))
    assert debrief["title_match"] is True


def test_results_are_newest_first(client: TestClient, seeded: Session) -> None:
    dates = [
        r["meeting_date"] for r in client.get("/api/search", params={"q": "the"}).json()["results"]
    ]
    assert dates == sorted(dates, reverse=True)


def test_case_insensitive_and_wildcards_literal(client: TestClient, seeded: Session) -> None:
    assert client.get("/api/search", params={"q": "SAMSARA"}).json()["total_hits"] >= 1
    assert client.get("/api/search", params={"q": "%%"}).json()["results"] == []


def test_no_results(client: TestClient, seeded: Session) -> None:
    body = client.get("/api/search", params={"q": "kubernetes"}).json()
    assert body == {"query": "kubernetes", "results": [], "total_hits": 0, "truncated": False}


@pytest.mark.parametrize("q", ["", "a", "x" * 101])
def test_query_length_is_validated(client: TestClient, q: str) -> None:
    assert client.get("/api/search", params={"q": q}).status_code == 422


def test_results_are_capped(client: TestClient, seeded: Session) -> None:
    body = client.get("/api/search", params={"q": "the"}).json()
    assert len(body["results"]) <= 10 and body["total_hits"] <= 50 and body["truncated"] is True


def test_snippet_keeps_short_text_whole() -> None:
    assert snippet("a short needle text", "needle") == "a short needle text"


def test_snippet_trims_long_text_at_word_boundaries() -> None:
    text = (
        " ".join(f"word{i}" for i in range(40))
        + " needle "
        + " ".join(f"tail{i}" for i in range(40))
    )
    result = snippet(text, "NEEDLE", context=30)
    assert result.startswith("…") and result.endswith("…") and "needle" in result
    inner = result.strip("…").split()
    assert all(w in text.split() for w in inner)  # no word was cut in half
    assert len(result) < 2 * 30 + len("needle") + 3


def test_snippet_without_match_returns_text() -> None:
    assert snippet("nothing here", "zzz") == "nothing here"
