# ADR-003: SQLite via SQLAlchemy 2.0 + Alembic

**Status:** Accepted (Phase 0)

## Context
SQLite is mandated by the PDF. The schema is explicitly evaluated, and data must persist across restarts and deployments.

## Decision
SQLite file owned solely by the Meeting Service; SQLAlchemy 2.0 typed ORM; Alembic migrations; per-connection `PRAGMA foreign_keys=ON`, `journal_mode=WAL`, `busy_timeout=5000`.

## Alternatives
- **Raw `sqlite3`:** fewer dependencies, but hand-written mapping and easy to slip into string-built SQL.
- **SQLModel:** less boilerplate, but blurs ORM model and API schema — we want those separate.
- **`create_all()` without migrations:** fine for a demo, but no upgrade path and a weaker DB-design story.

## Trade-offs
+ Zero-ops, single file, trivial to seed and reset; portable models make PostgreSQL a config change.
− Single writer ⇒ the Meeting Service cannot scale horizontally; needs a persistent volume when deployed.

## Implementation notes (Phase 2)
`app/database.py` owns a `Database` object (engine + session factory) created by the app factory and stored on
`app.state` — no module-level globals, so every test gets an isolated SQLite file. Pragmas are set in a SQLAlchemy
`connect` listener and verified by tests. Alembic is introduced in Phase 3 together with the first migration
(no empty migration scaffolding).

## Consequences
Only the Meeting Service touches the DB; the AI Service is stateless (ADR-004).
