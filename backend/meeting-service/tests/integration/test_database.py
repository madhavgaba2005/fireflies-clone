from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import Database
from app.dependencies import get_session


def pragma(database: Database, name: str) -> object:
    with database.engine.connect() as connection:
        return connection.execute(text(f"PRAGMA {name}")).scalar()


def test_sqlite_pragmas_are_applied_on_every_connection(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'p.db'}")
    assert pragma(database, "foreign_keys") == 1
    assert pragma(database, "journal_mode") == "wal"
    assert pragma(database, "busy_timeout") == 5000
    database.dispose()


def test_parent_directory_is_created(tmp_path: Path) -> None:
    db_file = tmp_path / "nested" / "dir" / "meetings.db"
    database = Database(f"sqlite:///{db_file}")
    assert database.ping()
    assert db_file.exists()
    database.dispose()


def test_in_memory_url_is_supported() -> None:
    database = Database("sqlite:///:memory:")
    assert database.ping()
    database.dispose()


def test_ping_returns_false_when_database_is_unreachable(tmp_path: Path) -> None:
    # A directory cannot be opened as a database file.
    database = Database(f"sqlite:///{tmp_path}")
    assert database.ping() is False
    database.dispose()


def test_session_dependency_yields_working_session_and_closes_it(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 's.db'}")
    sessions = get_session(database)
    session = next(sessions)
    assert isinstance(session, Session)
    assert session.execute(text("SELECT 42")).scalar() == 42
    sessions.close()  # runs the generator's cleanup (session.close())
    database.dispose()
