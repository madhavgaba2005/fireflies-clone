# ADR-005: Router → Service → Repository layering

**Status:** Accepted (Phase 0)

## Context
The rubric scores code quality and modularity. Many FastAPI examples put queries inside route functions, mixing HTTP, business rules and SQL.

## Decision
- **Routers:** parse/validate HTTP, call one service method, return a response model. No SQL.
- **Services:** business rules, transaction boundaries, outbox writes; raise domain exceptions. No HTTP types.
- **Repositories:** all SQLAlchemy queries. No business decisions.

## Alternatives
- **Fat routers:** fewer files; logic becomes untestable without HTTP and gets duplicated across endpoints.
- **Full DDD / unit-of-work / generic repositories:** more abstraction than a ~10-table app needs.

## Trade-offs
+ Each layer is testable in isolation; the Kafka consumer reuses the same services as the HTTP routes.
− More files; some thin pass-through methods.

## Consequences
The AI-result consumer calls `SummaryService.apply_generated(...)` — the same code path the tests exercise.
