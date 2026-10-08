# AI Processing Service

Stateless worker: `meeting.created` / `transcript.updated` / `summary.requested` in →
`SummaryProvider.generate()` → `summary.generated` / `summary.failed` out. No database.
Design: [docs/EVENT_DRIVEN_ARCHITECTURE.md](../../docs/EVENT_DRIVEN_ARCHITECTURE.md). Scaffolded in Phase 2.
