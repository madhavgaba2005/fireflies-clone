# Development Guide (study document)

> Living document — the author's primary study material for the evaluation interview.
> Status: **Phase 2** — every *design* decision below is final; scaffolding is explained in the Phase 2 section; implementation details (file names, code
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
Scaffolding (Phase 2): [App factory](#app-factory-create_appsettings) · [Configuration](#configuration-appconfigpy) ·
[Database layer](#database-connection-layer-appdatabasepy) · [Error envelope](#error-envelope-apperrorspy) ·
[Event publishers](#event-publisher-abstraction-appevents) · [Tooling](#tooling) · [Docker Compose](#local-infrastructure-docker-composeyml)

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
Stateless worker: consume `meeting.created`/`transcript.updated`/`summary.requested` → `MeetingProcessor` →
`SummaryProvider.generate()` (in a worker thread, retried with backoff) → publish `summary.generated` or
`summary.failed`. The processor never raises, so one bad message can't block a partition. In HTTP mode the same
processor answers `POST /internal/process`. **30 s:** "Transcript in, notes out, no database — so it can be restarted,
swapped or scaled freely; Kafka and HTTP are just two doors into the same processor."

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

## Transactional outbox
1. **What:** a table (`outbox_events`) that stores events in the **same transaction** as the data change they describe.
2. **Why:** a request can't atomically write to SQLite *and* Kafka. Publishing inside the request either loses the event
   (commit succeeded, publish failed) or announces data that never committed (publish before commit).
3. **Problem solved:** "the meeting exists but its summary request was lost" can't happen.
4. **How:** `queue_processing()` adds the envelope to `outbox_events` in the create/regenerate transaction.
   `OutboxRelay` (a background task) reads unpublished rows oldest-first, publishes, and sets `published_at`.
   Failure → `attempts`/`last_error` recorded, exponential backoff, the row is retried. At-least-once.
5–6. **Alternatives:** publish after commit (loses events on crash/outage); CDC with Debezium (production-grade but far
   too heavy for SQLite); Kafka transactions (don't cover the SQLite write).
7. **Advantages:** no lost events; the API works even when Kafka is down. 8. **Disadvantages:** ~1 s extra latency,
   an extra table, duplicates possible (handled by the idempotent consumer).
9. **Failure modes:** relay crash → rows stay unpublished until restart; poison row → retried forever with backoff
   (visible in `last_error`). 10. **Scaling:** multiple relays would need row claiming (`SELECT … FOR UPDATE SKIP LOCKED`
   in Postgres). 11. **Place:** inside the Meeting Service, between the services and the publisher.
12. **30 s:** "The request only writes to the database — the event goes into an outbox table in the same transaction.
   A background relay publishes it to Kafka, retrying until it succeeds, so an event can be duplicated but never lost."
13. **Follow-ups:** What if the relay publishes and crashes before marking the row? (published again → the consumer
   de-duplicates by event id) · Why stop the batch at the first failure? (keeps events for one meeting in order).

## Eventual consistency
1. **What:** the summary isn't available the moment a meeting is created; it becomes consistent a few seconds later.
2. **Why:** AI work is slow and can fail; the user shouldn't wait for it or lose their meeting because of it.
3. **How:** `processing_status` makes the gap explicit — `pending` (in the outbox) → `processing` (handed to Kafka) →
   `completed` / `failed`. The UI polls the meeting every 2 s only while pending/processing, shows "Generating notes…",
   then a toast; `failed` shows the reason and a Retry button (`POST /summary/regenerate`).
4. **Safety rules:** results are applied idempotently (`processed_events`), results for an older `transcript_revision`
   are discarded (`stale`), results for deleted meetings are dropped, and regeneration replaces only AI-sourced action
   items — never what the user created or edited.
5. **Strong consistency where it matters:** every user write (CRUD) is a single synchronous SQLite transaction.
12. **30 s:** "CRUD is strongly consistent; only AI output is eventually consistent, and the UI shows that state honestly
   with a processing status instead of pretending it's instant."
13. **Follow-ups:** Why poll instead of WebSockets? (one page needs it, works through every proxy) · What if the result
   arrives before the relay marks `processing`? (the relay only moves `pending → processing`, so a completed meeting
   stays completed — tested).

## Summary generation
`SummaryProvider` interface; `MockSummaryProvider` (default, deterministic heuristics); optional LLM provider.
Seeded meetings use hand-written summaries. **How the mock works:** keywords = frequent meaningful words (stop-words,
numbers and names removed); chapters = equal runs of segments titled by their own keywords and summarized by their
most informative sentence; action items = commitment phrases ("I'll …" → the speaker, "Sarah, can you …" → Sarah,
"we need to … by Friday" → unassigned). **30 s:** "A pluggable provider: a deterministic mock by default so the demo is
free and tests are exact; an LLM drops in behind the same interface." → [ADR-007](adr/007-mock-summary-provider.md)

## Transcript synchronization
1. **What:** Two-way link between player position and transcript. 2. **Why:** PDF must-have R2.3/R2.4 and the core Fireflies interaction.
3. **Problem:** Clicking a line must seek; playback must highlight and reveal the current line.
4. **How:** A `PlaybackClock` interface (`currentMs`, `play`, `pause`, `seek`, `rate`, subscribe). `SimulatedClock` advances time with `requestAnimationFrame`; an `HtmlMediaClock` can wrap `<audio>` later. `findActiveSegmentIndex(segments, ms)` binary-searches sorted `start_ms`, active when `start_ms ≤ t < end_ms`; in a gap, the previous segment stays active. Click line → `seek(start_ms)` + play. Active index change → `scrollIntoView({block: 'center'})`, paused for a few seconds after manual scrolling.
5. **Alternatives:** Linear scan per frame; real audio from TTS. 6. **Rejected:** O(n) per frame is fine but binary search is no harder; TTS costs time for no grading value.
7. **Adv:** Same logic works with real media. 8. **Dis:** No sound in the demo.
9. **Failure/edge cases:** t exactly on a boundary, t before the first segment, gaps, t ≥ duration, empty transcript — each unit-tested.
10. **Scaling:** O(log n) per tick. 11. **Place:** Frontend workspace. 12. **30 s:** "One clock is the source of truth; a binary search maps time to the active line; clicking a line just seeks the clock."
**Implementation:** `lib/playback.ts` (`SimulatedClock`: time = anchor position + elapsed wall-clock × rate, so
skipped frames or background tabs never drift), `hooks/usePlaybackClock.ts` (`useSyncExternalStore`),
`lib/transcript.ts` (`findActiveSegmentIndex`), `components/transcript/TranscriptPanel.tsx` (memoized lines,
auto-follow with a 4 s manual-scroll grace period), `components/workspace/MeetingWorkspace.tsx` (wiring, keyboard).
**Performance:** the clock ticks every animation frame, but only the player re-renders each frame; `TranscriptPanel`
is memoized and receives just `activeIndex`, so it re-renders when the active line *changes*, and each
`TranscriptLine` is memoized too. **Tests:** 9 boundary cases + clock behaviour (Vitest), 4 E2E sync tests.
13. **Follow-ups:** What happens at exact boundaries? Why not re-render every line each frame? (memoized lines, only active index changes trigger re-render)

## Transcript search
Client-side, case-insensitive. Query is regex-escaped; text is split into match/non-match fragments rendered as
`<mark>` — never `dangerouslySetInnerHTML`, so uploaded text cannot inject HTML. "n of m" counter, Enter/Shift+Enter
navigation. **30 s:** "Search runs in the browser over already-loaded segments and highlights safely with React
elements." Implemented in `lib/search.ts` + `TranscriptPanel.tsx`; tested by `search.test.ts` and two E2E specs.

## Frontend state management
1. **What:** server state (meetings, transcripts, summaries, action items) lives in **TanStack Query**; UI state
   (dialogs, filters, search query, playback) lives in React state, the URL, or the playback clock.
2. **Why:** the rubric looks at loading/error states and fresh data after mutations — a query cache provides both
   without Redux boilerplate. 3. **How:** one hook per endpoint in `hooks/queries.ts`; every mutation invalidates
   exactly the queries it changes (`keys.*`); the meeting query polls every 2 s only while notes are pending/processing.
4. **Optimistic action items:** the row keeps a local optimistic value set synchronously on click (no flicker) and
   cleared when the server answers; failures roll back and toast.
5. **A lesson worth telling:** `mutate(vars, { onSuccess })` callbacks are skipped if the component unmounts first —
   a deleted row unmounts after the refetch, so its "deleted" toast sometimes never showed (caught by repeated E2E
   runs). Using `await mutateAsync()` fixed it: the promise settles regardless of unmounting.
6. **Alternatives:** Redux/Zustand (more code for server state), SWR (similar; weaker mutation API), hand-written
   `useEffect` fetching (re-implements caching and invalidation).
12. **30 s:** "Server data is cached by TanStack Query with one hook per endpoint and targeted invalidation; everything
   else is local state or the URL. The only polling is while AI notes are being generated."

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

---

# Phase 2 — scaffolding: what exists and why

## App factory (`create_app(settings)`)
1. **What:** Both services build their FastAPI app in a function instead of at import time.
2. **Why:** Tests create a fresh app with their own settings (temp database, no broker); importing a module never opens files or connections.
3. **Problem:** Module-level `app = FastAPI()` + global engine makes tests share state and read the developer's `.env`.
4. **How:** `create_app` reads `Settings`, builds a `Database`, stores both on `app.state`, adds CORS + error handlers + routers. Uvicorn runs it with `--factory`.
5–6. **Alternatives:** global app with dependency overrides — works, but every test must remember to override; rejected for isolation.
7. **Adv:** isolated, explicit wiring in one function. 8. **Dis:** `uvicorn ... --factory` must be remembered (it's in every README/Dockerfile).
9. **Failure:** invalid config → `Settings` raises at startup (fail fast). 10–11. n/a; entry point of each service.
12. **30 s:** "Each service has an app factory, so the app is built from explicit settings — production reads env vars, tests pass a temporary SQLite file."
13. **Follow-ups:** Where does the Kafka consumer start? (the lifespan inside the factory, Phase 5–6)

## Configuration (`app/config.py`)
`pydantic-settings` reads environment variables (and an optional `.env`), with types and defaults. Each service owns
its own `Settings` — no shared config package, because services deploy independently. Cross-field rules fail fast:
`PROCESSING_MODE=http` without `INTERNAL_API_TOKEN`, or `SUMMARY_PROVIDER=llm` without `LLM_API_KEY`, refuses to start.
`.env.example` documents every variable; real `.env` files are git-ignored.
**30 s:** "Typed settings from the environment; invalid combinations crash at startup instead of failing at 2 a.m."
**Follow-up:** "Why is `NEXT_PUBLIC_API_URL` not a secret?" → it is compiled into the browser bundle by design.

## Database connection layer (`app/database.py`)
`Database` owns the engine and session factory. A `connect` listener sets `foreign_keys=ON` (SQLite ignores FKs
otherwise), `journal_mode=WAL` (readers don't block the writer) and `busy_timeout=5000`. `check_same_thread=False`
because FastAPI runs sync endpoints in a thread pool — safe since each request gets its own session from the
`SessionDep` dependency, which always closes it. `ping()` backs `/health/ready`.
**Verified by:** `tests/integration/test_database.py` (pragmas, directory creation, unreachable DB, session lifecycle).
**30 s:** "One object owns the engine; every connection gets the SQLite pragmas; every request gets its own session."

## Error envelope (`app/errors.py`)
Services raise `NotFoundError` / `ConflictError` (subclasses of `DomainError`); four handlers turn domain errors,
validation errors, routing errors and unexpected exceptions into `{"error": {code, message, details}}`.
Unexpected errors are logged with the stack trace and returned as a generic 500.
**Verified by:** `tests/integration/test_errors.py`. **30 s:** "One error shape for every failure; internals stay in the log."

## Health endpoints
`/health` = liveness (process is up; touches nothing, so it can't cause restart loops).
`/health/ready` = readiness (database answers → 200, else 503). Used by compose, hosting platforms and smoke tests.

## Event publisher abstraction (`app/events/`)
```
EventEnvelope (envelope.py)       versioned, frozen, extra fields forbidden
EventPublisher (publisher.py)     Protocol: start() · stop() · publish(envelope)
 ├─ KafkaEventPublisher           aiokafka, acks=all + idempotent producer, key = meeting id
 ├─ HttpEventPublisher            FALLBACK: POST envelope → AI /internal/process → result to on_result()
 └─ InMemoryEventPublisher        tests only: records events
build_publisher(settings, on_result)   picks one from PROCESSING_MODE
```
Phase 2 builds and tests the transports; Phase 5 wires them into the outbox relay. Kafka is verified against a real
broker (`tests/kafka/`, CI `kafka` job). The producer is injected (`producer_factory`) so unit tests use a fake
producer, not a mock of aiokafka internals.
**Contract:** each service has its own copy of the envelope; both must equal `tests/contract/envelope_v1.schema.json`,
and CI fails if the two schema files differ.
**30 s:** "Business code publishes an envelope through one interface; Kafka is the real transport, HTTP is a documented
fallback, in-memory is for tests — and a contract test stops the two services' event formats drifting."
**Follow-ups:** Why `Protocol` and not an abstract base class? (structural typing; implementations don't inherit
anything) · Why `acks=all`? (the broker confirms the write is replicated before we mark the outbox row published).

## Layer packages
`models/ schemas/ routers/ services/ repositories/ events/` exist now with a docstring stating their rule
(e.g. "routers only speak HTTP"), so every later file has an obvious home. They fill up from Phase 3.

## Tooling
| Tool | Role | Why this one |
|------|------|--------------|
| ruff | Python lint + format | One fast tool replaces flake8 + isort + black |
| mypy (strict) | Python types | Catches wrong types across layers before tests do |
| ESLint (next config) + Prettier | TS lint + format | Next's recommended rules; Prettier owns formatting (`eslint-config-prettier` disables overlapping rules) |
| `next typegen && tsc --noEmit` | TS types | Next generates route types (`LayoutProps`, `PageProps`) that plain `tsc` can't see |
| Vitest | Frontend unit tests | Native TS/ESM, near-zero config — for pure logic like `findActiveSegmentIndex` |
| Playwright | E2E | Real browser against a production build |
| `.gitattributes` | LF everywhere | Windows checkouts would otherwise get CRLF and fail format checks in CI |

## Local infrastructure (`docker-compose.yml`)
Single-node Kafka 3.9 in KRaft mode (no ZooKeeper) with two listeners: `localhost:9092` for tools on the host,
`kafka:29092` for containers. Both services run as non-root users; the SQLite file lives on a named volume.
The frontend runs natively for fast hot reload.
**Follow-up:** "Why two listeners?" → a Kafka client connects to whatever address the broker *advertises*; host and
container networks need different addresses.

## Assumptions · Known limitations · Future improvements
Maintained in the [README](../README.md#assumptions).
