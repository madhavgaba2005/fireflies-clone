"""HTTP fallback transport (PROCESSING_MODE=http): same envelope in, same result envelope out.

Only mounted in http mode, and only callable with the shared internal token — never by browsers.
"""

import secrets
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.events.envelope import EventEnvelope
from app.processors.meeting_processor import REQUEST_EVENTS, MeetingProcessor

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/process", response_model=EventEnvelope)
async def process(
    event: EventEnvelope,
    request: Request,
    x_internal_token: Annotated[str | None, Header()] = None,
) -> EventEnvelope:
    expected: str = request.app.state.settings.internal_api_token
    if not x_internal_token or not secrets.compare_digest(x_internal_token, expected):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid internal token")
    if event.event_type not in REQUEST_EVENTS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Not a processing request")
    processor: MeetingProcessor = request.app.state.processor
    return await processor.process(event)
