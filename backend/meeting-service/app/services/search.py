"""Global search (bonus): one result per meeting, with the transcript moments that matched."""

from sqlalchemy.orm import Session

from app.repositories.search import SearchRepository
from app.schemas.search import SearchHit, SearchMeetingResult, SearchResponse

SNIPPET_CONTEXT = 60  # characters kept on each side of the match


def snippet(text: str, query: str, context: int = SNIPPET_CONTEXT) -> str:
    """The match with surrounding words, never cutting a word in half, with ellipses."""
    index = text.lower().find(query.lower())
    if index < 0 or len(text) <= 2 * context + len(query):
        return text
    start = max(0, index - context)
    end = min(len(text), index + len(query) + context)
    if start > 0:
        space = text.find(" ", start, index)
        start = space + 1 if space != -1 else start
    if end < len(text):
        space = text.rfind(" ", index + len(query), end)
        end = space if space != -1 else end
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return prefix + text[start:end].strip() + suffix


class SearchService:
    def __init__(self, session: Session) -> None:
        self.repository = SearchRepository(session)

    def search(self, query: str, *, max_meetings: int = 10, max_hits: int = 50) -> SearchResponse:
        query = query.strip()
        results: dict[int, SearchMeetingResult] = {}

        for meeting in self.repository.meetings_by_title(query, max_meetings):
            results[meeting.id] = SearchMeetingResult(
                meeting_id=meeting.id,
                title=meeting.title,
                meeting_date=meeting.meeting_date,
                title_match=True,
                hits=[],
            )

        segments = self.repository.segments_by_text(query, max_hits)
        for segment in segments:
            result = results.get(segment.meeting_id)
            if result is None:
                if len(results) >= max_meetings:
                    continue
                result = results[segment.meeting_id] = SearchMeetingResult(
                    meeting_id=segment.meeting_id,
                    title=segment.meeting.title,
                    meeting_date=segment.meeting.meeting_date,
                    title_match=False,
                    hits=[],
                )
            result.hits.append(
                SearchHit(
                    segment_id=segment.id,
                    start_ms=segment.start_ms,
                    speaker=segment.speaker.name,
                    snippet=snippet(segment.text, query),
                )
            )

        ordered = sorted(results.values(), key=lambda r: r.meeting_date, reverse=True)
        return SearchResponse(
            query=query,
            results=ordered,
            total_hits=sum(len(r.hits) for r in ordered),
            truncated=len(segments) >= max_hits,
        )
