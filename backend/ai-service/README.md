# AI Processing Service

Stateless worker: `meeting.created` / `transcript.updated` / `summary.requested` in →
`SummaryProvider.generate()` → `summary.generated` / `summary.failed` out. No database.
Design: [docs/EVENT_DRIVEN_ARCHITECTURE.md](../../docs/EVENT_DRIVEN_ARCHITECTURE.md).

```
app/
  main.py       create_app() factory; lifespan will start the Kafka consumer (Phase 6)
  config.py     Settings (environment variables / .env)
  routers/      /health; POST /internal/process in http mode (Phase 6)
  events/       envelope (identical copy of the Meeting Service's; pinned by tests/contract)
  consumers/    Kafka consumer + retry policy (Phase 6)
  processors/   MeetingProcessor, shared by Kafka and HTTP paths (Phase 6)
  providers/    SummaryProvider, MockSummaryProvider, optional LLM provider (Phase 6)
```

## Run locally
```bash
python -m venv .venv && source .venv/Scripts/activate    # macOS/Linux: .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:create_app --factory --reload --port 8001
```

## Checks
```bash
ruff check . && ruff format --check . && mypy app && pytest --cov
```
