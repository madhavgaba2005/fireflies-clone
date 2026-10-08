"""Alembic environment: migrations run against the configured DATABASE_URL with SQLite pragmas."""

from logging.config import fileConfig

from alembic import context

from app.config import get_settings
from app.database import Database
from app.models import Base

config = context.config
if config.config_file_name is not None and config.attributes.get("configure_logging", True):
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_online() -> None:
    url = config.attributes.get("database_url") or get_settings().database_url
    database = Database(url)
    with database.engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # SQLite can't ALTER most things; batch mode rebuilds tables
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    database.dispose()


run_migrations_online()
