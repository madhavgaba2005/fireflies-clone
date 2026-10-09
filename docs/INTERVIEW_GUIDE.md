# Interview Guide

Answers to the questions most likely to come up in the evaluation interview. Each answer cites real files and tests.
**Format:** 30-second answer · Deeper · Trade-off · Likely follow-up.
The design records behind them are in the [ADRs](adr/) and [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md).

**The system in one breath:**
- A Next.js workspace talks REST to the **Meeting Service**, which is FastAPI + SQLite and the only system of record.
- Creating or changing a transcript writes the meeting **and** an event row to an outbox in one transaction.
- A relay publishes the event to Kafka. The stateless **AI Service** consumes it, generates notes, and publishes the
  result.
- The Meeting Service consumes that result and applies it idempotently.
- The UI shows `pending → processing → completed / failed` and polls only while work is in flight.

---

## Technology choices

### 1. Why Next.js?
- **30 s:** The PDF requires it. Beyond that, the App Router gives file-based routes for the library, workspace and
  settings, and a production build that's easy to host.
- **Deeper:** The app is highly interactive, so almost every page is a client component. Server state goes through
  TanStack Query (`hooks/queries.ts`), and UI state is local React state. I used Next for routing, the build, fonts
  and metadata, not for server data fetching. That keeps a single source of truth for API data: the query cache.
- **Trade-off:** There's a brief loading skeleton on first paint instead of server-rendered data. That's acceptable
  for a logged-in tool. [ADR-001](adr/001-use-nextjs.md)
- **Follow-up:** "Why not Server Components for the data?" → Mutations, optimistic updates and polling all live
  client-side, and mixing the two caches adds invalidation complexity for no user benefit here.

### 2. Why TypeScript?
- **30 s:** It's required, and it catches contract drift. `lib/types.ts` mirrors the API schemas, so a renamed field
  breaks the build instead of the demo.
- **Deeper:** `strict: true`, and `typecheck` runs `next typegen && tsc --noEmit` so route params are typed too.
  Pure logic (`lib/transcript.ts`, `lib/search.ts`, `lib/export.ts`) is typed against minimal interfaces such as
  `Timed`, which makes it trivially unit-testable.
- **Trade-off:** The types are hand-written, not generated from OpenAPI. That's fine at 15 endpoints; I'd generate
  them at 50.
- **Follow-up:** "How do you keep them in sync?" → E2E tests run against the real API, so a mismatch fails CI.

### 3. Why FastAPI?
- **30 s:** Typed request and response models with Pydantic, automatic OpenAPI at `/docs`, async support for the
  Kafka loops, and very little boilerplate.
- **Deeper:**
  - Each service is an app factory, `create_app(settings)`, so tests build isolated apps with their own database and
    processing mode.
  - Background workers (outbox relay, result consumer) start in the lifespan (`app/main.py`).
  - Validation errors and domain errors map to one envelope, `{error:{code,message,details}}` (`app/errors.py`).
- **Trade-off:** Unlike Django, there's no admin or ORM built in. I added SQLAlchemy + Alembic myself, which also
  gives explicit control over the schema. [ADR-002](adr/002-use-fastapi.md)
- **Follow-up:** "Sync or async endpoints?" → CRUD endpoints are sync (SQLite is synchronous, so FastAPI runs them
  in a threadpool). The Kafka loops are async and push their database work to threads via `asyncio.to_thread`.

### 4. Why SQLite?
- **30 s:** It's required. It's also a real relational database with foreign keys, CHECK constraints and
  transactions, with zero operational cost.
- **Deeper:** Every connection sets `foreign_keys=ON`, WAL and `busy_timeout` (`app/database.py`). WAL lets readers
  proceed during a write, and the busy timeout queues writers instead of failing.
- **Trade-off:** There's a single writer, so the Meeting Service runs as one instance. That's documented, and it's
  the main reason the AI work lives in a separate stateless service. [ADR-003](adr/003-use-sqlite.md)
- **Follow-up:** see Q24, migrating off SQLite.

### 5. Why SQLAlchemy?
- **30 s:** Typed 2.0-style models, explicit relationships and cascades, and Alembic migrations, all
  database-agnostic, so moving to Postgres is a URL change plus a migration test.
- **Deeper:**
  - A custom `UTCDateTime` type stores timezone-aware datetimes correctly in SQLite.
  - `test_migrations.py` proves that the Alembic schema equals the models, and that downgrade → upgrade works.
