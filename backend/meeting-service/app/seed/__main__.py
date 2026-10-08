"""python -m app.seed [--reset]  — migrate the configured database and load the demo meetings."""

import argparse
from datetime import UTC, datetime

from app.config import get_settings
from app.database import Database
from app.migrations import upgrade_to_head
from app.seed.loader import seed_database


def main() -> None:
    parser = argparse.ArgumentParser(description="Load demo meetings into the database.")
    parser.add_argument("--reset", action="store_true", help="delete all data first")
    args = parser.parse_args()

    settings = get_settings()
    upgrade_to_head(settings.database_url)
    database = Database(settings.database_url)
    with database.session_factory() as session:
        created = seed_database(session, datetime.now(UTC), reset=args.reset)
    database.dispose()
    print(f"Seeded {created} meetings." if created else "Database already has meetings; skipped.")


if __name__ == "__main__":
    main()
