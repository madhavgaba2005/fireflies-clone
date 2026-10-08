"""Action item use cases. Rule: any user edit turns an AI item into a manual one, so
regenerating notes (which replaces AI items) never destroys the user's work."""

from sqlalchemy.orm import Session

from app.errors import NotFoundError, UnprocessableError
from app.models import ActionItem, ActionItemSource, Meeting
from app.models.types import utcnow
from app.repositories.action_items import ActionItemRepository
from app.repositories.meetings import MeetingRepository
from app.schemas.action_items import ActionItemCreate, ActionItemOut, ActionItemUpdate


class ActionItemService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.items = ActionItemRepository(session)
        self.meetings = MeetingRepository(session)

    def list_items(self, meeting_id: int) -> list[ActionItemOut]:
        self._meeting_or_404(meeting_id)
        return [ActionItemOut.model_validate(i) for i in self.items.list_for_meeting(meeting_id)]

    def create_item(self, meeting_id: int, data: ActionItemCreate) -> ActionItemOut:
        meeting = self._meeting_or_404(meeting_id)
        self._check_assignee(meeting, data.assignee_id)
        item = ActionItem(
            meeting_id=meeting_id,
            title=data.title,
            description=data.description or None,
            assignee_id=data.assignee_id,
            due_date=data.due_date,
            source=ActionItemSource.MANUAL,
        )
        self.items.add(item)
        self.session.commit()
        return self._out(item.id)

    def update_item(self, item_id: int, data: ActionItemUpdate) -> ActionItemOut:
        item = self._item_or_404(item_id)
        changes = data.model_fields_set  # distinguishes "assignee_id": null from "not sent"
        if "title" in changes and data.title is not None:
            item.title = data.title
        if "description" in changes:
            item.description = data.description or None
        if "assignee_id" in changes:
            self._check_assignee(item.meeting, data.assignee_id)
            item.assignee_id = data.assignee_id
        if "due_date" in changes:
            item.due_date = data.due_date
        if "completed" in changes and data.completed is not None:
            if data.completed and not item.completed:
                item.completed_at = utcnow()
            elif not data.completed:
                item.completed_at = None
            item.completed = data.completed
        if changes:
            item.source = ActionItemSource.MANUAL
        self.session.commit()
        return self._out(item_id)

    def delete_item(self, item_id: int) -> None:
        self.items.delete(self._item_or_404(item_id))
        self.session.commit()

    def _out(self, item_id: int) -> ActionItemOut:
        self.session.expire_all()  # reload relationships changed through foreign keys
        return ActionItemOut.model_validate(self._item_or_404(item_id))

    def _meeting_or_404(self, meeting_id: int) -> Meeting:
        meeting = self.meetings.get(meeting_id)
        if meeting is None:
            raise NotFoundError(f"Meeting {meeting_id} not found", code="meeting_not_found")
        return meeting

    def _item_or_404(self, item_id: int) -> ActionItem:
        item = self.items.get(item_id)
        if item is None:
            raise NotFoundError(f"Action item {item_id} not found", code="action_item_not_found")
        return item

    @staticmethod
    def _check_assignee(meeting: Meeting, assignee_id: int | None) -> None:
        if assignee_id is not None and assignee_id not in {p.id for p in meeting.participants}:
            raise UnprocessableError(
                "The assignee must be a participant of this meeting", code="invalid_assignee"
            )
