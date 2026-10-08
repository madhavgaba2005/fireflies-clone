from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import Settings
from app.main import create_app
from app.models import Base


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Isolated settings: a fresh SQLite file per test and no broker."""
    return Settings(
        environment="test",
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        processing_mode="inline-test",
        run_migrations_on_startup=False,  # tests build the schema from the models (faster);
        # tests/integration/test_migrations.py proves the migration produces the same schema
        _env_file=None,  # type: ignore[call-arg]  # ignore any developer .env
    )


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    application = create_app(settings)
    Base.metadata.create_all(application.state.db.engine)
    return application


@pytest.fixture
def session(app: FastAPI) -> Iterator[Session]:
    with app.state.db.session_factory() as db_session:
        yield db_session


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
