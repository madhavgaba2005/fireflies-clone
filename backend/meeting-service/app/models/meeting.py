"""Domain models: meetings, participants, transcript segments, summaries and action items.

See docs/DATABASE_DESIGN.md for the ER diagram and the reasoning behind each constraint.
"""

from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.types import UTCDateTime, utcnow


class ProcessingStatus(StrEnum):
    NOT_REQUESTED = "not_requested"  # no transcript → nothing to summarize
    PENDING = "pending"  # request committed to the outbox
    PROCESSING = "processing"  # request handed to Kafka / the AI service
    COMPLETED = "completed"
    FAILED = "failed"


class MeetingSource(StrEnum):
    SEED = "seed"
    UPLOAD = "upload"
    PASTE = "paste"
    FORM = "form"


class ActionItemSource(StrEnum):
    AI = "ai"
    MANUAL = "manual"


def _check_in(column: str, enum: type[StrEnum]) -> str:
    values = ", ".join(f"'{member.value}'" for member in enum)
    return f"{column} IN ({values})"


meeting_participants = Table(
    "meeting_participants",
    Base.metadata,
    Column("meeting_id", ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True),
    Column("participant_id", ForeignKey("participants.id", ondelete="RESTRICT"), primary_key=True),
    # The composite PK serves "participants of meeting X"; this serves "meetings of participant X".
    Index("ix_meeting_participants_participant_id", "participant_id"),
)


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    # NOCASE: "priya sharma" in an uploaded transcript resolves to the existing "Priya Sharma".
    name: Mapped[str] = mapped_column(String(100, collation="NOCASE"), unique=True)
    email: Mapped[str | None] = mapped_column(String(254), unique=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    meetings: Mapped[list["Meeting"]] = relationship(
        secondary=meeting_participants, back_populates="participants"
    )

    __table_args__ = (CheckConstraint("length(trim(name)) > 0", name="ck_participants_name"),)


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    meeting_date: Mapped[datetime] = mapped_column(UTCDateTime, index=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[MeetingSource] = mapped_column(String(16), default=MeetingSource.FORM)
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        String(16), default=ProcessingStatus.NOT_REQUESTED
    )
    processing_error: Mapped[str | None] = mapped_column(Text)
    # Bumped on every transcript change; results for an older revision are discarded.
    transcript_revision: Mapped[int] = mapped_column(Integer, default=0)
    media_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)

    participants: Mapped[list[Participant]] = relationship(
        secondary=meeting_participants, back_populates="meetings", order_by="Participant.name"
    )
    segments: Mapped[list["TranscriptSegment"]] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="TranscriptSegment.sequence",
    )
    summary: Mapped["Summary | None"] = relationship(
        back_populates="meeting", cascade="all, delete-orphan", passive_deletes=True
    )
    action_items: Mapped[list["ActionItem"]] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ActionItem.id",
    )

    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="ck_meetings_title"),
        CheckConstraint("duration_seconds >= 0", name="ck_meetings_duration"),
        CheckConstraint(_check_in("source", MeetingSource), name="ck_meetings_source"),
        CheckConstraint(
            _check_in("processing_status", ProcessingStatus), name="ck_meetings_processing_status"
        ),
    )


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(ForeignKey("meetings.id", ondelete="CASCADE"))
    speaker_id: Mapped[int] = mapped_column(ForeignKey("participants.id", ondelete="RESTRICT"))
    sequence: Mapped[int] = mapped_column(Integer)
    start_ms: Mapped[int] = mapped_column(Integer)
    end_ms: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)

    meeting: Mapped[Meeting] = relationship(back_populates="segments")
    speaker: Mapped[Participant] = relationship()

    __table_args__ = (
        # Deterministic order; also the index for "transcript of meeting X".
        UniqueConstraint("meeting_id", "sequence", name="uq_segments_meeting_sequence"),
        CheckConstraint("start_ms >= 0", name="ck_segments_start"),
        CheckConstraint("end_ms >= start_ms", name="ck_segments_end"),
        Index("ix_transcript_segments_speaker_id", "speaker_id"),
    )


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    # UNIQUE enforces 1:1 — regeneration updates this row instead of inserting another.
    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), unique=True
    )
    overview: Mapped[str] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(32))
    transcript_revision: Mapped[int] = mapped_column(Integer)
    generated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)

    meeting: Mapped[Meeting] = relationship(back_populates="summary")
    topics: Mapped[list["SummaryTopic"]] = relationship(
        back_populates="summary_ref",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SummaryTopic.sequence",
    )
    keywords: Mapped[list["SummaryKeyword"]] = relationship(
        back_populates="summary",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="SummaryKeyword.id",
    )


class SummaryTopic(Base):
    """One chapter of the outline; `start_ms` lets the UI seek the player to it."""

    __tablename__ = "summary_topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    summary_id: Mapped[int] = mapped_column(ForeignKey("summaries.id", ondelete="CASCADE"))
    sequence: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text)
    start_ms: Mapped[int | None] = mapped_column(Integer)

    summary_ref: Mapped[Summary] = relationship(back_populates="topics")

    __table_args__ = (
        UniqueConstraint("summary_id", "sequence", name="uq_topics_summary_sequence"),
        CheckConstraint("start_ms IS NULL OR start_ms >= 0", name="ck_topics_start"),
    )


class SummaryKeyword(Base):
    __tablename__ = "summary_keywords"

    id: Mapped[int] = mapped_column(primary_key=True)
    summary_id: Mapped[int] = mapped_column(ForeignKey("summaries.id", ondelete="CASCADE"))
    keyword: Mapped[str] = mapped_column(String(64, collation="NOCASE"))

    summary: Mapped[Summary] = relationship(back_populates="keywords")

    __table_args__ = (
        UniqueConstraint("summary_id", "keyword", name="uq_keywords_summary_keyword"),
        Index("ix_summary_keywords_keyword", "keyword"),  # tag filter (bonus)
    )


class ActionItem(Base):
    __tablename__ = "action_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[int] = mapped_column(
        ForeignKey("meetings.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("participants.id", ondelete="SET NULL"), index=True
    )
    due_date: Mapped[date | None] = mapped_column(Date)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    # AI items are replaced on regeneration; anything the user touched becomes manual and is kept.
    source: Mapped[ActionItemSource] = mapped_column(String(16), default=ActionItemSource.MANUAL)
    start_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)

    meeting: Mapped[Meeting] = relationship(back_populates="action_items")
    assignee: Mapped[Participant | None] = relationship()

    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="ck_action_items_title"),
        CheckConstraint(_check_in("source", ActionItemSource), name="ck_action_items_source"),
        CheckConstraint(
            "(completed = 1 AND completed_at IS NOT NULL)"
            " OR (completed = 0 AND completed_at IS NULL)",
            name="ck_action_items_completed_at",
        ),
        CheckConstraint("start_ms IS NULL OR start_ms >= 0", name="ck_action_items_start"),
    )
