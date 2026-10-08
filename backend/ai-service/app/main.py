"""Application factory for the AI Processing Service.

Run locally:  uvicorn app.main:create_app --factory --reload --port 8001
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings, get_settings
from app.consumers.kafka_consumer import RequestConsumer
from app.processors.meeting_processor import MeetingProcessor
from app.providers import build_provider
from app.routers import health, internal

logger = logging.getLogger(__name__)
SHUTDOWN_TIMEOUT_SECONDS = 10


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=settings.log_level)
    processor = MeetingProcessor(
        build_provider(settings),
        max_retries=settings.max_retries,
        backoff_seconds=settings.retry_backoff_seconds,
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        stop = asyncio.Event()
        task = None
        if settings.processing_mode == "kafka":
            consumer = RequestConsumer(
                processor,
                settings.kafka_bootstrap_servers,
                settings.kafka_request_topic,
                settings.kafka_result_topic,
                settings.kafka_consumer_group,
            )
            task = asyncio.create_task(consumer.run_forever(stop))
        logger.info("AI service running in %s mode", settings.processing_mode)
        yield
        stop.set()
        if task is not None:
            _done, pending = await asyncio.wait({task}, timeout=SHUTDOWN_TIMEOUT_SECONDS)
            for leftover in pending:
                leftover.cancel()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Stateless worker: transcript in, summary / topics / action items out.",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.processor = processor
    app.include_router(health.router)
    if settings.processing_mode == "http":
        app.include_router(internal.router)
    return app
