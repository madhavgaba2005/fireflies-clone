"""Global search across meeting titles and transcript text.

Escaped LIKE = a full scan: fine for one workspace (hundreds of meetings, ~10k segments).
The scale-up path is SQLite FTS5 or PostgreSQL full-text search behind this same interface.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Meeting, TranscriptSegment
from app.repositories.meetings import _escape_like


class SearchRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def meetings_by_title(self, query: str, limit: int) -> list[Meeting]:
        pattern = f"%{_escape_like(query)}%"
        return list(
            self.session.scalars(
                select(Meeting)
                .where(Meeting.title.ilike(pattern, escape="\\"))
                .order_by(Meeting.meeting_date.desc())
                .limit(limit)
            )
        )

    def segments_by_text(self, query: str, limit: int) -> list[TranscriptSegment]:
        pattern = f"%{_escape_like(query)}%"
        return list(
            self.session.scalars(
                select(TranscriptSegment)
                .join(Meeting)
                .where(TranscriptSegment.text.ilike(pattern, escape="\\"))
                .order_by(Meeting.meeting_date.desc(), TranscriptSegment.sequence)
                .limit(limit)
                .options(
                    joinedload(TranscriptSegment.speaker), joinedload(TranscriptSegment.meeting)
                )
            )
        )
