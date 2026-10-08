"""Typed payloads carried inside the event envelope (contract v1).

The AI service keeps an identical copy; both are pinned by
tests/contract/payloads_v1.schema.json.
"""

from pydantic import BaseModel, Field


class ParticipantPayload(BaseModel):
    id: int
    name: str


class SegmentPayload(BaseModel):
    speaker_id: int
    speaker: str
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)
    text: str


class ProcessingRequestPayload(BaseModel):
    """meeting.created / transcript.updated / summary.requested — carries the whole transcript."""

    meeting_id: int
    transcript_revision: int
    title: str
    participants: list[ParticipantPayload]
    segments: list[SegmentPayload]


class TopicPayload(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    summary: str
    start_ms: int | None = Field(default=None, ge=0)


class ActionItemPayload(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    assignee_speaker_id: int | None = None
    start_ms: int | None = Field(default=None, ge=0)


class SummaryGeneratedPayload(BaseModel):
    meeting_id: int
    transcript_revision: int
    provider: str = Field(max_length=32)
    overview: str
    keywords: list[str] = Field(default_factory=list)
    topics: list[TopicPayload] = Field(default_factory=list)
    action_items: list[ActionItemPayload] = Field(default_factory=list)


class SummaryFailedPayload(BaseModel):
    meeting_id: int
    transcript_revision: int
    reason: str
    attempts: int = Field(ge=0)


CONTRACT_MODELS: dict[str, type[BaseModel]] = {
    "ProcessingRequestPayload": ProcessingRequestPayload,
    "SummaryGeneratedPayload": SummaryGeneratedPayload,
    "SummaryFailedPayload": SummaryFailedPayload,
}
