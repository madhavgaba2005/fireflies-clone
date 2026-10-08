from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import ActionItem


class ActionItemRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_meeting(self, meeting_id: int) -> list[ActionItem]:
        return list(
            self.session.scalars(
                select(ActionItem)
                .where(ActionItem.meeting_id == meeting_id)
                .order_by(ActionItem.id)
                .options(selectinload(ActionItem.assignee))
            )
        )

    def get(self, item_id: int) -> ActionItem | None:
        return self.session.scalar(
            select(ActionItem)
            .where(ActionItem.id == item_id)
            .options(selectinload(ActionItem.assignee))
        )

    def add(self, item: ActionItem) -> ActionItem:
        self.session.add(item)
        self.session.flush()
        return item

    def delete(self, item: ActionItem) -> None:
        self.session.delete(item)
