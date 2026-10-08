"""API contracts for meetings, participants, transcripts and summaries."""

from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.models import MeetingSource, ProcessingStatus

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
PersonName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Email = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
]

MAX_TRANSCRIPT_CHARS = 300_000
MAX_PARTICIPANTS = 50


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- participants ----------------------------------------------------------------------------


class ParticipantOut(ORMModel):
    id: int
    name: str
    email: str | None


class ParticipantWithCount(ParticipantOut):
    meeting_count: int


class ParticipantRef(BaseModel):
    """An existing participant (`id`) or a person to find-or-create by `name`."""

    id: int | None = Field(default=None, ge=1)
    name: PersonName | None = None
    email: Email | None = None

    @model_validator(mode="after")
    def _id_or_name(self) -> Self:
        if self.id is None and self.name is None:
            raise ValueError("Each participant needs an id or a name")
        return self


# --- meetings ------------------------------------------------------------------------------


class MeetingCreate(BaseModel):
    title: Title
    meeting_date: AwareDatetime
    participants: list[ParticipantRef] = Field(default_factory=list, max_length=MAX_PARTICIPANTS)
    duration_seconds: int | None = Field(default=None, ge=0, le=24 * 3600)
    transcript_text: str | None = Field(default=None, max_length=MAX_TRANSCRIPT_CHARS)
    transcript_format: Literal["txt", "vtt", "json"] = "txt"
    source: Literal["upload", "paste", "form"] = "form"


class MeetingUpdate(BaseModel):
    """Every field is optional; `participants` is the complete desired list (replace semantics)."""

    title: Title | None = None
    meeting_date: AwareDatetime | None = None
    participants: list[ParticipantRef] | None = Field(default=None, max_length=MAX_PARTICIPANTS)


class MeetingListItem(ORMModel):
    id: int
    title: str
    meeting_date: datetime
    duration_seconds: int
    source: MeetingSource
    processing_status: ProcessingStatus
    participants: list[ParticipantOut]
    keywords: list[str] = Field(default_factory=list)
    action_item_count: int = 0
    open_action_item_count: int = 0


class MeetingList(BaseModel):
    items: list[MeetingListItem]
    total: int
    limit: int
    offset: int


class SpeakerStat(BaseModel):
    participant_id: int
    name: str
    talk_time_ms: int
    percentage: float


class MeetingDetail(MeetingListItem):
    processing_error: str | None
    transcript_revision: int
    media_url: str | None
    created_at: datetime
    updated_at: datetime
    speaker_stats: list[SpeakerStat] = Field(default_factory=list)


class ProcessingState(BaseModel):
    meeting_id: int
    processing_status: ProcessingStatus


# --- transcript & summary ---------------------------------------------------------------------


class SpeakerOut(ORMModel):
    id: int
    name: str


class SegmentOut(ORMModel):
    id: int
    sequence: int
    start_ms: int
    end_ms: int
    speaker: SpeakerOut
    text: str


class TranscriptOut(BaseModel):
    meeting_id: int
    revision: int
    segments: list[SegmentOut]


class TopicOut(ORMModel):
    sequence: int
    title: str
    summary: str
    start_ms: int | None


class SummaryOut(BaseModel):
    meeting_id: int
    overview: str
    provider: str
    transcript_revision: int
    generated_at: datetime
    topics: list[TopicOut]
    keywords: list[str]
