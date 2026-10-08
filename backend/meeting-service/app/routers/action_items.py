"""Action items addressed by their own id (they're globally unique, so no meeting in the path)."""

from fastapi import APIRouter, Response, status

from app.routers.meetings import INVALID, NOT_FOUND, ActionItems
from app.schemas.action_items import ActionItemOut, ActionItemUpdate

router = APIRouter(prefix="/api/action-items", tags=["action items"])


@router.patch("/{item_id}", response_model=ActionItemOut, responses={**NOT_FOUND, **INVALID})
def update_action_item(item_id: int, data: ActionItemUpdate, service: ActionItems) -> ActionItemOut:
    """Edit, complete (`"completed": true`) or uncomplete an item. Only sent fields change."""
    return service.update_item(item_id, data)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND)
def delete_action_item(item_id: int, service: ActionItems) -> Response:
    service.delete_item(item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
