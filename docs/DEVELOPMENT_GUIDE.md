# Development & Architecture Guide

> Living document. Each technology/decision answers: **What · Why · Problem solved · Alternatives · Why not them ·
> Pros · Cons · Production changes · How to explain it.** Sections marked _(Phase N)_ are completed when that phase lands.

## Assignment Goals
Recreate the Fireflies post-meeting experience (library → workspace with synced transcript + AI notes + CRUD) on
Next.js/TS + FastAPI + SQLite. Graded on functionality, UI similarity, DB design, API design, code quality,
modularity, and the author's ability to explain it. See [EVALUATION_MATRIX.md](EVALUATION_MATRIX.md).

## Requirements
Every PDF line is tracked in [REQUIREMENTS_MATRIX.md](REQUIREMENTS_MATRIX.md) with implementation, test and status.

## Architecture
See [ARCHITECTURE.md](ARCHITECTURE.md). One-line version: *a FastAPI system of record over SQLite, plus a stateless AI
worker fed through Kafka; the browser only ever talks REST to the Meeting Service.*

## Frontend Architecture
- **What:** Next.js App Router, TypeScript strict, Tailwind, Radix primitives, TanStack Query.
- **Why:** Next.js is mandated. Pages are interactive (player, search), so pages are client components fed by a typed
  `lib/api.ts`; TanStack Query gives loading/error states, caching and cache invalidation after mutations for free —
  exactly the UX states the rubric looks for — without Redux.
- **Alternatives:** Redux (too much ceremony for server state), SWR (fine, but weaker mutation story), plain `useEffect` fetches (re-implementing caching/invalidation by hand).
- **Explain it:** "Server state lives in TanStack Query, UI state in local React state, and complex logic (sync, search) in pure functions + hooks so it is testable."
_(Phase 8+: routing table, data-fetching map, component inventory)_

## Backend Architecture
Layered: `routers` (HTTP only) → `services` (business rules, transactions) → `repositories` (SQL only) → SQLAlchemy → SQLite.
Domain exceptions (`NotFoundError`, `ConflictError`) are raised in services and mapped to the error envelope by one handler.

## Meeting Service
System of record. Owns REST API, validation, transcript parsing, the outbox relay and the AI-result consumer. _(Phase 3–6)_

## AI Processing Service
Stateless: consume → `SummaryProvider.generate(transcript)` → publish. No database, so it can be scaled or replaced freely. _(Phase 7)_

## Kafka
See [EVENT_DRIVEN_ARCHITECTURE.md](EVENT_DRIVEN_ARCHITECTURE.md) and [ADR-003](adr/003-use-kafka-for-async-processing.md).

## Event-Driven Processing
Outbox for reliable publishing, `processed_events` + `transcript_revision` for idempotent, stale-safe consumption. _(Phase 6)_

## SQLite
Mandated. WAL mode for concurrent reads during writes; `foreign_keys=ON` per connection; `busy_timeout` to avoid
"database is locked". Single writer process is the main limitation. [ADR-002](adr/002-use-sqlite.md)

## SQLAlchemy
2.0-style typed ORM (`Mapped[...]`). Parameterized queries by construction → no SQL injection. Relationship loading is
explicit (`selectinload`) to avoid N+1 on the list page. _(Phase 4)_

## Pydantic
Request/response contracts with field limits; separate `Create`/`Update`/`Read` schemas so clients can't set server-owned fields (`id`, `completed_at`, `source`). Also models the event envelope. `pydantic-settings` for config.

## Repository Layer
Only place SQL is written. Lets services be tested with a real in-memory SQLite and keeps query optimisations local. [ADR-005](adr/005-repository-service-layer.md)

## Service Layer
Business rules (speaker must be participant, AI items vs manual items, revision bump), transaction boundaries, outbox writes.

## API Layer
Thin FastAPI routers; dependency-injected DB session and services. See [API.md](API.md).

## Database Schema
See [DATABASE_DESIGN.md](DATABASE_DESIGN.md).

## Relationships
M:N meetings↔participants; 1:N meeting→segments/action items; 1:0..1 meeting→summary; speaker and assignee FKs to participants.

## Transcript Synchronization
_(Phase 11)_ Plan: `useMediaClock` exposes `{currentMs, playing, seek, play, pause, rate}` over an `<audio>` element
(or a simulated clock when no media). `findActiveSegmentIndex(segments, ms)` = binary search over sorted `start_ms`
(O(log n) per `timeupdate`/animation frame). Click line → `seek(start_ms)`. Active index change → `scrollIntoView({block:'center'})` unless user scrolled in the last 4 s.

## Search
Library: server-side title `LIKE`. Transcript: client-side, case-insensitive; text is split into match/non-match
fragments and matches rendered as `<mark>` elements — never via `dangerouslySetInnerHTML`, so uploaded text can't inject HTML. Query is regex-escaped. _(Phase 12)_

## Filtering
Combinable query params; filter state lives in the URL (shareable, survives refresh). _(Phase 9)_

## CRUD
See API.md. Action-item toggles are optimistic with rollback. _(Phase 12–13)_

## AI Summary Pipeline
`SummaryProvider` interface → `MockSummaryProvider` (deterministic heuristics: chapters by time windows + speaker
turns, keywords by TF-IDF-style term frequency minus stop-words, action items by commitment phrases) → optional
`LLMSummaryProvider` when `LLM_API_KEY` is set. [ADR-006](adr/006-mock-summary-provider.md) _(Phase 7)_

## Testing
See [TESTING.md](TESTING.md).

## Code Coverage
pytest-cov with a fail-under threshold; numbers reported only from generated reports. _(Phase 14)_

## CI
See [CI_CD.md](CI_CD.md).

## Git Workflow
See [PROJECT_PLAN.md](PROJECT_PLAN.md).

## Pull Requests
One issue per PR, template with test evidence + requirement IDs; CI must pass before merge.

## Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md).

## Security Considerations
Input limits (Pydantic, upload size/type), parameterized SQL, CORS allow-list, no secrets in git (`.env.example` only),
generic 500 messages, React auto-escaping for all user/transcript text, no auth (documented assumption).

## Error Handling
Domain exceptions → single handler → `{error:{code,message,details}}`. Frontend maps errors to toasts or inline ErrorState.

## Loading / Empty / Error States
Enumerated per screen in [UI_DESIGN_SPEC.md §6](UI_DESIGN_SPEC.md#6-states).

## Design Trade-offs
See [TRADEOFFS.md](TRADEOFFS.md).

## Architectural Alternatives
See each ADR's "Alternatives" section in [adr/](adr/).

## Assumptions
Listed in README#assumptions.

## Known Limitations
_(maintained)_

## Future Improvements
_(maintained)_

## Interview Questions & Answers
See [INTERVIEW_GUIDE.md](INTERVIEW_GUIDE.md).
