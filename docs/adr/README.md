# Architecture Decision Records

Lightweight ADRs: **Context · Decision · Alternatives · Trade-offs · Consequences.** An ADR is never edited to change
its decision; a new ADR supersedes it.

| ADR | Decision | Status |
|-----|----------|--------|
| [001](001-use-nextjs.md) | Next.js App Router + TypeScript, Tailwind, Radix, TanStack Query | Accepted |
| [002](002-use-fastapi.md) | FastAPI for both backend services | Accepted |
| [003](003-use-sqlite.md) | SQLite via SQLAlchemy 2.0 + Alembic | Accepted |
| [004](004-two-service-architecture.md) | Exactly two services: Meeting Service + AI Processing Service | Accepted |
| [005](005-use-kafka-for-async-processing.md) | Kafka for asynchronous AI processing only (never CRUD) | Accepted |
| [006](006-service-repository-layer.md) | Router → Service → Repository layering | Accepted |
| [007](007-mock-summary-provider.md) | Pluggable `SummaryProvider`, deterministic mock by default | Accepted |
| [008](008-transactional-outbox.md) | Transactional outbox for reliable event publishing | Accepted |
