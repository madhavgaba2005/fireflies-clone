"""API contracts for action items."""

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.models import ActionItemSource
from app.schemas.meetings import ORMModel, ParticipantOut

ItemTitle = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]


class ActionItemCreate(BaseModel):
    title: ItemTitle
    description: Description | None = None
    assignee_id: int | None = Field(default=None, ge=1)
    due_date: date | None = None


class ActionItemUpdate(BaseModel):
    """Partial update: `"assignee_id": null` unassigns; an omitted field is left unchanged."""

    title: ItemTitle | None = None
    description: Description | None = None
    assignee_id: int | None = Field(default=None, ge=1)
    due_date: date | None = None
    completed: bool | None = None


class ActionItemOut(ORMModel):
    id: int
    meeting_id: int
    title: str
    description: str | None
    assignee: ParticipantOut | None
    due_date: date | None
    completed: bool
    completed_at: datetime | None
    source: ActionItemSource
    start_ms: int | None
    created_at: datetime
    updated_at: datetime
