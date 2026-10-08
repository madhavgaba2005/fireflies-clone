"""Run Alembic migrations programmatically (on startup and from the seed script)."""

from pathlib import Path

from alembic import command
from alembic.config import Config

SERVICE_ROOT = Path(__file__).resolve().parents[1]


def alembic_config(database_url: str) -> Config:
    config = Config(str(SERVICE_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(SERVICE_ROOT / "alembic"))
    config.attributes["database_url"] = database_url
    config.attributes["configure_logging"] = False  # keep the application's logging setup
    return config


def upgrade_to_head(database_url: str) -> None:
    command.upgrade(alembic_config(database_url), "head")
