"""The database itself enforces the rules in docs/DATABASE_DESIGN.md (not just the application)."""

from datetime import UTC, datetime, timedelta, timezone

import pytest
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    ActionItem,
    Meeting,
    Participant,
    Summary,
    SummaryKeyword,
    SummaryTopic,
    TranscriptSegment,
    meeting_participants,
)

NOW = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


def make_meeting(session: Session, **overrides: object) -> Meeting:
    speaker = Participant(name="Priya Sharma", email="priya@example.com")
    fields: dict[str, object] = {"title": "Sync", "meeting_date": NOW, **overrides}
    meeting = Meeting(participants=[speaker], **fields)
    meeting.segments = [
        TranscriptSegment(speaker=speaker, sequence=0, start_ms=0, end_ms=1000, text="Hi")
    ]
    meeting.summary = Summary(
        overview="o",
        provider="seed",
        transcript_revision=0,
        topics=[SummaryTopic(sequence=0, title="t", summary="s")],
        keywords=[SummaryKeyword(keyword="k")],
    )
    meeting.action_items = [ActionItem(title="Do it", assignee=speaker)]
    session.add(meeting)
    session.commit()
    return meeting


def count(session: Session, model: object) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0  # type: ignore[arg-type]


def test_deleting_a_meeting_cascades_to_all_children(session: Session) -> None:
    make_meeting(session)
    session.execute(delete(Meeting))  # plain SQL DELETE: relies on ON DELETE CASCADE in SQLite
    session.commit()
    for model in (TranscriptSegment, Summary, SummaryTopic, SummaryKeyword, ActionItem):
        assert count(session, model) == 0, model
    assert count(session, meeting_participants) == 0
    assert count(session, Participant) == 1  # people are shared, not owned by a meeting


def test_participant_with_transcript_lines_cannot_be_deleted(session: Session) -> None:
    make_meeting(session)
    with pytest.raises(IntegrityError):
        session.execute(delete(Participant))
        session.commit()


def test_deleting_an_assignee_unassigns_the_action_item(session: Session) -> None:
    speaker = Participant(name="Speaker")
    assignee = Participant(name="Assignee")
    meeting = Meeting(title="M", meeting_date=NOW, participants=[speaker])
    meeting.action_items = [ActionItem(title="Task", assignee=assignee)]
    session.add(meeting)
    session.commit()
    session.execute(delete(Participant).where(Participant.id == assignee.id))
    session.commit()
    session.expire_all()
    assert session.scalars(select(ActionItem)).one().assignee_id is None


def test_participant_names_are_unique_case_insensitively(session: Session) -> None:
    session.add(Participant(name="Priya Sharma"))
    session.commit()
    session.add(Participant(name="priya sharma"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_one_summary_per_meeting(session: Session) -> None:
    meeting = make_meeting(session)
    session.add(Summary(meeting_id=meeting.id, overview="x", provider="p", transcript_revision=0))
    with pytest.raises(IntegrityError):
        session.commit()


def test_segment_sequence_is_unique_within_a_meeting(session: Session) -> None:
    meeting = make_meeting(session)
    speaker_id = meeting.segments[0].speaker_id
    session.add(
        TranscriptSegment(
            meeting_id=meeting.id, speaker_id=speaker_id, sequence=0, start_ms=5, end_ms=6, text="x"
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE meetings SET title = '   '",
        "UPDATE meetings SET duration_seconds = -1",
        "UPDATE meetings SET processing_status = 'exploded'",
        "UPDATE transcript_segments SET end_ms = start_ms - 1",
        "UPDATE transcript_segments SET start_ms = -5, end_ms = 0",
        "UPDATE action_items SET completed = 1, completed_at = NULL",
        "UPDATE action_items SET source = 'robot'",
    ],
)
def test_check_constraints_reject_invalid_rows(session: Session, statement: str) -> None:
    make_meeting(session)
    with pytest.raises(IntegrityError):
        session.execute(text(statement))
        session.commit()


def test_datetimes_round_trip_as_aware_utc(session: Session) -> None:
    ist = timezone(timedelta(hours=5, minutes=30))
    meeting = make_meeting(session, meeting_date=datetime(2026, 10, 1, 14, 30, tzinfo=ist))
    session.expire_all()
    stored = session.get(Meeting, meeting.id)
    assert stored is not None
    assert stored.meeting_date == datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
    assert stored.meeting_date.tzinfo is UTC


def test_naive_datetimes_are_refused(session: Session) -> None:
    session.add(Meeting(title="M", meeting_date=datetime(2026, 1, 1)))
    with pytest.raises(Exception, match="Naive datetimes"):
        session.commit()


def test_relationships_are_ordered(session: Session) -> None:
    speaker = Participant(name="S")
    meeting = Meeting(title="M", meeting_date=NOW, participants=[speaker])
    meeting.segments = [
        TranscriptSegment(speaker=speaker, sequence=i, start_ms=i, end_ms=i, text=str(i))
        for i in (2, 0, 1)
    ]
    session.add(meeting)
    session.commit()
    session.expire_all()
    stored = session.get(Meeting, meeting.id)
    assert stored is not None
    assert [segment.sequence for segment in stored.segments] == [0, 1, 2]
