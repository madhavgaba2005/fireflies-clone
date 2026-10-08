from fastapi import APIRouter

from app.routers.meetings import Meetings
from app.schemas.meetings import ParticipantWithCount

router = APIRouter(prefix="/api/participants", tags=["participants"])


@router.get("", response_model=list[ParticipantWithCount])
def list_participants(service: Meetings) -> list[ParticipantWithCount]:
    """Everyone in the workspace, with how many meetings they attended (for filters and pickers)."""
    return service.list_participants()
