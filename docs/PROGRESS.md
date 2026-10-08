# Progress Log

One entry per milestone: what was built, how it was verified, what's left. Newest last.

| Milestone | Branch | Status |
|-----------|--------|--------|
| Phase 0–1 Requirements & architecture | `docs/1-requirements-analysis` | ✅ merged |
| Phase 2 Scaffolding | `chore/2-project-scaffolding` | ✅ merged |
| A Database + seed | `feature/3-database-schema` | ✅ merged |
| B Meeting API | `feature/4-meeting-api` | ✅ merged |
| C Kafka + AI service | `feature/6-kafka-events` | ✅ merged |
| D Frontend shell + dashboard + CRUD dialogs | `feature/9-meetings-dashboard` | ✅ merged |
| E–F Workspace, transcript sync, search, action items | `feature/10-meeting-workspace` | ✅ merged |

---

## A — Database schema + seed data (#3, #8)

**Built**
- SQLAlchemy models for all domain tables plus `outbox_events` / `processed_events`
  (`backend/meeting-service/app/models/`), with CHECK / UNIQUE / FK constraints and explicit `ON DELETE` rules.
- `UTCDateTime` column type: stores UTC, returns aware datetimes, rejects naive ones.
- Alembic initial migration, applied automatically on startup (`RUN_MIGRATIONS_ON_STARTUP`).
- Transcript parser for txt / WebVTT / JSON with line-numbered errors.
- Seed: 7 meetings, 11 recurring people, 183 segments, 34 chapters, 35 action items (`python -m app.seed [--reset]`).

**Verified**
- 82 backend tests pass (schema constraints incl. cascades, RESTRICT, SET NULL, NOCASE uniqueness, CHECKs;
  migration ≡ models; downgrade/upgrade; parser edge cases; seed completeness/idempotency).
- Real run: fresh file → migrate → seed → `PRAGMA integrity_check = ok`, `foreign_key_check` empty; second run skips; `--reset` reseeds.

**Known gaps:** none for this milestone.

## B — Meeting API (#4, #5, #14 backend)

**Built**
- Repositories (`meetings`, `action_items`, `participants`, `outbox`): escaped `LIKE` title search, any-of participant
  filter, inclusive UTC date range, keyword tag filter, both sort orders, pagination; page loads in 3 queries + 1
  grouped count query.
- Services: create from form / pasted / uploaded transcript in one transaction with the `meeting.created` outbox row;
  update with replace semantics and the 409 "speaker can't be removed" rule; delete; regenerate (`summary.requested`);
  talk-time stats; action items with assignee validation and "user edit ⇒ manual" rule.
- 14 REST endpoints with documented error responses; sample transcripts for each format.

**Verified** — 144 backend tests pass (every endpoint, filter combination, validation rule and error code; outbox side
effects; persistence via a fresh session). ruff + strict mypy clean.

**Decision:** uploads are sent as JSON text with `transcript_format` instead of multipart (documented in API.md).

## C — Kafka pipeline + AI Processing Service (#6, #7)

**Built**
- Typed payload contract (pinned in both services), outbox relay, Kafka result consumer, idempotent `SummaryService`.
- AI service: deterministic `MockSummaryProvider`, `MeetingProcessor` with retries, Kafka consume→process→produce
  loop, token-protected HTTP fallback endpoint.
- Lifespan wiring per `PROCESSING_MODE`; compose healthchecks; `SEED_ON_STARTUP` in compose.

**Verified**
- 171 meeting-service tests (97 % coverage) and 39 AI-service tests (99 %).
- **Real Kafka:** `pytest -m kafka` with the broker and the AI service container — API → outbox → Kafka → AI → Kafka →
  consumer → SQLite, `completed` in ~5 s.
- **Full compose stack:** auto-seeded 7 meetings; meeting created via `curl` completed in ~1 s with correctly assigned
  action items; data survived `docker compose restart meeting-service`.

**Bugs found by tests and fixed:** summary silently not saved (SQLAlchemy 2.x backref cascade) — SQLAlchemy warnings
are now test errors; keyword de-duplication kept the last spelling instead of the first.

**Decision:** no LLM provider ships (no key, no tests ⇒ it would be decorative); the extension point is documented in ADR-007.

