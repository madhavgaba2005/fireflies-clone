from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Participant, meeting_participants


class ParticipantRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_many(self, ids: Iterable[int]) -> list[Participant]:
        wanted = set(ids)
        if not wanted:
            return []
        return list(self.session.scalars(select(Participant).where(Participant.id.in_(wanted))))

    def get_by_name(self, name: str) -> Participant | None:
        # The column is COLLATE NOCASE, so this comparison is case-insensitive.
        return self.session.scalar(select(Participant).where(Participant.name == name.strip()))

    def get_or_create(self, name: str, email: str | None = None) -> Participant:
        participant = self.get_by_name(name)
        if participant is None:
            participant = Participant(name=name.strip(), email=email or None)
            self.session.add(participant)
            self.session.flush()
        elif email and not participant.email:
            participant.email = email
        return participant

    def list_with_meeting_counts(self) -> list[tuple[Participant, int]]:
        count = func.count(meeting_participants.c.meeting_id)
        rows = self.session.execute(
            select(Participant, count)
            .outerjoin(
                meeting_participants, meeting_participants.c.participant_id == Participant.id
            )
            .group_by(Participant.id)
            .order_by(Participant.name)
        )
        return [(participant, meetings) for participant, meetings in rows.tuples()]
