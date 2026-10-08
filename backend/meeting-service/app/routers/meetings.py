"""Meetings, their transcript, summary and action items. HTTP only — rules live in the services."""

from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencies import SessionDep
from app.repositories.meetings import MeetingFilters, SortOrder
from app.schemas.action_items import ActionItemCreate, ActionItemOut
from app.schemas.common import ErrorResponse
from app.schemas.meetings import (
    MeetingCreate,
    MeetingDetail,
    MeetingList,
    MeetingUpdate,
    ProcessingState,
    SummaryOut,
    TranscriptOut,
)
from app.services.action_items import ActionItemService
from app.services.meetings import MeetingService

router = APIRouter(prefix="/api/meetings", tags=["meetings"])

NOT_FOUND: dict[int | str, dict[str, Any]] = {404: {"model": ErrorResponse}}
INVALID: dict[int | str, dict[str, Any]] = {422: {"model": ErrorResponse}}


def get_meeting_service(session: SessionDep) -> MeetingService:
    return MeetingService(session)


def get_action_item_service(session: SessionDep) -> ActionItemService:
    return ActionItemService(session)


Meetings = Annotated[MeetingService, Depends(get_meeting_service)]
ActionItems = Annotated[ActionItemService, Depends(get_action_item_service)]


@router.get("", response_model=MeetingList, responses=INVALID)
def list_meetings(
    service: Meetings,
    q: Annotated[str | None, Query(max_length=100, description="Title contains")] = None,
    participant_id: Annotated[list[int], Query(description="ANY of these people")] = [],  # noqa: B006
    date_from: Annotated[date | None, Query(description="Inclusive (UTC)")] = None,
    date_to: Annotated[date | None, Query(description="Inclusive (UTC)")] = None,
    keyword: Annotated[str | None, Query(max_length=64, description="Tagged with")] = None,
    sort: SortOrder = "-meeting_date",
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> MeetingList:
    filters = MeetingFilters(q, participant_id, date_from, date_to, keyword, sort, limit, offset)
    return service.list_meetings(filters)


@router.post(
    "",
    response_model=MeetingDetail,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, **INVALID},
)
def create_meeting(data: MeetingCreate, service: Meetings) -> MeetingDetail:
    """Create from a form, pasted text or an uploaded file's contents (`transcript_format`)."""
    return service.create_meeting(data)


@router.get("/{meeting_id}", response_model=MeetingDetail, responses=NOT_FOUND)
def get_meeting(meeting_id: int, service: Meetings) -> MeetingDetail:
    return service.get_meeting(meeting_id)


@router.patch(
    "/{meeting_id}",
    response_model=MeetingDetail,
    responses={**NOT_FOUND, 409: {"model": ErrorResponse}, **INVALID},
)
def update_meeting(meeting_id: int, data: MeetingUpdate, service: Meetings) -> MeetingDetail:
    return service.update_meeting(meeting_id, data)


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND)
def delete_meeting(meeting_id: int, service: Meetings) -> Response:
    service.delete_meeting(meeting_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{meeting_id}/transcript", response_model=TranscriptOut, responses=NOT_FOUND)
def get_transcript(meeting_id: int, service: Meetings) -> TranscriptOut:
    return service.get_transcript(meeting_id)


@router.get("/{meeting_id}/summary", response_model=SummaryOut, responses=NOT_FOUND)
def get_summary(meeting_id: int, service: Meetings) -> SummaryOut:
    return service.get_summary(meeting_id)


@router.post(
    "/{meeting_id}/summary/regenerate",
    response_model=ProcessingState,
    status_code=status.HTTP_202_ACCEPTED,
    responses={**NOT_FOUND, 409: {"model": ErrorResponse}},
)
def regenerate_summary(meeting_id: int, service: Meetings) -> ProcessingState:
    """Queue a new AI summary. 202: the work happens asynchronously."""
    return service.regenerate_summary(meeting_id)


@router.get("/{meeting_id}/action-items", response_model=list[ActionItemOut], responses=NOT_FOUND)
def list_action_items(meeting_id: int, service: ActionItems) -> list[ActionItemOut]:
    return service.list_items(meeting_id)


@router.post(
    "/{meeting_id}/action-items",
    response_model=ActionItemOut,
    status_code=status.HTTP_201_CREATED,
    responses={**NOT_FOUND, **INVALID},
)
def create_action_item(
    meeting_id: int, data: ActionItemCreate, service: ActionItems
) -> ActionItemOut:
    return service.create_item(meeting_id, data)
