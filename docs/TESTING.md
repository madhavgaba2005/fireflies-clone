# Testing Strategy

> Status: **Planned (Phase 1)**. Commands and real numbers are added as suites land.

## Test pyramid

| Layer | Tool | Scope | Runs against |
|-------|------|-------|--------------|
| Unit (many) | pytest | Transcript parsers, MockSummaryProvider heuristics, envelope validation, service rules, `findActiveSegmentIndex`, `splitByQuery` | Pure functions / in-memory SQLite |
| Integration (some) | pytest + FastAPI `TestClient` | Every endpoint incl. validation & error codes; schema constraints (cascade, unique, check); outbox → `InMemoryEventPublisher` → AI processor → consumer pipeline | Temp SQLite file, `PROCESSING_MODE=inline-test` |
| Contract | pytest | Event envelope/payload shape pinned identically in both services | — |
| Kafka integration (one) | pytest, marker `kafka` | Real broker: create meeting → summary persisted | Kafka service container in CI / compose locally |
| E2E (critical flows) | Playwright | Dashboard filters, transcript sync, transcript search, all CRUD + reload persistence, error toasts | Real backend (memory bus) + seeded DB + Next.js build |

## Coverage philosophy
Backend: target ≥ 90 % line+branch, enforced with `--cov-fail-under`; excluded only: `if __name__ == "__main__"`,
Kafka client wiring covered by the `kafka` marker test. Frontend: no line-coverage target — every MUST-have
workflow has an E2E spec instead (see [TEST_COVERAGE_MATRIX.md](TEST_COVERAGE_MATRIX.md)). The real goal is
**100 % requirement coverage**, not a vanity line number.

## Commands _(pending Phase 3+)_
```
cd backend/meeting-service && pytest --cov=app --cov-report=term-missing
cd backend/ai-service      && pytest --cov=app
cd frontend && npx playwright test
```

## CI behaviour
See [CI_CD.md](CI_CD.md): any failing lint, test, coverage threshold, type-check, build or E2E job fails the PR.
