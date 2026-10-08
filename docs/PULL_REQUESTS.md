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

## #6 feat: Kafka event pipeline and AI processing service — `feature/6-kafka-events`
**What:** payload contract, outbox relay, result consumer, idempotent result application; AI service provider,
processor, Kafka loop and HTTP fallback; compose healthchecks; CI Kafka job runs the full pipeline.
**Why:** asynchronous, decoupled summary generation (ADR-004/005/008) without routing CRUD through Kafka.
**Testing:** 171 + 39 tests; `pytest -m kafka` against the real broker and AI container; compose stack smoke test incl.
restart persistence.
**Known limitations:** no DLQ; polling relay; single relay instance (see EVENT_DRIVEN_ARCHITECTURE §11).
Closes #6, closes #7

## #9 feat: app shell, meetings dashboard and meeting CRUD dialogs — `feature/9-meetings-dashboard`
**What:** typed API client, URL-synced filters, Fireflies-style shell, library with search/filters/sort/tags, create /
edit / delete dialogs, settings placeholders, Playwright harness running the real stack.
**Testing:** 26 Vitest tests; library E2E specs. **Screenshots:** README.
Closes #9; part of #13

## #10 feat: meeting workspace with synchronized transcript — `feature/10-meeting-workspace`
**What:** playback clock + active-segment search, transcript search, workspace (notes, transcript, player), action
item management, E2E for sync, search, CRUD, action items and error states, responsive fix.
**Why:** the interactive transcript and summary views are called out explicitly in the Functionality criterion.
**Testing:** 65 Vitest tests; 33 Playwright tests (all MUST workflows) against the real stack.
**Known limitations:** playback is simulated (no audio file); date filters use UTC days.
Closes #10, #11, #12, #13, #14

## #16 feat: global search (bonus B3) — `feature/16-global-search`
**What:** `GET /api/search` over titles and transcript lines (escaped LIKE, grouped per meeting, snippets); top-bar
combobox with highlighted snippets that deep-links to `/meetings/{id}?t=ms&find=q`.
**Why:** highest-priority bonus; Fireflies' global search is a core navigation feature.
**Testing:** `test_search_api.py` (12); E2E `global-search.spec.ts` (2).
**Known limitations:** LIKE instead of FTS5 (fine at this data size; see BONUS_FEATURES).
Closes #16

## #17 feat: export transcripts and notes (bonus B2) — `feature/17-export`
**What:** Download dialog (⋯ menu) exporting the transcript or AI notes as TXT or Markdown, with timestamp and
speaker toggles; pure formatters in `lib/export.ts`.
**Why:** Fireflies' Download flow; generated client-side from cached data, so no new endpoint is needed.
**Testing:** 6 Vitest tests; E2E `export.spec.ts` verifies real downloaded file names and contents.
**Known limitations:** no PDF/DOCX formats.
Closes #17

## #18 feat: dark mode (bonus B6) — `feature/18-dark-mode`
**What:** dark values for every design token, account-menu toggle, localStorage persistence with a system-preference
default, and a pre-paint script so there is no light flash; themed toasts.
**Why:** visible polish at low cost, because all colours were already CSS variables.
**Testing:** 3 Vitest tests; E2E `dark-mode.spec.ts` (toggle, reload persistence, system preference).
**Screenshots:** `docs/screenshots/dark-library.png`, `dark-workspace.png`.
Closes #18

## #19 chore: production deployment stack and full verification — `feature/19-deployment-prep`
**What:** `deploy/` (prod compose with Caddy + Kafka, Caddyfile, env example), frontend Dockerfile (standalone),
DEPLOYMENT guide; fix for a stale-identity-map reseed bug; full test, coverage and CI-in-Linux run recorded.
**Why:** submission needs a hosted link; this makes any free VM a one-command deploy without choosing the provider.
**Testing:** prod stack run locally through Caddy: health, create → Kafka summary in ~2 s, restart persistence,
headless-browser check with no console errors. Backend CI job re-run in `python:3.11-slim`.
**Known limitations:** no host chosen yet; GitHub Actions not run until the repo is published.
Closes #19

## #20 docs: final evaluation report and interview preparation — `feature/20-final-audit`
**What:** `FINAL_EVALUATION_REPORT.md` (strict, PDF line by line); all matrix and scorecard statuses closed out;
completed INTERVIEW_GUIDE (29 answers) and FINAL_DEMO_SCRIPT.
**Why:** "Code Understanding" is an evaluation criterion, and the report keeps every claim tied to evidence.
**Testing:** every UI label, file name and code claim in the documents was checked against the source.
Closes #20