- **Trade-off:** ORMs hide queries. I watch for N+1 (the library uses aggregate queries for action-item counts and
  talk time). In tests, SQLAlchemy warnings are **errors**, because one such warning hid a real bug where the
  summary wasn't saved.
- **Follow-up:** "What was that bug?" → SQLAlchemy 2.x no longer cascades through backrefs, so
  `Summary(meeting=meeting)` was silently not added. The fix was `meeting.summary = summary`, plus making SAWarning
  fatal (`pyproject.toml`).

## Backend design

### 6. Why the repository pattern?
- **30 s:** Repositories own queries; services own rules. Routers stay thin, and each layer is testable alone.
- **Deeper:** For example, `MeetingRepository.search()` builds the filtered, sorted query, while `MeetingService`
  validates participants, parses transcripts, bumps `transcript_revision` and queues processing. Routers just map
  HTTP to service calls.
- **Trade-off:** It adds a layer of indirection. I kept repositories thin (no generic base class) so they read as
  plain SQLAlchemy. [ADR-006](adr/006-service-repository-layer.md)
- **Follow-up:** "Where do transactions live?" → In the service, one per use case. That's what lets the outbox row
  commit atomically with the change.

### 7. Why a service layer?
- **30 s:** Business rules have one home, used by both the API and the event consumer.
- **Deeper:**
  - `SummaryService.apply_result` is called by the Kafka consumer **and** the HTTP fallback path, with identical
    behaviour.
  - `MeetingService.create` is used by the API and the seed loader.
- **Trade-off:** There are more files, but each is short and named for what it does.
- **Follow-up:** "How do you test it?" → Integration tests against a real SQLite database (`tests/integration/`) and
  unit tests for pure parts such as the parser and snippets.

### 8. How is the schema normalized? Why many-to-many for participants?
- **30 s:**
  - `meetings` 1–N `transcript_segments`, `meetings` 1–1 `summaries` (1–N `summary_topics` and `summary_keywords`),
    and `meetings` 1–N `action_items`.
  - `participants` are shared people, linked to meetings through `meeting_participants`.
- **Deeper:**
  - People appear in many meetings, and a speaker or assignee must refer to the same person everywhere. That
    enables filtering by participant, talk time and assignment.
  - The foreign keys say what deletion means. Deleting a meeting **cascades** to its segments, summary and items.
    Deleting a participant who is still referenced is **restricted**. If an assignee goes away, the item stays
    (**SET NULL**).
  - Indexes exist only where a query needs them, e.g. `meeting_date` for sorting and keywords for tag filtering.
  - Each constraint has a test in `test_schema.py`. Details: [DATABASE_DESIGN.md](DATABASE_DESIGN.md).
- **Trade-off:** Summary topics and keywords are separate tables, not JSON. That means more joins, but the tag
  filter is a plain indexed query.
- **Follow-up:** "Why `transcript_revision`?" → So that a late AI result for an old transcript is recognised as
  stale (Q16).

## Architecture

### 9. Why microservices?
- **30 s:** Not microservices for their own sake: exactly two, split where the workload differs. The fast,
  transactional CRUD is the system of record. The slow, retryable, CPU- or LLM-bound AI work is stateless.
- **Deeper:**
  - The AI Service has no database. It receives the whole transcript in the event and returns the result.
  - That means it can scale horizontally, crash or be redeployed without touching data. It is also the place where
    a paid LLM key would live, isolated from the public API.
- **Trade-off:** It brings the costs of a distributed system: eventual consistency, duplicates, a contract between
  the services. Each is handled explicitly (Q14–Q18). [ADR-004](adr/004-two-service-architecture.md)
- **Follow-up:** "How do you keep the contract in sync?" → Byte-identical JSON schemas in both services'
  `tests/contract/`. A CI job `cmp`s them, and both services validate their payloads against them.

### 10. Why only two services?
- **30 s:** Each extra service would need its own data, deployment and failure handling with nothing gained. Search,
  CRUD and action items share one database and one transaction boundary.
- **Deeper:** A good split follows workload or ownership. Splitting "meetings" from "action items" would just turn
  foreign keys into network calls.
- **Trade-off:** The Meeting Service is a modular monolith. Its routers and services are already separated, so a
  later split is mechanical.
- **Follow-up:** "What would you split next?" → Search, if it moved to a dedicated index fed by outbox events.

