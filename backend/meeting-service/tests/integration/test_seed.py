from dataclasses import replace
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ActionItem, Meeting, Participant, ProcessingStatus
from app.repositories.participants import ParticipantRepository
from app.seed.data import MEETINGS
from app.seed.loader import seed_database, timeline, validate

NOW = datetime(2026, 10, 9, 12, 0, tzinfo=UTC)


def meeting_count(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(Meeting)) or 0


def test_seed_creates_complete_realistic_meetings(session: Session) -> None:
    assert seed_database(session, NOW) == len(MEETINGS)
    meetings = session.scalars(select(Meeting)).all()
    assert 6 <= len(meetings) <= 8
    for meeting in meetings:
        assert 3 <= len(meeting.participants) <= 5, meeting.title
        assert len(meeting.segments) >= 20, meeting.title
        assert meeting.summary is not None and meeting.summary.overview
        assert len(meeting.summary.topics) >= 4
        assert meeting.summary.keywords
        assert meeting.action_items
        assert meeting.processing_status == ProcessingStatus.COMPLETED
        speakers = {segment.speaker_id for segment in meeting.segments}
        assert speakers <= {participant.id for participant in meeting.participants}
        last_end_seconds = meeting.segments[-1].end_ms / 1000
        assert meeting.duration_seconds == pytest.approx(last_end_seconds, abs=1)


def test_seed_dates_are_relative_to_now_so_filters_stay_demoable(session: Session) -> None:
    seed_database(session, NOW)
    newest = session.scalars(select(Meeting).order_by(Meeting.meeting_date.desc())).first()
    assert newest is not None
    assert newest.meeting_date.date() == date(2026, 10, 8)


def test_seed_is_idempotent_and_reset_reseeds(session: Session) -> None:
    seed_database(session, NOW)
    assert seed_database(session, NOW) == 0
    assert meeting_count(session) == len(MEETINGS)
    assert seed_database(session, NOW, reset=True) == len(MEETINGS)
    assert meeting_count(session) == len(MEETINGS)


def test_people_are_shared_across_meetings(session: Session) -> None:
    seed_database(session, NOW)
    counts = dict(
        (participant.name, meetings)
        for participant, meetings in ParticipantRepository(session).list_with_meeting_counts()
    )
    assert counts["Priya Sharma"] >= 5  # recurring people make the participant filter meaningful


def test_completed_items_are_manual_and_open_items_are_ai(session: Session) -> None:
    seed_database(session, NOW)
    for item in session.scalars(select(ActionItem)):
        assert (item.completed_at is not None) == item.completed
        assert item.source == ("manual" if item.completed else "ai")


def test_timeline_is_monotonic_with_pauses() -> None:
    spans = timeline([("A", "one two three"), ("B", "x " * 20)])
    assert spans[0] == (0, 1500)  # minimum duration for short lines
    assert spans[1][0] == 1500 + 600
    assert spans[1][1] - spans[1][0] == 20 * 380


def test_validate_rejects_broken_catalogue_entries() -> None:
    seed = MEETINGS[0]
    with pytest.raises(ValueError, match="unknown people"):
        validate(replace(seed, lines=[*seed.lines, ("Nobody", "hi")]))
    with pytest.raises(ValueError, match="points past"):
        validate(replace(seed, topics=[replace(seed.topics[0], line=999)]))


def test_participant_get_or_create_is_case_insensitive_and_fills_email(session: Session) -> None:
    repository = ParticipantRepository(session)
    first = repository.get_or_create("Priya Sharma")
    again = repository.get_or_create("  priya sharma ", "priya@example.com")
    assert again.id == first.id and again.email == "priya@example.com"
    assert repository.get_many([first.id, first.id]) == [first]
    assert repository.get_many([]) == []
    assert session.scalar(select(func.count()).select_from(Participant)) == 1