## D–F — Frontend: dashboard, workspace, transcript sync, CRUD, search (#9–#14)

**Built**
- App shell (sidebar, top bar, avatar menu, coming-soon dialogs, settings tabs), UI kit, TanStack Query hooks.
- Library: day groups, debounced search, date presets/custom range, participant filter, sort, tags — URL-synced.
- Create (upload/paste/form), edit and delete dialogs with toasts and inline server errors.
- Workspace: notes panel (keywords, overview, outline, action items by assignee, talk time), transcript with search,
  player with speaker timeline; simulated `PlaybackClock`; binary-search active segment; auto-follow with manual-scroll
  grace; keyboard shortcuts; polling + "notes ready" toast; responsive tabs and drawer.

**Verified**
- 65 Vitest tests; 33 Playwright tests against the real stack (both services + production build), all passing,
  including repeated runs of the timing-sensitive specs.
- Visual review of every screen via screenshots (README) — no console errors.

**Bugs found and fixed:** seek while paused didn't scroll the active line into view; optimistic checkbox flickered
(update ran after an await); success toasts skipped when a row unmounted (`mutate` callbacks); top bar overflowed at
phone width (utility-class conflict).

## G — Bonuses (#16–#18)

**Built:**
- Global search across titles and transcripts, with deep links to the exact moment.
- Export of the transcript or notes as TXT or Markdown.
- Dark mode: system default, persisted choice, no flash on load.
- Tags (from the AI keywords) were already built in D–F.

**Deferred, with reasons in BONUS_FEATURES:** comments on segments, and an "Ask" chat (it needs a real LLM to be
honest).

**Verified:** 6 export and 3 theme unit tests. The E2E tests check real downloaded file names and contents, and the
theme toggle, reload persistence and system preference. Dark screenshots were reviewed.

## H — Full test run and coverage

**Results:** every suite passes (see TESTING "Latest results"): 183 + 2 Kafka + 39 backend tests, 74 Vitest tests and
39 Playwright tests. Coverage is 97 % for the meeting service and 99 % for the AI service.

**Bug found and fixed:** `seed --reset` in the same session could fail intermittently. Bulk DELETEs leave stale
objects in SQLAlchemy's identity map, and SQLite reuses row IDs, so a new row could collide with a stale one. The fix
is `session.expunge_all()` after the wipe. The test now passes on repeated runs, and SAWarnings stay fatal in tests.

**Clean-ups:**
- Removed the deprecated `Result.tuples()` calls (SQLAlchemy 2.1).
- Set Alembic's `path_separator`.

## I — CI validation

- `act` is not installed, so the backend CI job was reproduced in a clean `python:3.11-slim` container with its exact
  commands. Both services pass, coverage gate included.
- The frontend job's commands (`lint`, `format:check`, `typecheck`, `test`, `build`, `test:e2e` with
  `E2E_PYTHON=python`) all pass locally.
- The Kafka job's `docker compose up --wait kafka ai-service` followed by `pytest -m kafka` passes locally.
- **Not yet verified:** a run on GitHub itself, which needs the repository to be published (the owner's decision).

## J — Deployment preparation (#19)

**Built:**
- `deploy/docker-compose.prod.yml`: Caddy with automatic HTTPS, Next.js standalone image, both services and real
  Kafka with a 256 MB heap. Only Caddy publishes ports.
- `deploy/Caddyfile`: a single origin, so there is no CORS.
- Frontend `Dockerfile` and `deploy/.env.example`.
- `docs/DEPLOYMENT.md` rewritten with options, steps, backup and the checklist.

**Verified locally:** the prod stack ran on `:8088`.
- All containers became healthy, and the frontend served the seeded library.
- `/health/ready` returned OK.
- A meeting created through Caddy was summarised through Kafka in about 2 s.
- After restarting the whole stack, the new meeting was still there with status `completed`.
- In a headless browser, the workspace rendered, click-to-seek worked, and there were no console errors.

The browser does log `net::ERR_ABORTED` for some link prefetches. These are Next.js cancelling its own prefetches;
the pages themselves load normally.

**Pending the owner's decision:** the hosting provider. Free VM recommended, no purchase made. Publishing the
repository is also pending.