### 11. Why Kafka?
- **30 s:**
  - Summary generation is slow and can fail, so it shouldn't block a request.
  - Kafka gives a durable, replayable log between the two services.
  - Partitioning by meeting ID keeps each meeting's events in order.
- **Deeper:**
  - Topics: `meeting.events` carries `meeting.created`, `transcript.updated` and `summary.requested`; `ai.events`
    carries `summary.generated` and `summary.failed`.
  - The producer uses `acks=all` and idempotent sends.
  - Consumers commit offsets manually, **after** the database commit, which gives at-least-once delivery.
  - It runs as a single-node KRaft broker in compose.
- **Trade-off:** It's heavier than a task queue. The HTTP fallback (`PROCESSING_MODE=http`) reuses the same envelope,
  processor and apply path for hosts without a broker. It's a fallback only.
  [ADR-005](adr/005-use-kafka-for-async-processing.md)
- **Follow-up:** "Is it actually tested?" → Yes. `pytest -m kafka` runs against a real broker and the AI container
  (`test_pipeline_kafka.py`), and it's a CI job too.

### 12. Why not Kafka for CRUD?
- **30 s:** CRUD is a request the user waits on and must see reflected immediately. One SQLite transaction already
  gives that. Kafka would add latency and eventual consistency for no benefit.
- **Deeper:**
  - Kafka shines for work that is slow, retryable and can finish later, like summary generation.
  - Renaming a meeting or ticking an action item needs read-your-own-writes.
  - Routing those through a broker means the response can't confirm the write happened, the UI would need
    reconciliation, and failure modes multiply.
- **Trade-off:** If many downstream systems needed to react to edits (a search index, analytics), we would *also*
  emit events via the same outbox, but the write itself would stay synchronous.
- **Follow-up:** "So how do other services learn about edits?" → Outbox events such as `transcript.updated`,
  published after commit.

### 13. Why asynchronous processing?
- **30 s:** Creating a meeting returns `201` immediately with `processing_status: pending`. Notes arrive a second or
  so later, or a minute later with a real LLM, and the request never waits.
- **Deeper:**
  - The UI shows a "Generating notes…" state and polls `GET /api/meetings/{id}` every 2 s **only while**
    the status is pending or processing.
  - When the status completes, it shows a "Notes ready" toast and loads the summary.
- **Trade-off:** It uses polling rather than WebSockets or SSE. That's simpler, works on any host, and generation
  is short. SSE would be the upgrade.
- **Follow-up:** "Why does polling stop?" → `refetchInterval` returns `false` once the status is terminal
  (`hooks/queries.ts`).

### 14. How is eventual consistency handled?
- **30 s:** It's made visible and bounded. Only the AI notes are eventually consistent; everything the user edits
  is immediately consistent. The status field tells the UI exactly where processing stands.
- **Deeper:**
  - States: `not_requested → pending` (event in the outbox) `→ processing` (published) `→ completed | failed`.
  - The relay only moves `pending → processing`, so a fast HTTP-mode result is never overwritten.
  - A result for an outdated transcript is ignored as `stale`.
- **Trade-off:** For a moment a meeting can show a transcript without notes. That's honest and expected.
- **Follow-up:** "What if the user edits during processing?" → The edit bumps `transcript_revision` and queues a new
  request. The old result arrives as stale and is dropped, and the new result wins.

### 15. What if Kafka is down?
- **30 s:** Nothing the user does fails. Writes commit to SQLite together with an outbox row. The relay keeps retrying
  with exponential backoff, and when Kafka returns, the backlog is published in order.
- **Deeper:**
  - `OutboxRelay.run_forever` (`app/events/relay.py`) backs off from 1 s up to a maximum.
  - `run_once` stops at the first failure, so each meeting's events stay in order.
  - Failures are recorded on the outbox row (attempts, last error).
- **Trade-off:** The relay polls instead of using change data capture. It's simple and sub-second, with one relay
  instance. [ADR-008](adr/008-transactional-outbox.md)
- **Follow-up:** "Why not publish directly in the request?" → The dual-write problem: the database commit succeeds
  and the publish fails (or the reverse), and the two disagree forever. The outbox makes it one atomic write.

### 16. How do you prevent duplicate events?
- **30 s:** I accept that duplicates will happen (at-least-once delivery) and make applying them idempotent.
  Every event has a UUID, and `processed_events` records each applied ID **in the same transaction** as its effect.
