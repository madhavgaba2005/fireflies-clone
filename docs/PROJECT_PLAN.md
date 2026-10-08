# Project Plan — Issues, Branches, PRs, Phases

## 1. Git workflow

```
issue #N ──▶ branch <type>/<N>-<slug> ──▶ small conventional commits ──▶ PR "Closes #N" ──▶ CI green ──▶ squash-free merge (merge commit) ──▶ main
```

* `main` is always deployable; no direct commits after the initial scaffold.
* Branch prefixes: `feature/`, `fix/`, `docs/`, `test/`, `ci/`, `chore/`.
* Merge strategy: **merge commits** (keeps the individual conventional commits visible in history — the history is part of the evaluation).
* PR template: summary · linked issue · screenshots (UI) · test evidence · requirement IDs touched · docs updated ✔.
* Commit style: Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `ci:`, `chore:`, `refactor:`), imperative, ≤ 72-char subject.

## 2. Issues → branches

| # | Issue | Branch | Req IDs |
|---|-------|--------|---------|
| 1 | Analyze assignment requirements | `docs/1-requirements-analysis` | all |
| 2 | Project scaffolding (monorepo, tooling, compose) | `chore/2-project-scaffolding` | C1–C3 |
| 3 | Database schema + migrations | `feature/3-database-schema` | C3, C7, R4.9 |
| 4 | Meeting API (CRUD, search, filters) | `feature/4-meeting-api` | R1.*, R4.1–R4.5 |
| 5 | Transcript parsing + transcript API | `feature/5-transcript-api` | R2.1, R4.1, R4.2, C4 |
| 6 | Kafka event infrastructure (envelope, outbox, consumer) | `feature/6-kafka-events` | X2 |
| 7 | AI processing service | `feature/7-ai-processing` | R3.*, X1 |
| 8 | Realistic seed data | `feature/8-seed-data` | C6 |
| 9 | Frontend shell + meetings dashboard | `feature/9-meetings-dashboard` | R1.*, R5.1, R5.5 |
| 10 | Meeting detail page (two-panel workspace) | `feature/10-meeting-detail` | R2.1, R5.2 |
| 11 | Audio ↔ transcript synchronization | `feature/11-transcript-sync` | R2.2–R2.4 |
| 12 | Transcript search highlighting | `feature/12-transcript-search` | R2.5 |
| 13 | Meeting CRUD UI (create/edit/delete modals) | `feature/13-meeting-crud-ui` | R4.1–R4.5, R5.3, R5.4 |
| 14 | Action item CRUD | `feature/14-action-items` | R4.6–R4.8 |
| 15 | Fireflies UI polish + states | `feature/15-ui-polish` | R5.*, X7 |
| 16 | Bonus features | `feature/16-*` (one branch per bonus) | B* |
| 17 | Test coverage (E2E suite, gaps) | `test/17-coverage` | X3, X4 |
| 18 | GitHub Actions CI | `ci/18-github-actions` | X5 |
| 19 | Deployment | `chore/19-deployment` | D8 |
| 20 | Documentation completion + interview guide | `docs/20-documentation` | D2–D7, C9 |
| 21 | Final rubric audit + fixes | `docs/21-final-audit` | all |

CI (#18) is pulled forward to right after #3 so every later PR is gated by it.

## 3. Development plan (priority order)

| Phase | Work | Exit criterion |
|-------|------|----------------|
| 0 | Requirements, matrices, architecture, schema, API, events, plan, doc skeleton | **Your approval** |
| 1–2 | Repo scaffold: tooling (ruff, pytest, eslint, prettier), `.env.example`, compose with Kafka | `docker compose up` starts empty services; lint passes |
| 3–4 | Meeting Service foundation, models, Alembic, seed (7 meetings) | Fresh DB → migrate → seed; schema tests pass |
| 15 (early) | CI workflow (lint + tests) | PRs gated |
| 5 | Meeting/transcript/summary/action-item APIs + parsers | Integration tests green, coverage ≥ 90% |
| 6 | Event bus, outbox relay, result consumer | In-memory pipeline test green |
| 7 | AI service: Mock provider, consumer, retries | Kafka E2E: upload → summary persisted |
| 8–9 | Frontend shell, sidebar, dashboard w/ search/filters/sort | E2E: list/search/filter |
| 10–11 | Detail page, player, transcript sync | E2E: click-to-seek, active line follows |
| 12–13 | CRUD modals, action items, transcript search, toasts, states | E2E: every CRUD + persistence after reload |
| 14 | Test gaps, coverage report, TEST_COVERAGE_MATRIX all green | All MUST rows ✅ |
| 16 | UI polish pass vs. UI spec, responsive, a11y | Manual checklist |
| 17 | Bonuses: global search → export → dark mode → tags | Each with test |
| 18 | Deployment + smoke test | Public URL works end-to-end |
| 19 | Final audit (FINAL_EVALUATION_REPORT.md), fix HIGH/CRITICAL, interview guide | Submission |

Rough budget (≈ 24 h of work as the PDF estimates, plus extra for the Kafka/CI goals):
backend ~7 h · events/AI ~4 h · frontend ~10 h · tests/CI ~4 h · deploy ~2 h · docs/audit ~3 h.
