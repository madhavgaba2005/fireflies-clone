# Backend

Two FastAPI services (see [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md)):

| Service | Role |
|---------|------|
| [meeting-service](meeting-service/) | System of record: REST API, SQLite, transcript parsing, outbox relay, AI-result consumer |
| [ai-service](ai-service/) | Stateless: consumes processing requests, generates notes, publishes results |

Scaffolded in Phase 2.