- **Deeper:**
  - `SummaryService.apply_result` returns an outcome: `applied | duplicate | stale | meeting_missing | invalid |
    ignored`.
  - Duplicates are no-ops.
  - Stale results, where `transcript_revision` doesn't match, are dropped.
  - Results for deleted meetings are ignored safely.
  - Tests: `test_summary_results.py`. Against a **real broker**, `tests/kafka/test_duplicates_kafka.py` publishes the
    same result event twice and checks that it is applied once (no doubled topics or action items).
- **Trade-off:** `processed_events` grows over time. In production it would be pruned after the broker's retention
  window.
- **Follow-up:** "Why not exactly-once?" → Kafka's exactly-once covers Kafka-to-Kafka only. With an external
  database, an idempotent consumer is the standard answer.

### 17. What happens if AI processing fails?
- **30 s:** The AI Service retries internally, then publishes `summary.failed` with a reason. The meeting becomes
  `failed`, and the UI shows the reason with a **Retry** button that calls `POST …/summary/regenerate`.
- **Deeper:** `MeetingProcessor` never raises. Every outcome becomes either a result event or a failure event, so the
  consumer loop can't be poisoned by one bad message. Invalid messages are logged and skipped.
- **Trade-off:** There is no dead-letter topic yet. Failure is visible per meeting, which suits a single-user app.
- **Follow-up:** The E2E test "summary generation failure shows the reason and a retry" (`errors.spec.ts`) covers
  this.

### 18. How would retry work?
- **30 s:** It works at three levels:
  - The relay retries publishing with backoff.
  - The AI Service retries generation (`max_retries=3` with exponential backoff, `retry_backoff_seconds=1.0`).
  - The user can retry from the UI, which writes a new outbox event.
- **Deeper:** Retries are safe because the apply path is idempotent and checks the revision.
- **Trade-off:** Fixed retry counts, no jitter. At scale I'd add jitter and a dead-letter topic with replay tooling.
- **Follow-up:** "What about poison messages?" → None is retried forever:
  - A malformed envelope is logged and skipped (`handle_message` → `malformed`).
  - A well-formed result with an invalid payload is recorded in `processed_events` as `invalid`.
  - A database error is retried a few times with backoff, then logged as `gave_up`
    (`app/events/consumer.py`).
  - A dead-letter topic would be the production upgrade.

## Frontend

### 19. How does transcript synchronization work?
- **30 s:**
  - A `PlaybackClock` gives the current time.
  - A binary search, `findActiveSegmentIndex` (`lib/transcript.ts`), finds the segment whose start ≤ t.
  - That line is highlighted and scrolled into view.
  - Clicking a line seeks the clock, and moving the seek bar does the reverse.
- **Deeper:**
  - The clock is anchored to wall-clock time, so it doesn't drift, and it emits on `requestAnimationFrame`. React
    reads it through `useSyncExternalStore` (`hooks/usePlaybackClock.ts`).
  - At a boundary the next segment wins. In a gap, the previous segment stays active.
  - Auto-follow pauses for 4 s after a manual scroll and shows a "Back to current" button.
  - Unit tests: `lib/transcript.test.ts`, `lib/playback.test.ts`. E2E: the workspace spec.
- **Trade-off:** Binary search is O(log n) per frame, which is negligible even for long meetings.
- **Follow-up:** "How does in-transcript search interact?" → Matches are computed by plain substring search (no
  user-supplied RegExp) and rendered as `<mark>` elements, never as HTML strings. Next/previous scrolls without
  stealing playback.

### 20. Why simulated audio?
- **30 s:** Real transcription is out of scope, and the seeded meetings have no recordings. The PDF allows a
  placeholder player. A simulated clock gives the full sync experience with no fake media files.
- **Deeper:** Everything depends on the `PlaybackClock` interface. An `AudioElementClock` wrapping `<audio>` (its
  `currentTime` and events) would drop in without changing the transcript code.
- **Trade-off:** There's no actual sound. The UI says so in the player's info tooltip.
- **Follow-up:** "What changes with real audio?" → Only the clock implementation, plus a media URL on the meeting.

## AI

### 21. Why mock AI?
- **30 s:** It's deterministic, free, and needs no API key, so tests are reliable and the demo always works. The PDF
  explicitly allows mocked summaries.
- **Deeper:**
  - `MockSummaryProvider` (`ai-service/app/providers/mock.py`) picks the most representative sentence for the
    overview, chunks the transcript into timed topics, extracts keywords (no names, numbers or filler), and detects
    action items from commitment phrases. Assignees are the speaker or an addressed participant.
  - It's real logic with tests, not canned text.
