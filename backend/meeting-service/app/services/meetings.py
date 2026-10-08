"""Meeting use cases: list, create, read, update, delete, transcript, summary, regenerate."""

import math

from sqlalchemy.orm import Session

from app.errors import ConflictError, DomainError, NotFoundError, UnprocessableError
from app.events.envelope import EventType
from app.models import Meeting, MeetingSource, Participant, ProcessingStatus, TranscriptSegment
from app.repositories.meetings import MeetingFilters, MeetingRepository
from app.repositories.participants import ParticipantRepository
from app.schemas.meetings import (
    MeetingCreate,
    MeetingDetail,
    MeetingList,
    MeetingListItem,
    MeetingUpdate,
    ParticipantRef,
    ParticipantWithCount,
    ProcessingState,
    SegmentOut,
    SpeakerStat,
    SummaryOut,
    TopicOut,
    TranscriptOut,
)
from app.services.processing import queue_processing
from app.services.transcript_parser import TranscriptParseError, parse_transcript


def _list_item(meeting: Meeting, counts: tuple[int, int]) -> MeetingListItem:
    item = MeetingListItem.model_validate(meeting)
    item.keywords = [k.keyword for k in meeting.summary.keywords] if meeting.summary else []
    item.action_item_count, item.open_action_item_count = counts
    return item


