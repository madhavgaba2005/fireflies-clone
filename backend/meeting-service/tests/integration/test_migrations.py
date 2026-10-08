"""Alembic migrations build exactly the schema the models describe, and can be rolled back."""

from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect

from app.database import Database
from app.migrations import alembic_config, upgrade_to_head
from app.models import Base


def test_upgrade_head_matches_models(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'migrated.db'}"
    upgrade_to_head(url)
    database = Database(url)
    with database.engine.connect() as connection:
        diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    database.dispose()
    assert diff == [], f"models and migrations differ — generate a new migration: {diff}"


def test_downgrade_to_base_and_upgrade_again(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'roundtrip.db'}"
    config = alembic_config(url)
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    database = Database(url)
    assert set(inspect(database.engine).get_table_names()) == {"alembic_version"}
    database.dispose()
    command.upgrade(config, "head")


def test_app_runs_migrations_on_startup(tmp_path: Path) -> None:
    from app.config import Settings
    from app.main import create_app

    url = f"sqlite:///{tmp_path / 'startup.db'}"
    create_app(Settings(_env_file=None, database_url=url, processing_mode="inline-test"))  # type: ignore[call-arg]
    database = Database(url)
    assert "meetings" in inspect(database.engine).get_table_names()
    database.dispose()
