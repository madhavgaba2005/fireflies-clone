from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from typing import Literal

from sqlalchemy import Select, case, func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    ActionItem,
    Meeting,
    Participant,
    Summary,
    SummaryKeyword,
    TranscriptSegment,
    meeting_participants,
)

SortOrder = Literal["-meeting_date", "meeting_date"]


@dataclass(frozen=True)
class MeetingFilters:
    q: str | None = None
    participant_ids: Sequence[int] = field(default_factory=tuple)
    date_from: date | None = None  # inclusive, UTC day
    date_to: date | None = None  # inclusive, UTC day
    keyword: str | None = None
    sort: SortOrder = "-meeting_date"
    limit: int = 50
    offset: int = 0


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _start_of_day(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=UTC)


class MeetingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _filtered(self, filters: MeetingFilters) -> Select[Meeting]:
        statement = select(Meeting)
        if filters.q:
            pattern = f"%{_escape_like(filters.q.strip())}%"
            statement = statement.where(Meeting.title.ilike(pattern, escape="\\"))
        if filters.participant_ids:
            attended = select(meeting_participants.c.meeting_id).where(
                meeting_participants.c.participant_id.in_(filters.participant_ids)
            )
            statement = statement.where(Meeting.id.in_(attended))
        if filters.date_from:
            statement = statement.where(Meeting.meeting_date >= _start_of_day(filters.date_from))
        if filters.date_to:
            end = _start_of_day(filters.date_to + timedelta(days=1))
            statement = statement.where(Meeting.meeting_date < end)
        if filters.keyword:
            tagged = (
                select(Summary.meeting_id)
                .join(SummaryKeyword)
                .where(SummaryKeyword.keyword == filters.keyword.strip())
            )
            statement = statement.where(Meeting.id.in_(tagged))
        return statement

    def search(self, filters: MeetingFilters) -> tuple[list[Meeting], int]:
        statement = self._filtered(filters)
        total = self.session.scalar(select(func.count()).select_from(statement.subquery())) or 0
        newest_first = filters.sort == "-meeting_date"
        order = Meeting.meeting_date.desc() if newest_first else Meeting.meeting_date.asc()
        page = (
            statement.order_by(order, Meeting.id.desc() if newest_first else Meeting.id.asc())
            .limit(filters.limit)
            .offset(filters.offset)
            # Load related rows in two extra queries for the whole page instead of one per row.
            .options(
                selectinload(Meeting.participants),
                selectinload(Meeting.summary).selectinload(Summary.keywords),
            )
        )
        return list(self.session.scalars(page)), total

    def action_item_counts(self, meeting_ids: Sequence[int]) -> dict[int, tuple[int, int]]:
        """meeting_id → (total items, open items), in one grouped query."""
        if not meeting_ids:
            return {}
        open_items = func.sum(case((ActionItem.completed.is_(False), 1), else_=0))
        rows = self.session.execute(
            select(ActionItem.meeting_id, func.count(ActionItem.id), open_items)
            .where(ActionItem.meeting_id.in_(meeting_ids))
            .group_by(ActionItem.meeting_id)
        )
        return {meeting_id: (total, int(open_count or 0)) for meeting_id, total, open_count in rows}

    def get(self, meeting_id: int) -> Meeting | None:
        return self.session.scalar(
            select(Meeting)
            .where(Meeting.id == meeting_id)
            .options(
                selectinload(Meeting.participants),
                selectinload(Meeting.summary).selectinload(Summary.keywords),
            )
        )

    def segments(self, meeting_id: int) -> list[TranscriptSegment]:
        return list(
            self.session.scalars(
                select(TranscriptSegment)
                .where(TranscriptSegment.meeting_id == meeting_id)
                .order_by(TranscriptSegment.sequence)
                .options(selectinload(TranscriptSegment.speaker))
            )
        )

    def speaker_ids(self, meeting_id: int) -> set[int]:
        return set(
            self.session.scalars(
                select(TranscriptSegment.speaker_id)
                .where(TranscriptSegment.meeting_id == meeting_id)
                .distinct()
            )
        )

    def talk_time(self, meeting_id: int) -> list[tuple[Participant, int]]:
        spoken = func.sum(TranscriptSegment.end_ms - TranscriptSegment.start_ms)
        rows = self.session.execute(
            select(Participant, spoken)
            .join(TranscriptSegment, TranscriptSegment.speaker_id == Participant.id)
            .where(TranscriptSegment.meeting_id == meeting_id)
            .group_by(Participant.id)
            .order_by(spoken.desc())
        )
        return [(participant, int(total or 0)) for participant, total in rows.tuples()]

    def get_summary(self, meeting_id: int) -> Summary | None:
        return self.session.scalar(
            select(Summary)
            .where(Summary.meeting_id == meeting_id)
            .options(selectinload(Summary.topics), selectinload(Summary.keywords))
        )

    def add(self, meeting: Meeting) -> Meeting:
        self.session.add(meeting)
        self.session.flush()
        return meeting

    def delete(self, meeting: Meeting) -> None:
        self.session.delete(meeting)
