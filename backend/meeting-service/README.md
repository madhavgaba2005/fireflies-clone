# Meeting Service

System of record for meetings, participants, transcripts, summaries and action items.
Layers: `routers → services → repositories → SQLAlchemy → SQLite`, plus `events/` (envelope, publishers,
outbox relay, result consumer). Design: [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md).

```
app/
  main.py          create_app() factory: settings, database, CORS, error handlers, routers
  config.py        Settings (environment variables / .env)
  database.py      Base, Database (engine, sessions, SQLite pragmas), ping
  dependencies.py  FastAPI dependencies (settings, database, session)
  errors.py        Domain exceptions → one error envelope
  models/          ORM models (Phase 3)
  schemas/         Pydantic contracts
  routers/         HTTP only
  services/        Business rules + transactions (Phase 4)
  repositories/    All SQL (Phase 3+)
  events/          envelope · EventPublisher · Kafka / HTTP / in-memory publishers · factory
tests/
  unit/ integration/   run by default
  kafka/               real broker, `pytest -m kafka`
  contract/            envelope_v1.schema.json (must equal the AI service's copy)
```

## Run locally
```bash
python -m venv .venv
.venv/Scripts/activate            # Windows (Git Bash: source .venv/Scripts/activate); macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:create_app --factory --reload --port 8000     # http://localhost:8000/docs
```

## Checks
```bash
ruff check . && ruff format --check . && mypy app
pytest --cov                        # unit + integration
pytest -m kafka                     # needs: docker compose up -d kafka
```