- **Trade-off:** The quality is lower than an LLM's. Shipping an untested LLM provider would have been decorative.
  [ADR-007](adr/007-mock-summary-provider.md)
- **Follow-up:** "Why is it in a separate service if it's a mock?" → The service boundary is the point. Replacing
  the provider changes nothing else.

### 22. How would you add a real LLM?
- **30 s:**
  1. Implement `SummaryProvider` with a client for an LLM API (a current Claude model, for example).
  2. Ask for JSON that matches `SummaryGeneratedPayload` and validate it.
  3. Select it with `SUMMARY_PROVIDER=llm` and keep the key in the AI Service's environment only.
- **Deeper:**
  - Chunk long transcripts and summarise the chunks first (map-reduce).
  - Use the existing retries and failure events.
  - Add a timeout and a cost guard.
  - Keep the mock for tests, and contract-test the LLM provider's output schema.
- **Trade-off:** Latency (seconds) and cost per meeting. The async design already absorbs the latency.
- **Follow-up:** "Ask-a-question chat?" → Retrieve relevant segments (FTS or embeddings) and answer with cited
  timestamps that deep-link using the same `?t=` mechanism as global search.

## Scaling, security, operations

### 23. How would you scale the system?
- **30 s:**
  - The AI Service scales horizontally: add consumers to the group, up to the partition count.
  - The Meeting Service is limited by SQLite's single writer. Move to Postgres, then run several stateless API
    replicas.
- **Deeper:**
  - Increase the partitions of `meeting.events`. Ordering per meeting is preserved by keying on the meeting ID.
  - Run the outbox relay as a single leader, or switch to change data capture (Debezium).
  - Add a CDN for the frontend.
- **Trade-off:** Each step adds operational cost, so only take it when metrics demand it.
- **Follow-up:** "First bottleneck?" → Write throughput on SQLite, then LLM cost and latency.

### 24. How would you migrate from SQLite?
- **30 s:** Point `DATABASE_URL` at Postgres, run the Alembic migrations (the models are database-agnostic), copy
  the data, and run the same test suite against Postgres in CI.
- **Deeper:** Watch for SQLite-specific details: the `UTCDateTime` type (Postgres has `timestamptz`), the pragmas in
  `database.py`, and `LIKE` search (move to `tsvector` / `pg_trgm`).
- **Trade-off:** Postgres needs hosting and backups. Until then, SQLite plus volume backups is enough.
- **Follow-up:** "Zero downtime?" → Dual-write via the outbox, or a short read-only window for a dataset this
  size.

### 25. How would you introduce authentication?
- **30 s:** Use an identity provider with OIDC (or NextAuth / Auth.js on the frontend). The API validates JWTs,
  and every query is scoped by `owner_id` / `workspace_id`.
- **Deeper:**
  - Add `users` and `workspaces` tables with memberships, and foreign keys from meetings.
  - A FastAPI dependency resolves the current user, and repositories take it as a required filter, so nothing can
    be queried unscoped.
  - Events carry the workspace ID.
- **Trade-off:** It's out of scope per the PDF. A fixed demo user ("Alex Morgan") stands in.
- **Follow-up:** "Sharing?" → A meeting-level ACL table, checked in the service layer.

### 26. How would you secure the APIs?
- **Already in place:**
  - Pydantic limits on every input, including transcript size.
  - Strict parsers.
  - A CORS allow-list.
  - Generic 500s that never leak internals (`test_errors.py`).
  - `<mark>`-based highlighting with no HTML injection.
  - The internal endpoint uses a token compared with `secrets.compare_digest`.
  - Non-root containers.
  - In production only Caddy is exposed, and Kafka is internal.
- **Next:** auth (Q25), rate limiting at the proxy, security headers, dependency scanning in CI, and Kafka SASL/TLS
  if the broker ever leaves the private network.

### 27. How would search scale?
- **30 s:** Today, global search uses escaped `LIKE` over titles and transcript lines, grouped per meeting with
  snippets. That's instant at this size. Next steps would be SQLite FTS5, then Postgres full-text search, then a
  dedicated index (OpenSearch) fed by outbox events.
- **Deeper:** `LIKE '%q%'` can't use an index, which is fine for thousands of segments. FTS adds ranking and
  stemming. The API shape (`/api/search` returning hits with `start_ms`) stays the same.
