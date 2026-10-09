# Evaluation Matrix

Maps each of the PDF's seven evaluation criteria to **concrete, checkable evidence** in this repository.
An evaluator should be able to verify every "Evidence" cell in under a minute.
Status uses the same legend as [REQUIREMENTS_MATRIX.md](REQUIREMENTS_MATRIX.md): ✅ verified by passing tests or a
documented run · 🟨 in progress · ⬜ not started. The PDF gives seven criteria and **no numeric weights**; none are
invented here. §8 lists what an evaluator is likely to inspect, the main risks, and what we did about them.

Paths: `ms/` = `backend/meeting-service`, `ai/` = `backend/ai-service`, `fe/` = `frontend`.

---

## 1. Functionality

> PDF: *"All core features working correctly, including the interactive transcript and summary views"*

| Evidence | Where | Req IDs | Status |
|----------|-------|---------|--------|
| Library: a meetings table with title, participants, date, time and duration in aligned columns, grouped by week | `/meetings` — `fe/components/meetings/` | R1.1 | ✅ |
| Title search, date presets + custom range, participant filter, sort, keyword tags — combinable and URL-synced | `/meetings?q=…&participant=…&date=7d` | R1.2–R1.5 | ✅ |
| Transcript with speaker, avatar and timestamp per line | `/meetings/{id}` right panel | R2.1 | ✅ |
| Player: play/pause, ±15 s, seek bar with speaker timeline, speed 0.75–2× | bottom player bar | R2.2 | ✅ |
| Click a line/chapter/action-item timestamp → player seeks and plays; playback and seeking → active line highlighted and scrolled into view | workspace | R2.3, R2.4 | ✅ |
| In-transcript search: highlighted matches, "n / m", ↑/↓, Enter / Shift+Enter, "No matches" | transcript header | R2.5 | ✅ |
| Keywords, overview, timestamped outline, action items grouped by assignee, talk time | left panel | R3.1–R3.3 | ✅ |
| New meeting → "Generating notes…" → notes appear without reload + toast | create flow | R3.4, X2 | ✅ |
| Create (upload .txt/.vtt/.json, paste, form), edit, delete | dialogs | R4.1–R4.5 | ✅ |
| Add / edit / complete / uncomplete / delete action items | action items section | R4.6–R4.8 | ✅ |
| Everything survives a refresh and a server restart | any | R4.9 | ✅ |
| **Proof:** 45 Playwright tests drive all of the above against the real stack | `fe/tests/e2e/` | all | ✅ |

## 2. UI/UX

> PDF: *"Visual similarity to the original app's design and UX patterns"*

