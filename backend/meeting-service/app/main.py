"""Application factory for the Meeting Service.

Run locally:  uvicorn app.main:create_app --factory --reload --port 8000
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.database import Database
from app.errors import register_exception_handlers
from app.routers import health


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=settings.log_level)
    database = Database(settings.database_url)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        # Phase 5 starts the outbox relay and the AI-result consumer here.
        yield
        database.dispose()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="System of record for meetings, transcripts, summaries and action items.",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.db = database

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
        allow_headers=["Content-Type"],
    )
    register_exception_handlers(app)
    app.include_router(health.router)
    return app
