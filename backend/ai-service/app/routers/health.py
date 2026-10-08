"""Liveness probe. The AI service is stateless, so there is no database to check."""

from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    processing_mode: str
    summary_provider: str


@router.get("/health", response_model=HealthResponse)
def liveness(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        processing_mode=settings.processing_mode,
        summary_provider=settings.summary_provider,
    )
