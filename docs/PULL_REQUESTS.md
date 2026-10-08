# Pull Request Archive

GitHub was not available during development (no CLI, repository not yet published), so every milestone was developed
on its own branch and merged into `main` locally with `--no-ff` — the merge commits show each branch exactly as a PR
merge would. The descriptions below are the PR bodies, ready to paste if the branches are re-opened as PRs.

---

## #1 docs: requirements analysis and architecture — `docs/1-requirements-analysis`
**What:** requirements and evaluation matrices, architecture, database, API and event design, UI spec, ADRs, Git plan.
**Why:** design before code; every PDF requirement traceable to implementation and tests.
**Testing:** markdown link/anchor check (all links resolve).
Closes #1

## #2 chore: scaffold services, frontend, tooling and CI — `chore/2-project-scaffolding`
**What:** FastAPI app factories (both services), config, SQLite connection layer, error envelope, health checks,
`EventPublisher` with Kafka / HTTP / in-memory transports, Next.js 16 scaffold, Vitest + Playwright, Docker Compose
with Kafka, GitHub Actions workflow, `.gitattributes`.
**Testing:** 36 + 11 backend tests, 6 Vitest, 2 Playwright; real Kafka round trip; both services and the frontend started.
Closes #2

## #3 feat: database schema and seed data — `feature/3-database-schema`
**What:** normalized models + Alembic migration, UTC datetime type, transcript parser (txt/vtt/json), 7-meeting seed.
**Why:** database design is explicitly evaluated; the app must be populated on first start.
**Files:** `app/models/`, `alembic/`, `app/services/transcript_parser.py`, `app/seed/`.
**Testing:** 82 backend tests (constraints, cascades, migration ≡ models, parser edge cases, seed); manual integrity check.
**Known limitations:** none.
Closes #3, closes #8

## #4 feat: meeting API — `feature/4-meeting-api`
**What:** repositories, services and REST endpoints for meetings, transcripts, summaries, action items and participants.
**Why:** PDF core features 1–4 need a clean, sensible API (evaluated under Backend/API Design).
**Files:** `app/repositories/`, `app/services/`, `app/routers/`, `app/schemas/`, `samples/`.
**Testing:** 144 backend tests incl. `test_meetings_api.py`, `test_action_items_api.py`.
**Known limitations:** date filters use UTC day boundaries.
Closes #4, closes #5 (transcript API); backend part of #14
