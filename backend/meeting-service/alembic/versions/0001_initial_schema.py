"""initial schema

Revision ID: 0c7317848580
Revises:
Create Date: 2026-10-09 00:49:46.417078
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

import app.models.types

revision: str = "0c7317848580"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "meetings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("meeting_date", app.models.types.UTCDateTime(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("processing_status", sa.String(length=16), nullable=False),
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column("transcript_revision", sa.Integer(), nullable=False),
        sa.Column("media_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", app.models.types.UTCDateTime(), nullable=False),
        sa.Column("updated_at", app.models.types.UTCDateTime(), nullable=False),
        sa.CheckConstraint(
            "processing_status IN ('not_requested', 'pending', 'processing', 'completed', 'failed')",
            name="ck_meetings_processing_status",
        ),
        sa.CheckConstraint(
            "source IN ('seed', 'upload', 'paste', 'form')", name="ck_meetings_source"
        ),
        sa.CheckConstraint("duration_seconds >= 0", name="ck_meetings_duration"),
        sa.CheckConstraint("length(trim(title)) > 0", name="ck_meetings_title"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("meetings", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_meetings_meeting_date"), ["meeting_date"], unique=False
        )

    op.create_table(
        "outbox_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("aggregate_id", sa.String(length=64), nullable=False),
        sa.Column("envelope", sa.Text(), nullable=False),
        sa.Column("created_at", app.models.types.UTCDateTime(), nullable=False),
        sa.Column("published_at", app.models.types.UTCDateTime(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("outbox_events", schema=None) as batch_op:
        batch_op.create_index(
            "ix_outbox_unpublished",
            ["created_at"],
            unique=False,
            sqlite_where=sa.text("published_at IS NULL"),
        )

    op.create_table(
        "participants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100, collation="NOCASE"), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=True),
        sa.Column("created_at", app.models.types.UTCDateTime(), nullable=False),
        sa.CheckConstraint("length(trim(name)) > 0", name="ck_participants_name"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "processed_events",
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("processed_at", app.models.types.UTCDateTime(), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_table(
        "action_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("assignee_id", sa.Integer(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("completed_at", app.models.types.UTCDateTime(), nullable=True),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("start_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", app.models.types.UTCDateTime(), nullable=False),
        sa.Column("updated_at", app.models.types.UTCDateTime(), nullable=False),
        sa.CheckConstraint("source IN ('ai', 'manual')", name="ck_action_items_source"),
        sa.CheckConstraint(
            "(completed = 1 AND completed_at IS NOT NULL) OR (completed = 0 AND completed_at IS NULL)",
            name="ck_action_items_completed_at",
        ),
        sa.CheckConstraint("length(trim(title)) > 0", name="ck_action_items_title"),
        sa.CheckConstraint("start_ms IS NULL OR start_ms >= 0", name="ck_action_items_start"),
        sa.ForeignKeyConstraint(["assignee_id"], ["participants.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("action_items", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_action_items_assignee_id"), ["assignee_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_action_items_meeting_id"), ["meeting_id"], unique=False
        )

    op.create_table(
        "meeting_participants",
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("participant_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["participant_id"], ["participants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("meeting_id", "participant_id"),
    )
    with op.batch_alter_table("meeting_participants", schema=None) as batch_op:
        batch_op.create_index(
            "ix_meeting_participants_participant_id", ["participant_id"], unique=False
        )

    op.create_table(
        "summaries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("overview", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("transcript_revision", sa.Integer(), nullable=False),
        sa.Column("generated_at", app.models.types.UTCDateTime(), nullable=False),
        sa.Column("updated_at", app.models.types.UTCDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meeting_id"),
    )
    op.create_table(
        "transcript_segments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("speaker_id", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("start_ms", sa.Integer(), nullable=False),
        sa.Column("end_ms", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.CheckConstraint("end_ms >= start_ms", name="ck_segments_end"),
        sa.CheckConstraint("start_ms >= 0", name="ck_segments_start"),
        sa.ForeignKeyConstraint(["meeting_id"], ["meetings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["speaker_id"], ["participants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meeting_id", "sequence", name="uq_segments_meeting_sequence"),
    )
    with op.batch_alter_table("transcript_segments", schema=None) as batch_op:
        batch_op.create_index("ix_transcript_segments_speaker_id", ["speaker_id"], unique=False)

    op.create_table(
        "summary_keywords",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("summary_id", sa.Integer(), nullable=False),
        sa.Column("keyword", sa.String(length=64, collation="NOCASE"), nullable=False),
        sa.ForeignKeyConstraint(["summary_id"], ["summaries.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("summary_id", "keyword", name="uq_keywords_summary_keyword"),
    )
    with op.batch_alter_table("summary_keywords", schema=None) as batch_op:
        batch_op.create_index("ix_summary_keywords_keyword", ["keyword"], unique=False)

    op.create_table(
        "summary_topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("summary_id", sa.Integer(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("start_ms", sa.Integer(), nullable=True),
        sa.CheckConstraint("start_ms IS NULL OR start_ms >= 0", name="ck_topics_start"),
        sa.ForeignKeyConstraint(["summary_id"], ["summaries.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("summary_id", "sequence", name="uq_topics_summary_sequence"),
    )


def downgrade() -> None:
    op.drop_table("summary_topics")
    with op.batch_alter_table("summary_keywords", schema=None) as batch_op:
        batch_op.drop_index("ix_summary_keywords_keyword")

    op.drop_table("summary_keywords")
    with op.batch_alter_table("transcript_segments", schema=None) as batch_op:
        batch_op.drop_index("ix_transcript_segments_speaker_id")

    op.drop_table("transcript_segments")
    op.drop_table("summaries")
    with op.batch_alter_table("meeting_participants", schema=None) as batch_op:
        batch_op.drop_index("ix_meeting_participants_participant_id")

    op.drop_table("meeting_participants")
    with op.batch_alter_table("action_items", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_action_items_meeting_id"))
        batch_op.drop_index(batch_op.f("ix_action_items_assignee_id"))

    op.drop_table("action_items")
    op.drop_table("processed_events")
    op.drop_table("participants")
    with op.batch_alter_table("outbox_events", schema=None) as batch_op:
        batch_op.drop_index("ix_outbox_unpublished", sqlite_where=sa.text("published_at IS NULL"))

    op.drop_table("outbox_events")
    with op.batch_alter_table("meetings", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_meetings_meeting_date"))

    op.drop_table("meetings")
