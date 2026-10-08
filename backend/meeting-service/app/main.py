"""Application factory for the Meeting Service.

Run locally:  uvicorn app.main:create_app --factory --reload --port 8000
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.database import Database
from app.errors import register_exception_handlers
from app.migrations import upgrade_to_head
from app.routers import action_items, health, meetings, participants
from app.seed.loader import seed_database


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=settings.log_level)
    database = Database(settings.database_url)
    if settings.run_migrations_on_startup:
        # A fresh deployment needs no manual step; Alembic is a no-op when already at head.
        upgrade_to_head(settings.database_url)
    if settings.seed_on_startup:
        with database.session_factory() as session:
            seed_database(session, datetime.now(UTC))

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
    app.include_router(meetings.router)
    app.include_router(action_items.router)
    app.include_router(participants.router)
    return app