class MeetingService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.meetings = MeetingRepository(session)
        self.participants = ParticipantRepository(session)

    # --- queries -------------------------------------------------------------------------------

    def list_meetings(self, filters: MeetingFilters) -> MeetingList:
        if filters.date_from and filters.date_to and filters.date_from > filters.date_to:
            raise UnprocessableError(
                "date_from must not be after date_to", code="invalid_date_range"
            )
        meetings, total = self.meetings.search(filters)
        counts = self.meetings.action_item_counts([m.id for m in meetings])
        return MeetingList(
            items=[_list_item(m, counts.get(m.id, (0, 0))) for m in meetings],
            total=total,
            limit=filters.limit,
            offset=filters.offset,
        )

    def get_meeting(self, meeting_id: int) -> MeetingDetail:
        meeting = self._get_or_404(meeting_id)
        counts = self.meetings.action_item_counts([meeting_id]).get(meeting_id, (0, 0))
        detail = MeetingDetail.model_validate(meeting)
        base = _list_item(meeting, counts)
        detail.keywords = base.keywords
        detail.action_item_count = base.action_item_count
        detail.open_action_item_count = base.open_action_item_count
        talk_time = self.meetings.talk_time(meeting_id)
        total_ms = sum(ms for _, ms in talk_time) or 1
        detail.speaker_stats = [
            SpeakerStat(
                participant_id=participant.id,
                name=participant.name,
                talk_time_ms=ms,
                percentage=round(100 * ms / total_ms, 1),
            )
            for participant, ms in talk_time
        ]
        return detail

    def get_transcript(self, meeting_id: int) -> TranscriptOut:
        meeting = self._get_or_404(meeting_id)
        segments = self.meetings.segments(meeting_id)
        return TranscriptOut(
            meeting_id=meeting_id,
            revision=meeting.transcript_revision,
            segments=[SegmentOut.model_validate(segment) for segment in segments],
        )

    def get_summary(self, meeting_id: int) -> SummaryOut:
        self._get_or_404(meeting_id)
        summary = self.meetings.get_summary(meeting_id)
        if summary is None:
            raise NotFoundError("This meeting has no summary yet", code="summary_not_found")
        return SummaryOut(
            meeting_id=meeting_id,
            overview=summary.overview,
            provider=summary.provider,
            transcript_revision=summary.transcript_revision,
            generated_at=summary.generated_at,
            topics=[TopicOut.model_validate(topic) for topic in summary.topics],
            keywords=[keyword.keyword for keyword in summary.keywords],
        )

    def list_participants(self) -> list[ParticipantWithCount]:
        return [
            ParticipantWithCount(id=p.id, name=p.name, email=p.email, meeting_count=count)
            for p, count in self.participants.list_with_meeting_counts()
        ]

    # --- commands ------------------------------------------------------------------------------

    def create_meeting(self, data: MeetingCreate) -> MeetingDetail:
        parsed = []
        if data.transcript_text and data.transcript_text.strip():
            try:
                parsed = parse_transcript(data.transcript_text, data.transcript_format)
            except TranscriptParseError as exc:
                raise DomainError(
                    str(exc), code="transcript_invalid", details={"line": exc.line}
                ) from exc

        participants = self._resolve(data.participants)
        speakers: dict[str, Participant] = {}
        for segment in parsed:
            key = segment.speaker.casefold()
            if key not in speakers:
                speakers[key] = self.participants.get_or_create(segment.speaker)
        for speaker in speakers.values():  # speakers are always participants of their meeting
            if speaker not in participants:
                participants.append(speaker)

        transcript_seconds = math.ceil(parsed[-1].end_ms / 1000) if parsed else 0
        meeting = Meeting(
            title=data.title,
            meeting_date=data.meeting_date,
            duration_seconds=max(data.duration_seconds or 0, transcript_seconds),
            source=MeetingSource(data.source),
            processing_status=ProcessingStatus.NOT_REQUESTED,
            transcript_revision=1 if parsed else 0,
            participants=participants,
        )
        meeting.segments = [
            TranscriptSegment(
                speaker=speakers[segment.speaker.casefold()],
                sequence=index,
                start_ms=segment.start_ms,
                end_ms=segment.end_ms,
                text=segment.text,
            )
            for index, segment in enumerate(parsed)
        ]
        self.meetings.add(meeting)
        if meeting.segments:
            queue_processing(self.session, meeting, meeting.segments, EventType.MEETING_CREATED)
        self.session.commit()
        return self.get_meeting(meeting.id)

    def update_meeting(self, meeting_id: int, data: MeetingUpdate) -> MeetingDetail:
        meeting = self._get_or_404(meeting_id)
        if data.title is not None:
            meeting.title = data.title
        if data.meeting_date is not None:
            meeting.meeting_date = data.meeting_date
        if data.participants is not None:
            self._replace_participants(meeting, self._resolve(data.participants))
        self.session.commit()
        return self.get_meeting(meeting_id)

    def delete_meeting(self, meeting_id: int) -> None:
        self.meetings.delete(self._get_or_404(meeting_id))
        self.session.commit()

    def regenerate_summary(self, meeting_id: int) -> ProcessingState:
        meeting = self._get_or_404(meeting_id)
        segments = self.meetings.segments(meeting_id)
        if not segments:
            raise ConflictError("This meeting has no transcript to summarize", code="no_transcript")
        queue_processing(self.session, meeting, segments, EventType.SUMMARY_REQUESTED)
        self.session.commit()
        return ProcessingState(meeting_id=meeting_id, processing_status=meeting.processing_status)

    # --- helpers -------------------------------------------------------------------------------

    def _get_or_404(self, meeting_id: int) -> Meeting:
        meeting = self.meetings.get(meeting_id)
        if meeting is None:
            raise NotFoundError(f"Meeting {meeting_id} not found", code="meeting_not_found")
        return meeting

    def _resolve(self, refs: list[ParticipantRef]) -> list[Participant]:
        by_id = {p.id: p for p in self.participants.get_many(r.id for r in refs if r.id)}
        missing = sorted({r.id for r in refs if r.id} - by_id.keys())
        if missing:
            raise UnprocessableError(
                "Unknown participant id(s)", code="participant_not_found", details={"ids": missing}
            )
        resolved: list[Participant] = []
        for ref in refs:
            if ref.id:
                participant = by_id[ref.id]
            else:
                assert ref.name is not None  # guaranteed by ParticipantRef validation
                participant = self.participants.get_or_create(ref.name, ref.email)
            if participant not in resolved:
                resolved.append(participant)
        return resolved

    def _replace_participants(self, meeting: Meeting, wanted: list[Participant]) -> None:
        removed = {p.id for p in meeting.participants} - {p.id for p in wanted}
        speaking = removed & self.meetings.speaker_ids(meeting.id)
        if speaking:
            names = sorted(p.name for p in meeting.participants if p.id in speaking)
            raise ConflictError(
                "Speakers in the transcript can't be removed from the meeting",
                code="participant_has_transcript_lines",
                details={"participants": names},
            )
        for item in meeting.action_items:  # an assignee must belong to the meeting
            if item.assignee_id in removed:
                item.assignee_id = None
        meeting.participants = wanted