- **Trade-off:** I chose simplicity and an explanation I can defend over premature FTS triggers.
- **Follow-up:** "Why escape `LIKE`?" → So that `%` and `_` typed by the user match literally (`test_search_api.py`).

### 28. How does CI work?
- **30 s:** GitHub Actions on every PR and every push to main, with four jobs:
  1. **Backend** (a matrix of both services): ruff, format, mypy, and pytest with a 90 % coverage gate.
  2. **Event contract:** the schemas must be identical in both services.
  3. **Kafka:** compose starts the broker and the AI service, then `pytest -m kafka` runs.
  4. **Frontend:** lint, format, typecheck, unit tests, build, then Playwright against both real services.
- **Deeper:** The E2E tests start both FastAPI services in HTTP mode on a freshly seeded SQLite database and run a
  production frontend build, so the browser tests hit real APIs, not mocks.
- **Trade-off:** It's not yet run on GitHub, because the repo is unpublished. Every command was run locally, and
  the backend job in a clean Linux container.
- **Follow-up:** "Flaky tests?" → Timing-sensitive specs were run repeatedly (`--repeat-each`). Two real UI races
  were found and fixed that way.

### 29. Why this Git branching strategy?
- **30 s:** One issue leads to one feature branch, then logical commits, then a PR with a description, then a
  `--no-ff` merge into `main`. `main` is always green, and history reads as a list of features.
- **Deeper:** Commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`). PR descriptions are
  archived in [PULL_REQUESTS.md](PULL_REQUESTS.md) until the repository is published.
- **Trade-off:** Merge commits instead of squashing keep the logical commits, which helps the interview walkthrough.
- **Follow-up:** "Why not trunk-based?" → It would be fine for a solo developer, but feature branches map each PR to
  a requirement for review.

---

### 30. How did you test it?
- **30 s:** I test at three levels, and each requirement maps to a test in
  [TEST_COVERAGE_MATRIX.md](TEST_COVERAGE_MATRIX.md):
  - **Pure logic as unit tests:** parser, mock provider, active-segment search, transcript search, export, theme.
  - **API and database as integration tests:** a real SQLite file, with constraints, cascades and the
    idempotent consumer.
  - **Every must-have workflow in a real browser** (Playwright) against both real services.
  - **Kafka against a real broker.**
- **Numbers (latest run):**
  - 183 meeting-service tests (97 % line + branch coverage) and 39 AI-service tests (99 %).
  - 3 real-Kafka tests.
  - 76 Vitest tests.
  - 45 Playwright tests.
- **Trade-off:** E2E runs the services in HTTP mode, so the browser suite needs no broker; the separate `kafka` job
  covers the broker. Tests never weaken a check to pass. When a test failed, either the code or a wrong assumption in
  the test was fixed, and both cases are recorded in PROGRESS.md.
- **Follow-up:** "What would you add?" → Visual regression snapshots, and a load test on the outbox relay.

### 31. How is it deployed?
- **30 s:** `deploy/docker-compose.prod.yml` runs everything on one VM. Caddy terminates HTTPS and is the only
  public port. Behind it run the Next.js standalone server, both FastAPI services and a single-node Kafka. SQLite
  lives on a named volume.
- **Deeper:**
  - One origin means no CORS: Caddy routes `/api` and `/health` to the Meeting Service and everything else to the
    frontend.
  - Health checks gate the startup order: Kafka, then the services, then Caddy.
  - A free VM can host the whole real architecture, including Kafka. The fallback for a platform without Kafka is
    `PROCESSING_MODE=http` with a persistent volume.
  - Verified locally: a Kafka summary in about 2 s, and data survived a full restart.
- **Trade-off:** It's a single VM: simple and free, but not highly available. That's fine for a demo.
- **Follow-up:** "Zero-downtime deploys?" → Not needed at this scale. Next steps would be blue/green behind Caddy, or
  moving the stateless services to a container platform with Postgres.

## Bugs worth telling (each was found by a test)
1. **Summary silently not saved:** SQLAlchemy 2.x backref cascade. Fixed, and SAWarning is now fatal in tests.
2. **Reseed collision:** bulk DELETE + SQLite row-ID reuse + stale identity map. Fixed with `expunge_all()`.
3. **Checkbox flicker:** the optimistic state was set after an `await`. Fixed with local optimistic state in the row.
4. **Missing toasts:** `mutate` callbacks don't run if the component unmounts. Fixed by switching to `mutateAsync`.
5. **Seek while paused** didn't scroll to the active line. The follow effect no longer requires `playing`.
