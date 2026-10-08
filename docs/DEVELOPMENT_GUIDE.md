# Development Guide (study document)

> Living document — the author's primary study material for the evaluation interview.
> Status: **Phase 1** — every *design* decision below is final; implementation details (file names, code
> excerpts, real test names) are added in the phase that builds each component, marked _(Phase N)_.

Each component answers 13 questions in a fixed order:
**1 What · 2 Why chosen · 3 Problem solved · 4 How it works · 5 Alternatives · 6 Why rejected · 7 Advantages ·
8 Disadvantages · 9 Failure modes · 10 Scaling · 11 Place in the architecture · 12 30-second explanation ·
13 Follow-up questions.**

Context documents: [REQUIREMENTS_MATRIX](REQUIREMENTS_MATRIX.md) · [ARCHITECTURE](ARCHITECTURE.md) ·
[DATABASE_DESIGN](DATABASE_DESIGN.md) · [API](API.md) · [EVENT_DRIVEN_ARCHITECTURE](EVENT_DRIVEN_ARCHITECTURE.md) ·
[TRADEOFFS](TRADEOFFS.md) · [ADRs](adr/).

## Contents
Frontend: [Next.js](#nextjs) · [TypeScript](#typescript) · [Transcript synchronization](#transcript-synchronization) ·
[Transcript search](#transcript-search)
Backend: [FastAPI](#fastapi) · [Pydantic](#pydantic) · [SQLAlchemy](#sqlalchemy) · [SQLite](#sqlite) ·
[Router layer](#router-layer) · [Service layer](#service-layer) · [Repository layer](#repository-layer) · [REST API](#rest-api)
Distributed: [Microservices](#microservices) · [Meeting Service](#meeting-service) · [AI Processing Service](#ai-processing-service) ·
[Kafka](#kafka) · [Event-driven processing](#event-driven-processing) · [Summary generation](#summary-generation)
Engineering: [Testing](#testing) · [CI](#ci) · [Git workflow](#git-workflow) · [Deployment](#deployment)

---

## Next.js
1. **What:** React framework with file-system routing (App Router), bundling, and production builds.
2. **Why:** Mandated by the PDF; App Router is the current default.
3. **Problem:** Routing (`/meetings`, `/meetings/[id]`, `/settings`), code-splitting, a production build we can deploy to Vercel for free.
4. **How:** `app/<route>/page.tsx` files become routes; shared `layout.tsx` renders the sidebar/top bar once. Interactive pages are client components that call the API through `lib/api.ts` and cache results with TanStack Query.
5. **Alternatives:** Vite + React Router; Remix; Pages Router.
6. **Rejected:** Not allowed by the PDF (Vite/Remix); Pages Router is legacy for new apps.
7. **Advantages:** Zero-config build, layouts, Vercel deployment, large ecosystem.
8. **Disadvantages:** Server vs client component boundaries add concepts; we mostly use client components, so SSR benefits are small.
9. **Failure modes:** API unreachable → query error state + Retry; hydration mismatch if rendering depends on time/locale (format dates on the client).
10. **Scaling:** Static assets on a CDN; the frontend is stateless.
11. **Place:** Browser-facing tier; talks only to the Meeting Service over REST.
12. **30 s:** "Next.js gives me routing, layouts and a production build. Pages are client components because the workspace is highly interactive; server data goes through one typed API client and TanStack Query, which gives me loading, error and cache invalidation for free."
13. **Follow-ups:** Why not server components? Why TanStack Query and not Redux? How do you avoid duplicate fetches? → [ADR-001](adr/001-use-nextjs.md)

## TypeScript
1. **What:** Typed superset of JavaScript. 2. **Why:** Mandated; catches API-shape mistakes at compile time.
3. **Problem:** Keeping frontend code in sync with API response shapes. 4. **How:** `strict: true`; `lib/types.ts` mirrors the Pydantic response models; `tsc --noEmit` runs in CI.
5. **Alternatives:** Plain JS; generated types from OpenAPI. 6. **Rejected:** JS not allowed; codegen adds a build step — hand-written types are small and readable (codegen is a future improvement).
7. **Adv:** Refactors are safe; editor autocomplete. 8. **Dis:** Types can drift from the backend if not updated (mitigated by E2E tests).
9. **Failure:** Runtime data not matching types — types are compile-time only. 10. **Scaling:** OpenAPI codegen at larger team size.
11. **Place:** All frontend code. 12. **30 s:** "Strict TypeScript with types mirroring the API schemas, checked in CI."
13. **Follow-ups:** How do you keep types in sync? What does `strict` enable?

## FastAPI
1. **What:** Python ASGI web framework built on type hints and Pydantic.
2. **Why:** PDF allows FastAPI or Django; FastAPI gives validation + OpenAPI from type hints and an async lifespan to host the Kafka consumer and outbox relay.
3. **Problem:** Clean REST API with validated inputs and self-documenting endpoints.
4. **How:** Routers declare endpoints with Pydantic request/response models; dependencies inject a DB session and services; exception handlers map domain errors to the error envelope; `lifespan` starts/stops background tasks.
5. **Alternatives:** Django + DRF, Flask. 6. **Rejected:** Django brings unused admin/auth/templates and is awkward with an async Kafka loop; Flask needs extra libraries for validation/OpenAPI.
7. **Adv:** `/docs` for free, little boilerplate, async-friendly. 8. **Dis:** We assemble ORM/migrations ourselves.
9. **Failure:** Unhandled exception → generic 500 envelope (no stack trace to client), logged server-side.
10. **Scaling:** Stateless workers behind a load balancer — limited here by SQLite's single writer.
11. **Place:** Both backend services. 12. **30 s:** "FastAPI turns typed function signatures into validated endpoints and OpenAPI docs, and its lifespan hook hosts my Kafka consumer."
13. **Follow-ups:** Sync vs async endpoints with a sync ORM? How are errors mapped? → [ADR-002](adr/002-use-fastapi.md)

## Pydantic
1. **What:** Data validation via Python type hints. 2. **Why:** Native to FastAPI; also validates event envelopes and settings.
3. **Problem:** Never trust client input; never leak internal fields. 4. **How:** Separate `Create`, `Update` and `Read` schemas per resource; field constraints (`min_length`, `max_length`, `ge`); `pydantic-settings` reads env vars.
5. **Alternatives:** marshmallow, manual checks, SQLModel. 6. **Rejected:** Extra library / error-prone / merges ORM and API models.
7. **Adv:** One declaration = validation + docs + serialization. 8. **Dis:** Some duplication between ORM models and schemas (intentional).
9. **Failure:** Invalid input → 422 with field details. 10. **Scaling:** n/a. 11. **Place:** API boundary, event boundary, config.
12. **30 s:** "Pydantic schemas are my contracts: they validate input, shape output, and document the API."
13. **Follow-ups:** Why separate Create/Update/Read schemas? Why not SQLModel?

## SQLAlchemy
1. **What:** Python ORM + SQL toolkit (2.0 typed style). 2. **Why:** Parameterized queries by construction, explicit relationships, portable to PostgreSQL.
3. **Problem:** Mapping tables to objects safely, without string-built SQL. 4. **How:** `Mapped[...]` models; relationships with explicit cascade; `selectinload` on the list page to avoid N+1; a `connect` listener sets SQLite pragmas; Alembic manages schema migrations.
5. **Alternatives:** Raw `sqlite3`, SQLModel, Django ORM. 6. **Rejected:** Manual mapping + injection risk / blurs layers / not using Django.
7. **Adv:** Safe, expressive, portable. 8. **Dis:** Learning curve; lazy-loading surprises if not explicit.
9. **Failure:** N+1 queries (mitigated by explicit loading); `database is locked` (WAL + busy_timeout). 10. **Scaling:** Same models on PostgreSQL.
11. **Place:** Repository layer only. 12. **30 s:** "Typed SQLAlchemy models, used only from repositories; queries are parameterized, so no SQL injection."
13. **Follow-ups:** What is N+1 and how do you avoid it? Why Alembic instead of `create_all`? → [ADR-003](adr/003-use-sqlite.md)

## SQLite
1. **What:** Embedded, file-based relational database. 2. **Why:** Mandated.
3. **Problem:** Persistent relational storage with zero ops. 4. **How:** One file owned by the Meeting Service; `PRAGMA foreign_keys=ON` (off by default!), `journal_mode=WAL`, `busy_timeout`.
5. **Alternatives:** PostgreSQL, MySQL. 6. **Rejected:** Not allowed by the PDF.
7. **Adv:** No server, trivial reset/seed, fast reads. 8. **Dis:** Single writer; local file → needs a persistent volume; no network access.
9. **Failure:** Lost data on ephemeral hosting disks; lock contention. 10. **Scaling:** Migrate to PostgreSQL (see [TRADEOFFS](TRADEOFFS.md)).
11. **Place:** Meeting Service only. 12. **30 s:** "SQLite as required; I enable foreign keys explicitly because SQLite ignores them by default, and only one service owns the file."
13. **Follow-ups:** What if two services needed the data? How do you migrate to Postgres?

## Router layer
1. **What:** FastAPI route functions (`app/routers/`). 2. **Why:** Keep HTTP concerns in one place.
3. **Problem:** Fat route functions that mix HTTP, rules and SQL. 4. **How:** Parse/validate → call one service method → return a response model; no SQL, no business rules.
5–6. **Alternatives:** Logic in routes — rejected: untestable without HTTP, duplicated across endpoints and the Kafka consumer.
7. **Adv:** Thin, readable endpoints. 8. **Dis:** Extra indirection. 9. **Failure:** Domain exceptions bubble to one handler.
10. **Scaling:** n/a. 11. **Place:** Top of the Meeting Service. 12. **30 s:** "Routers only speak HTTP." 13. **Follow-ups:** Where would auth go? (a dependency on the router)

## Service layer
1. **What:** Business logic (`app/services/`). 2. **Why:** One place for rules and transaction boundaries.
3. **Problem:** Rules such as "speakers must be participants", "regeneration never deletes manual action items", "bump transcript revision" must not be duplicated. 4. **How:** Services receive a session + repositories, enforce rules, write outbox rows in the same transaction, raise domain exceptions (`NotFoundError`, `ConflictError`).
5–6. **Alternatives:** Put rules in repositories or routes — rejected: mixes concerns.
7. **Adv:** Shared by HTTP routes and the event consumer; unit-testable. 8. **Dis:** More files.
9. **Failure:** Exceptions roll back the transaction. 10. **Scaling:** n/a. 11. **Place:** Between routers/consumers and repositories.
12. **30 s:** "Services own the rules and the transaction; both the API and the Kafka consumer call the same service." 13. **Follow-ups:** Why is the outbox write in the service?

## Repository layer
1. **What:** Data access classes (`app/repositories/`). 2. **Why:** All SQL in one place.
3. **Problem:** Queries scattered across the codebase. 4. **How:** Methods like `list_meetings(filters)`, `get_with_participants(id)`; return ORM objects; no business decisions.
5–6. **Alternatives:** Direct ORM in services; generic repository/unit-of-work frameworks — rejected as scattered / over-abstracted.
7. **Adv:** Query tuning is local; filters tested in isolation. 8. **Dis:** Some thin methods.
9. **Failure:** n/a. 10. **Scaling:** Swap implementation per database. 11. **Place:** Bottom of the Meeting Service.
12. **30 s:** "Repositories are the only place that knows SQL." 13. **Follow-ups:** Isn't the ORM already a repository? → [ADR-006](adr/006-service-repository-layer.md)

## REST API
1. **What:** Resource-oriented HTTP API under `/api`. 2. **Why:** Simple, cacheable, matches CRUD semantics.
3. **Problem:** A predictable contract for the frontend. 4. **How:** Nouns + HTTP verbs; nested routes only for ownership (`/meetings/{id}/action-items`); one error envelope; correct status codes; pagination + filters as query params.
5. **Alternatives:** GraphQL, RPC. 6. **Rejected:** GraphQL adds schema/tooling for one client with simple needs.
7. **Adv:** Explainable, OpenAPI-documented. 8. **Dis:** Multiple requests for the detail page (made in parallel).
9. **Failure:** See error table in [API.md](API.md). 10. **Scaling:** HTTP caching, pagination. 11. **Place:** Frontend ↔ Meeting Service.
12. **30 s:** "Resource-based REST, nested only where ownership is real, one error format, OpenAPI docs." 13. **Follow-ups:** Why PATCH not PUT? Why are transcript and summary separate endpoints?

## Microservices
1. **What:** Two independently deployable services. 2. **Why:** To isolate slow, failure-prone AI work from the user-facing system of record.
3. **Problem:** An LLM call inside a request makes the API slow and fragile. 4. **How:** Meeting Service owns data and REST; AI service is stateless; they communicate only via events.
5. **Alternatives:** Monolith; many services. 6. **Rejected:** Monolith is fine but hides the async seam; many services would split one transactional boundary.
7. **Adv:** Independent deploy/scale/replace. 8. **Dis:** More moving parts, versioned contract.
9. **Failure:** AI service down → requests wait, UI shows Processing. 10. **Scaling:** Scale AI workers via consumer-group partitions.
11. **Place:** Whole backend. 12. **30 s:** "Two services split on the one boundary with different runtime behaviour: CRUD vs AI processing." 13. **Follow-ups:** Why not ten services? → [ADR-004](adr/004-two-service-architecture.md)

## Meeting Service
System of record: REST API, validation, transcript parsing (txt/vtt/json), persistence, outbox relay, consumer
of AI results. **30 s:** "Everything the user reads or writes goes through it; it's the only owner of the database."
_(Phases 3–5: file map, key functions.)_

## AI Processing Service
Stateless worker: consume `meeting.created`/`transcript.updated`/`summary.requested` → `SummaryProvider.generate()`
→ publish `summary.generated` or `summary.failed` after retries. Also exposes `POST /internal/process` in HTTP mode.
**30 s:** "Transcript in, notes out, no database — so it can be restarted, swapped or scaled freely." _(Phase 6.)_

## Kafka
1. **What:** Distributed, durable, partitioned log. 2. **Why:** Durable, decoupled hand-off between the two services.
3. **Problem:** Don't lose summary requests when a service is down; don't make the API wait. 4. **How:** Topics `meeting.events` and `ai.events`, keyed by `meeting_id` (per-meeting ordering); consumer groups; manual offset commit after handling.
5. **Alternatives:** BackgroundTasks, Celery+Redis, RabbitMQ, direct HTTP. 6. **Rejected:** In-process/lost on crash; Redis out of scope; HTTP couples availability (kept only as a documented fallback).
7. **Adv:** Durability, replay, ordering, independent consumers. 8. **Dis:** Heavy to operate and host for free.
9. **Failure:** Broker down → outbox keeps events, relay retries. 10. **Scaling:** More partitions + consumers.
11. **Place:** Between the services, async path only. 12. **30 s:** "Kafka carries only the asynchronous summary work; CRUD never touches it."
13. **Follow-ups:** At-least-once vs exactly-once? What if Kafka is down? → [ADR-005](adr/005-use-kafka-for-async-processing.md)

## Event-driven processing
Outbox for reliable publishing ([ADR-008](adr/008-transactional-outbox.md)); `processed_events` for duplicate
detection; `transcript_revision` to discard stale results; processing state machine visible in the UI.
**30 s:** "Events are written in the same transaction as the data, published at-least-once, and applied idempotently."
Details: [EVENT_DRIVEN_ARCHITECTURE.md](EVENT_DRIVEN_ARCHITECTURE.md).

## Summary generation
`SummaryProvider` interface; `MockSummaryProvider` (default, deterministic heuristics); optional LLM provider.
Seeded meetings use hand-written summaries. **30 s:** "A pluggable provider: mock by default so the demo is free and
tests are deterministic; an LLM drops in behind the same interface." → [ADR-007](adr/007-mock-summary-provider.md) _(Phase 6.)_

## Transcript synchronization
1. **What:** Two-way link between player position and transcript. 2. **Why:** PDF must-have R2.3/R2.4 and the core Fireflies interaction.
3. **Problem:** Clicking a line must seek; playback must highlight and reveal the current line.
4. **How:** A `PlaybackClock` interface (`currentMs`, `play`, `pause`, `seek`, `rate`, subscribe). `SimulatedClock` advances time with `requestAnimationFrame`; an `HtmlMediaClock` can wrap `<audio>` later. `findActiveSegmentIndex(segments, ms)` binary-searches sorted `start_ms`, active when `start_ms ≤ t < end_ms`; in a gap, the previous segment stays active. Click line → `seek(start_ms)` + play. Active index change → `scrollIntoView({block: 'center'})`, paused for a few seconds after manual scrolling.
5. **Alternatives:** Linear scan per frame; real audio from TTS. 6. **Rejected:** O(n) per frame is fine but binary search is no harder; TTS costs time for no grading value.
7. **Adv:** Same logic works with real media. 8. **Dis:** No sound in the demo.
9. **Failure/edge cases:** t exactly on a boundary, t before the first segment, gaps, t ≥ duration, empty transcript — each unit-tested.
10. **Scaling:** O(log n) per tick. 11. **Place:** Frontend workspace. 12. **30 s:** "One clock is the source of truth; a binary search maps time to the active line; clicking a line just seeks the clock." _(Phase 10.)_
13. **Follow-ups:** What happens at exact boundaries? Why not re-render every line each frame? (memoized lines, only active index changes trigger re-render)

## Transcript search
Client-side, case-insensitive. Query is regex-escaped; text is split into match/non-match fragments rendered as
`<mark>` — never `dangerouslySetInnerHTML`, so uploaded text cannot inject HTML. "n of m" counter, Enter/Shift+Enter
navigation. **30 s:** "Search runs in the browser over already-loaded segments and highlights safely with React
elements." _(Phase 13.)_

## Testing
pytest + pytest-cov (unit, integration with in-memory publisher, one real Kafka test), Playwright for critical
flows. Goal: 100 % **requirement** coverage, ~90 % backend line coverage reported from real runs only.
→ [TESTING.md](TESTING.md), [TEST_COVERAGE_MATRIX.md](TEST_COVERAGE_MATRIX.md)

## CI
GitHub Actions on PRs and pushes to `main`: lint, types, tests + coverage gate, frontend build, E2E.
→ [CI_CD.md](CI_CD.md)

## Git workflow
Issue → branch → small conventional commits → PR → CI → merge commit → delete branch.
→ [PROJECT_PLAN.md](PROJECT_PLAN.md)

## Deployment
Free-first; Kafka where hostable, otherwise the documented HTTP mode; persistence verified before claimed.
→ [DEPLOYMENT.md](DEPLOYMENT.md)

## Assumptions · Known limitations · Future improvements
Maintained in the [README](../README.md#assumptions).
