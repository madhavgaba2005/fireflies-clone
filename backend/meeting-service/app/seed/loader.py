"""Loads the seed catalogue into the database."""

import math
from datetime import datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import (
    ActionItem,
    ActionItemSource,
    Meeting,
    MeetingSource,
    OutboxEvent,
    Participant,
    ProcessedEvent,
    ProcessingStatus,
    Summary,
    SummaryKeyword,
    SummaryTopic,
    TranscriptSegment,
)
from app.repositories.participants import ParticipantRepository
from app.seed.data import MEETINGS, PEOPLE, SeedMeeting

MS_PER_WORD = 380  # ≈158 words per minute — natural meeting pace
MIN_SEGMENT_MS = 1500
PAUSE_MS = 600


def timeline(lines: list[tuple[str, str]]) -> list[tuple[int, int]]:
    """(start_ms, end_ms) per line from word counts, with a short pause between speakers."""
    spans: list[tuple[int, int]] = []
    cursor = 0
    for _speaker, text in lines:
        duration = max(MIN_SEGMENT_MS, len(text.split()) * MS_PER_WORD)
        spans.append((cursor, cursor + duration))
        cursor += duration + PAUSE_MS
    return spans


def validate(meeting: SeedMeeting) -> None:
    first_names = {name.split()[0] for name in meeting.participants}
    unknown = {speaker for speaker, _ in meeting.lines} - first_names
    unknown |= {item.assignee for item in meeting.action_items if item.assignee} - first_names
    if unknown:
        raise ValueError(f"{meeting.title!r}: unknown people {sorted(unknown)}")
    references = [topic.line for topic in meeting.topics] + [i.line for i in meeting.action_items]
    if any(not 0 <= line < len(meeting.lines) for line in references):
        raise ValueError(f"{meeting.title!r}: a topic or action item points past the transcript")
    missing = set(meeting.participants) - PEOPLE.keys()
    if missing:
        raise ValueError(f"{meeting.title!r}: no email for {sorted(missing)}")


def build_meeting(seed: SeedMeeting, people: dict[str, Participant], now: datetime) -> Meeting:
    by_first_name = {name.split()[0]: people[name] for name in seed.participants}
    spans = timeline(seed.lines)
    day = (now - timedelta(days=seed.days_ago)).date()
    meeting_date = datetime.combine(day, datetime.min.time(), tzinfo=now.tzinfo).replace(
        hour=seed.time[0], minute=seed.time[1]
    )

    meeting = Meeting(
        title=seed.title,
        meeting_date=meeting_date,
        duration_seconds=math.ceil(spans[-1][1] / 1000),
        source=MeetingSource.SEED,
        processing_status=ProcessingStatus.COMPLETED,
        transcript_revision=1,
        participants=[people[name] for name in seed.participants],
        created_at=meeting_date,
    )
    meeting.segments = [
        TranscriptSegment(
            speaker=by_first_name[speaker], sequence=index, start_ms=start, end_ms=end, text=text
        )
        for index, ((speaker, text), (start, end)) in enumerate(zip(seed.lines, spans, strict=True))
    ]
    meeting.summary = Summary(
        overview=seed.overview,
        provider="seed",
        transcript_revision=1,
        generated_at=meeting_date,
        topics=[
            SummaryTopic(sequence=i, title=t.title, summary=t.summary, start_ms=spans[t.line][0])
            for i, t in enumerate(seed.topics)
        ],
        keywords=[SummaryKeyword(keyword=keyword) for keyword in seed.keywords],
    )
    meeting.action_items = [
        ActionItem(
            title=item.title,
            assignee=by_first_name[item.assignee] if item.assignee else None,
            due_date=now.date() + timedelta(days=item.due_in_days)
            if item.due_in_days is not None
            else None,
            completed=item.completed,
            completed_at=meeting_date + timedelta(days=1) if item.completed else None,
            # Ticking an item off counts as a user edit, so completed items are "manual".
            source=ActionItemSource.MANUAL if item.completed else ActionItemSource.AI,
            start_ms=spans[item.line][0],
        )
        for item in seed.action_items
    ]
    return meeting


def has_meetings(session: Session) -> bool:
    return bool(session.scalar(select(func.count()).select_from(Meeting)))


def clear_all(session: Session) -> None:
    """Delete every row. Meeting children go through ON DELETE CASCADE."""
    for model in (ProcessedEvent, OutboxEvent, Meeting, Participant):
        session.execute(delete(model))


def load_seed(session: Session, now: datetime) -> int:
    for seed in MEETINGS:
        validate(seed)
    participants = ParticipantRepository(session)
    for seed in MEETINGS:
        people = {
            name: participants.get_or_create(name, PEOPLE[name]) for name in seed.participants
        }
        session.add(build_meeting(seed, people, now))
    session.commit()
    return len(MEETINGS)


def seed_database(session: Session, now: datetime, *, reset: bool = False) -> int:
    """Seed an empty database (or wipe and reseed with reset=True). Returns meetings created."""
    if reset:
        clear_all(session)
        session.commit()
    elif has_meetings(session):
        return 0
    return load_seed(session, now)
