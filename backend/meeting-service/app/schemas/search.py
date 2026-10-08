from datetime import datetime

from pydantic import BaseModel


class SearchHit(BaseModel):
    segment_id: int
    start_ms: int
    speaker: str
    snippet: str


class SearchMeetingResult(BaseModel):
    meeting_id: int
    title: str
    meeting_date: datetime
    title_match: bool
    hits: list[SearchHit]


class SearchResponse(BaseModel):
    query: str
    results: list[SearchMeetingResult]
    total_hits: int
    truncated: bool  # more transcript matches exist than were returned
