# Testing Strategy

> Status: **Structure in place (Phase 2)**. Numbers below are copied from real runs only.

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

## Layout
| Location | Runner | What lives there |
|----------|--------|------------------|
| `backend/<service>/tests/unit/` | pytest | Pure logic: config, envelope, publishers (fake producer / mock HTTP transport) |
| `backend/<service>/tests/integration/` | pytest + `TestClient` | App factory, health, error envelope, CORS, database layer (temp SQLite file per test) |
| `backend/meeting-service/tests/kafka/` | pytest `-m kafka` | Real broker round trip — **deselected by default**, run with compose Kafka and in the CI `kafka` job |
| `backend/<service>/tests/contract/` | — | `envelope_v1.schema.json`; each service asserts its model equals it, CI asserts both files are identical |
| `frontend/lib/*.test.ts` | Vitest | Pure functions (API client now; sync/search later) |
| `frontend/tests/e2e/` | Playwright | Critical user workflows against `next start` |

## Commands
```bash
cd backend/meeting-service && pytest --cov            # unit + integration
cd backend/meeting-service && pytest -m kafka         # needs: docker compose up -d kafka
cd backend/ai-service      && pytest --cov
cd frontend && npm test                               # Vitest
cd frontend && npm run build && npm run test:e2e      # Playwright (needs `npx playwright install chromium` once)
```

## Results at the end of Phase 2 (local run, 2026-10-09)
| Suite | Result | Coverage |
|-------|--------|----------|
| meeting-service unit + integration | 36 passed, 1 deselected (kafka) | 98 % (line + branch) |
| meeting-service kafka (`-m kafka`) | 1 passed against compose `apache/kafka:3.9.1` | — |
| ai-service unit + integration | 11 passed | 99 % |
| frontend Vitest | 6 passed | — |
| frontend Playwright smoke | 2 passed | — |

Coverage at this stage measures scaffolding only and says nothing about features yet.

## CI behaviour
See [CI_CD.md](CI_CD.md): any failing lint, test, coverage threshold, type-check, build or E2E job fails the PR.
