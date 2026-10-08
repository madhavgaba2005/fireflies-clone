# Testing Strategy

> Status: **All suites in place and green.** Numbers below are copied from real runs only.

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

## Latest results (local run, Milestone F)
| Suite | Result | Coverage (line + branch) |
|-------|--------|--------------------------|
| meeting-service unit + integration | 171 passed | 97 % |
| meeting-service `-m kafka` (real broker + AI container) | 2 passed | — |
| ai-service unit + integration | 39 passed | 99 % |
| frontend Vitest | 65 passed | — |
| frontend Playwright (real stack) | 33 passed (31 desktop + 2 phone-width) | — |

**How E2E works:** `playwright.config.ts` starts the AI service and the Meeting Service in `PROCESSING_MODE=http`
(no broker needed), resets and seeds a dedicated SQLite file, builds and starts the frontend on its own port, then
drives Chromium. Tests run serially against one seeded database and look up seeded meetings by name, so they're
independent of each other's data. Repeated runs (`--repeat-each`) were used to flush out timing bugs; two real UI
races were found and fixed this way (see DEVELOPMENT_GUIDE "Frontend state management").



## CI behaviour
See [CI_CD.md](CI_CD.md): any failing lint, test, coverage threshold, type-check, build or E2E job fails the PR.