| Evidence | Where | Status |
|----------|-------|--------|
| Design spec written from the Fireflies product site and help-centre guides before any UI code | [UI_DESIGN_SPEC.md](UI_DESIGN_SPEC.md) | ✅ |
| Left sidebar (active state, Workspace section, live-assistant card), top bar with search, "Add to live meeting", purple "New meeting", avatar menu | `fe/components/layout/` | ✅ |
| Two-panel notepad (notes left, transcript right) with a docked player bar; either panel can be expanded to full width | `fe/components/workspace/MeetingWorkspace.tsx` | ✅ |
| Notes in Fireflies' order: keywords → overview → outline → action items (by assignee) → talk time | `fe/components/summary/NotesPanel.tsx` | ✅ |
| Consistent per-person colours across avatars, speaker names, speaker timeline and talk-time bars | `fe/lib/colors.ts` | ✅ |
| Loading skeletons, empty states (no meetings / no matches / no transcript / no action items), error states with Retry, not-found page | `fe/components/ui/States.tsx` | ✅ |
| Toasts for every mutation and failure; "Coming soon" dialogs for out-of-scope features | sonner, `ComingSoon.tsx` | ✅ |
| Keyboard: Space play/pause, ←/→ seek, `/` find, Enter/Shift+Enter matches, Esc closes dialogs | `MeetingWorkspace.tsx`, Radix | ✅ |
| Responsive: sidebar → drawer, panels → tabs, no horizontal scroll at 390 px (E2E-tested) | `responsive.spec.ts` | ✅ |
| Screenshots of the real app in the README (light, dark, phone) | [README#screenshots](../README.md#screenshots) | ✅ |
| Two visual QA passes: findings and fixes recorded | [UI_FIDELITY_AUDIT.md](UI_FIDELITY_AUDIT.md) | ✅ |
| Theme: Settings → Appearance with System / Light / Dark (bonus) | `fe/components/settings/SettingsPage.tsx`, `fe/lib/theme.ts` | ✅ |

## 3. Database Design

> PDF: *"Well-structured schema with proper relationships"*

| Evidence | Where | Status |
|----------|-------|--------|
| ER diagram, per-table rationale, 3NF argument, deviations from the brief explained | [DATABASE_DESIGN.md](DATABASE_DESIGN.md) | ✅ |
| M:N `meetings ↔ participants` via `meeting_participants` (composite PK + reverse index) | `ms/app/models/meeting.py` | ✅ |
| Speakers and assignees are FKs to `participants` — no repeated name strings | `transcript_segments.speaker_id`, `action_items.assignee_id` | ✅ |
| 1:1 `meetings → summaries` enforced by `UNIQUE(meeting_id)`; topics and keywords as child tables | `summaries`, `summary_topics`, `summary_keywords` | ✅ |
| Integer-ms times with `CHECK (start_ms >= 0)`, `CHECK (end_ms >= start_ms)`; `UNIQUE(meeting_id, sequence)` | `transcript_segments` | ✅ |
| Explicit `ON DELETE`: CASCADE (owned children), RESTRICT (speakers), SET NULL (assignee); FKs enforced per connection | models + `ms/app/database.py` | ✅ |
| UTC-only datetime type; NOCASE-unique names | `ms/app/models/types.py` | ✅ |
| Outbox + processed-events tables for reliable, idempotent events | `ms/app/models/events.py` | ✅ |
| Alembic migration, run on startup; test proves migration ≡ models | `ms/alembic/`, `test_migrations.py` | ✅ |
| Tests prove every constraint fires (cascade, RESTRICT, SET NULL, UNIQUE, CHECK) | `ms/tests/integration/test_schema.py` | ✅ |

## 4. Backend / API Design

> PDF: *"Clean, sensible API design and architecture"*

| Evidence | Where | Status |
|----------|-------|--------|
| 15 resource-oriented operations + 2 health endpoints, nested only where ownership is real | [API.md](API.md), `/docs` | ✅ |
| Router → Service → Repository: routers have no SQL, services no HTTP, repositories no rules | `ms/app/routers`, `services`, `repositories` | ✅ |
| Separate Create / Update / Read schemas with field limits; 422 with field details | `ms/app/schemas` | ✅ |
| One error envelope `{error: {code, message, details}}` for domain, validation, routing and unexpected errors | `ms/app/errors.py`, `test_errors.py` | ✅ |
| Correct status codes (200/201/202/204/400/404/405/409/422/500), each tested | `test_meetings_api.py`, `test_action_items_api.py` | ✅ |
| Pagination (`limit`/`offset` + `total`), N+1-free list query | `ms/app/repositories/meetings.py` | ✅ |
| OpenAPI at `/docs` with documented error responses | FastAPI | ✅ |
| Async processing: transactional outbox, Kafka, idempotent consumer, visible `processing_status`; CRUD stays synchronous | [EVENT_DRIVEN_ARCHITECTURE.md](EVENT_DRIVEN_ARCHITECTURE.md) | ✅ (3 real-broker tests incl. duplicate delivery) |
| `/health` (liveness) and `/health/ready` (database) on both services; compose healthchecks | `routers/health.py` | ✅ |
| Environment-based config, fail-fast validation, `.env.example` files | `app/config.py` ×2 | ✅ |

## 5. Code Quality

> PDF: *"Clean, readable, and well-organized code"*

| Evidence | Where | Status |
|----------|-------|--------|
| ruff (lint + format) and `mypy --strict` clean on both services; ESLint, Prettier, `tsc --strict` clean on the frontend | local runs; CI workflow | ✅ (CI not yet run on GitHub) |
| SQLAlchemy warnings turned into test failures (caught a real silent-data-loss bug) | `ms/pyproject.toml` | ✅ |
| Backend coverage gate 90 % (measured: 97.45 % meeting-service, 98.84 % ai-service, line + branch) | CI, [TESTING.md](TESTING.md) | ✅ |
| Small focused modules; comments explain *why*, not *what* | review | ✅ |
| No secrets in the repository; only `.env.example` files tracked | `git ls-files` check | ✅ |
| Conventional commits on feature branches merged with `--no-ff`; PR descriptions archived | `git log --graph`, [PULL_REQUESTS.md](PULL_REQUESTS.md) | ✅ |

## 6. Code Modularity

> PDF: *"Proper separation of concerns, reusable components"*

| Evidence | Where | Status |
|----------|-------|--------|
| Two independently runnable/testable services; the only contract is a versioned envelope + payloads, pinned on both sides | `*/tests/contract/`, CI `event-contract` | ✅ |
| `EventPublisher` (Kafka / HTTP fallback / in-memory) — business code never knows the transport | `ms/app/events/` | ✅ |
| `SummaryProvider` interface (mock today; LLM = one class) and one `MeetingProcessor` shared by Kafka and HTTP | `ai/app/providers`, `ai/app/processors` | ✅ |
| Transcript parser module per format (txt / vtt / json) behind one function | `ms/app/services/transcript_parser.py` | ✅ |
| `PlaybackClock` interface: simulated clock now, a media-element clock later — sync code unchanged | `fe/lib/playback.ts` | ✅ |
| Pure, unit-tested logic outside JSX: active segment, search, filters, formatting | `fe/lib/*.ts` (76 Vitest tests) | ✅ |
| Reusable components: `Modal`, `Menu`, `Avatar(Stack)`, `StatusChip`, `EmptyState/ErrorState`, `ParticipantsInput`, `ActionItemEditor` (add + edit) | `fe/components/ui`, … | ✅ |
| Server state in one place (TanStack Query hooks, targeted invalidation) | `fe/hooks/queries.ts` | ✅ |

## 7. Code Understanding

> PDF: *"Ability to explain your code during evaluation"*

| Evidence | Where | Status |
|----------|-------|--------|
| Architecture: request, event, failure and data flows; why two services | [ARCHITECTURE.md](ARCHITECTURE.md) | ✅ |
| ADRs (context / decision / alternatives / trade-offs / consequences) with implementation notes | [adr/](adr/) | ✅ |
| Development guide: what / why / how / alternatives / failure modes / 30-second answers | [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) | ✅ |
| Interview guide: 31 answers that cite real files and tests | [INTERVIEW_GUIDE.md](INTERVIEW_GUIDE.md) | ✅ |
| 8-minute demo script using the exact UI labels | [FINAL_DEMO_SCRIPT.md](FINAL_DEMO_SCRIPT.md) | ✅ |
| Deliberately small architecture, honest trade-offs and limitations | [TRADEOFFS.md](TRADEOFFS.md) | ✅ |

## 8. Inspection, risks and score maximization

| Criterion | Evaluator will likely… | Biggest risks | How we maximize |
|-----------|------------------------|---------------|-----------------|
| Functionality | Open the live link, click through the library, open a meeting, click transcript lines, drag the seek bar, search, create/edit/delete, refresh | Live demo down or empty; sync glitches at segment boundaries; CRUD lost on restart (ephemeral disk); summary stuck in "Processing" | Seeded data on startup; boundary unit tests (`start ≤ t < end`, gaps, t = 0, t = duration); persistence verified on the real host; processing fallback mode + Retry button; post-deploy smoke script |
| UI/UX | Compare side-by-side with Fireflies: sidebar, meeting rows, two-panel notepad, player bar, summary sections order, toasts | "Generic CRUD table" look; missing loading/empty/error states; janky auto-scroll fighting the user | UI spec derived from the Fireflies Notepad guide (section order Keywords → Overview → Notes → Outline → Action items); state matrix per screen; auto-scroll pause after manual scroll; polish phase with a checklist |
| Database Design | Read the models/migration and ER diagram; ask "why this table?", "what happens on delete?" | Free-text speaker strings; JSON blobs instead of tables; missing FKs/cascade; FKs silently off in SQLite | 3NF schema with M:N join, speaker FK, 1:1 summary, CHECK/UNIQUE constraints, `PRAGMA foreign_keys=ON` + tests proving cascades |
| Backend / API | Read `/docs`, try a 404 and an invalid payload, look at router/service/repository files | Fat routers with SQL; inconsistent status codes; stack traces leaked | Layering enforced; one error envelope; status-code tests; generic 500 |
| Code Quality | Skim files for size, naming, typing, dead code; look at CI | Huge generated files; inconsistent style; failing CI | ruff/eslint/prettier/tsc in CI; small focused modules; code review pass every phase |
| Code Modularity | Look for reusable components and pure logic separated from UI | Logic buried in components; copy-pasted fetch code | Hooks + pure functions; typed API client; strategy interfaces (parsers, providers, publishers, playback clock) |
| Code Understanding | Ask "why Kafka?", "walk me through clicking a line", "what if Kafka is down?" | Author can't defend generated architecture; over-engineering | Only two services; every decision has an ADR; DEVELOPMENT_GUIDE + INTERVIEW_GUIDE written as study material; demo script |

**Single biggest score risk:** the extras (Kafka, two services) are worth nothing if a MUST-have is broken.
Rule: no EXTRA/BONUS work is merged while any MUST row is red.
