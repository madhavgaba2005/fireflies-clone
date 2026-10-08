"""Database connection layer: declarative base, engine, session factory and SQLite pragmas."""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event, make_url, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Parent class of every ORM model (models are added in Phase 3)."""


def _set_sqlite_pragmas(dbapi_connection: Any, _record: Any) -> None:
    # SQLite ignores foreign keys unless this is set on *every* connection.
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA journal_mode = WAL")  # readers don't block the writer
    cursor.execute("PRAGMA busy_timeout = 5000")  # wait up to 5 s instead of "database is locked"
    cursor.close()


def _ensure_sqlite_directory(url: str) -> None:
    database = make_url(url).database
    if database and database != ":memory:":
        Path(database).parent.mkdir(parents=True, exist_ok=True)


class Database:
    """Owns the engine and session factory for one database URL."""

    def __init__(self, url: str) -> None:
        connect_args: dict[str, Any] = {}
        if url.startswith("sqlite"):
            # Sync endpoints run in a thread pool; a session is never shared across threads.
            connect_args["check_same_thread"] = False
            _ensure_sqlite_directory(url)

        self.engine: Engine = create_engine(url, connect_args=connect_args)
        if self.engine.dialect.name == "sqlite":
            event.listen(self.engine, "connect", _set_sqlite_pragmas)

        self.session_factory = sessionmaker(
            bind=self.engine, autoflush=False, expire_on_commit=False
        )

    def session(self) -> Iterator[Session]:
        """Yield a session and always close it (used as a FastAPI dependency)."""
        with self.session_factory() as session:
            yield session

    def ping(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError:
            return False
        return True

    def dispose(self) -> None:
        self.engine.dispose()
