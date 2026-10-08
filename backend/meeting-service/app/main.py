"""Application factory for the Meeting Service.

Run locally:  uvicorn app.main:create_app --factory --reload --port 8000
"""

import asyncio
import logging
from collections.abc import AsyncIterator, Coroutine
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.database import Database
from app.errors import register_exception_handlers
from app.events.consumer import ResultConsumer, apply_result_in_new_session
from app.events.envelope import EventEnvelope
from app.events.factory import build_publisher
from app.events.relay import OutboxRelay
from app.migrations import upgrade_to_head
from app.routers import action_items, health, meetings, participants
from app.seed.loader import seed_database

logger = logging.getLogger(__name__)
SHUTDOWN_TIMEOUT_SECONDS = 10


def background_workers(
    settings: Settings, database: Database, stop: asyncio.Event
) -> list[Coroutine[Any, Any, None]]:
    """kafka: outbox relay + result consumer · http: relay only (results come back in the
    response) · inline-test: nothing (tests drive the pipeline themselves)."""
    if settings.processing_mode == "inline-test":
        return []

    async def apply_result(event: EventEnvelope) -> None:
        await asyncio.to_thread(apply_result_in_new_session, database, event)

    publisher = build_publisher(settings, apply_result)
    relay = OutboxRelay(database, publisher, poll_interval=settings.outbox_poll_interval)
    workers = [relay.run_forever(stop)]
    if settings.processing_mode == "kafka":
        consumer = ResultConsumer(
            database,
            settings.kafka_bootstrap_servers,
            settings.kafka_result_topic,
            settings.kafka_consumer_group,
        )
        workers.append(consumer.run_forever(stop))
    return workers


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
        stop = asyncio.Event()
        tasks = [asyncio.create_task(w) for w in background_workers(settings, database, stop)]
        logger.info(
            "Processing mode %s: %d background worker(s)", settings.processing_mode, len(tasks)
        )
        yield
        stop.set()
        if tasks:
            _done, pending = await asyncio.wait(tasks, timeout=SHUTDOWN_TIMEOUT_SECONDS)
            for task in pending:
                task.cancel()
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
