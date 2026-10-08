"""Application factory for the AI Processing Service.

Run locally:  uvicorn app.main:create_app --factory --reload --port 8001
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings, get_settings
from app.routers import health


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=settings.log_level)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        # Phase 6: in kafka mode, start the meeting.events consumer here.
        yield

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Stateless worker: transcript in, summary / topics / action items out.",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.include_router(health.router)
    return app
