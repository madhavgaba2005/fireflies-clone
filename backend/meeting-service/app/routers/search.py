from typing import Annotated

from fastapi import APIRouter, Query

from app.dependencies import SessionDep
from app.schemas.search import SearchResponse
from app.services.search import SearchService

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=SearchResponse)
def search(
    session: SessionDep,
    q: Annotated[str, Query(min_length=2, max_length=100, description="Words to find")],
) -> SearchResponse:
    """Search every meeting's title and transcript (bonus: global search).

    Returns one entry per meeting (newest first) with the matching transcript moments, each with a
    snippet and `start_ms`, so the UI can deep-link to `/meetings/{id}?t={start_ms}`.
    """
    return SearchService(session).search(q)
