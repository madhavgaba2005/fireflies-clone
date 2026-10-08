# Evaluation Matrix

Maps each of the PDF's seven evaluation criteria to **concrete, checkable evidence** in this repository.
An evaluator should be able to verify every "Evidence" cell in under a minute.
Status uses the same legend as [REQUIREMENTS_MATRIX.md](REQUIREMENTS_MATRIX.md).

---

## 1. Functionality — "All core features working correctly, including the interactive transcript and summary views"

| Evidence | Where | Req IDs | Status |
|----------|-------|---------|--------|
| Dashboard lists seeded meetings with title, date, duration, participants | `/meetings` | R1.1 | ⬜ |
| Title search, date-range filter, participant filter, sort toggle (combinable, URL-synced so refresh keeps them) | `/meetings?q=…&participant=…` | R1.2–R1.5 | ⬜ |
| Transcript with speaker + timestamp per line | `/meetings/{id}` right panel | R2.1 | ⬜ |
| Player with seek bar, speed, ±15 s | bottom player bar | R2.2 | ⬜ |
| Click line → player seeks; playback → active line highlighted + auto-scrolled | detail page | R2.3, R2.4 | ⬜ |
| In-transcript search with highlights, "n of m", next/prev | transcript search box | R2.5 | ⬜ |
| Overview, outline/chapters (timestamped, clickable), action items | left panel | R3.1–R3.3 | ⬜ |
| New meeting → async AI summary appears without reload ("Processing…" → ready toast) | create flow | R3.4, X2 | ⬜ |
| Create (upload / paste / form), edit, delete meetings | modals | R4.1–R4.5 | ⬜ |
| Add / edit / complete / delete action items | action items tab | R4.6–R4.8 | ⬜ |
| Everything survives a hard refresh and a server restart | any | R4.9 | ⬜ |
| **Proof:** Playwright suite exercises every row above against a real backend | `frontend/tests/e2e/` | all | ⬜ |

## 2. UI/UX — "Visual similarity to the original app's design and UX patterns"

| Evidence | Where | Status |
|----------|-------|--------|
| Written design spec derived from studying Fireflies before coding UI | [UI_DESIGN_SPEC.md](UI_DESIGN_SPEC.md) | 🟨 |
| Fireflies-style collapsible left sidebar, top search bar, purple primary CTA | `components/layout/` | ⬜ |
| Two-panel meeting workspace (summary left, transcript right) + bottom player bar | `app/meetings/[id]` | ⬜ |
| Speaker avatars with consistent per-speaker colours, talk-time bar | `TranscriptLine`, `SpeakerStats` | ⬜ |
| Loading skeletons, empty states (no meetings / no matches / no action items), error states with retry, 404 page | `components/ui/` | ⬜ |
| Toasts for every mutation; "Coming soon" modals for out-of-scope features | `sonner` | ⬜ |
| Keyboard: `/` focuses search, `Space` play/pause, `Esc` closes modals, Enter/Shift+Enter next/prev match | hooks | ⬜ |
| Responsive: panels stack < 1024 px; sidebar collapses to icons/drawer | CSS breakpoints | ⬜ |
| Dark mode (bonus) | theme toggle | ⬜ |
| Screenshots in README side-by-side with intent | `README.md#screenshots` | ⬜ |

## 3. Database Design — "Well-structured schema with proper relationships"

| Evidence | Where | Status |
|----------|-------|--------|
| ER diagram + per-table rationale + normalization argument (3NF) | [DATABASE_DESIGN.md](DATABASE_DESIGN.md) | 🟨 |
| Many-to-many `meetings ↔ participants` through `meeting_participants` (composite PK) | `models/` | ⬜ |
| Speakers are FKs to `participants` (no repeated name strings per line) | `transcript_segments.speaker_id` | ⬜ |
| One-to-one `meetings → summaries` enforced by `UNIQUE(meeting_id)` | `summaries` | ⬜ |
| Integer-millisecond timestamps with `CHECK (end_ms >= start_ms AND start_ms >= 0)` | `transcript_segments` | ⬜ |
| `UNIQUE(meeting_id, sequence)` ordering guarantees; justified indexes only | migrations | ⬜ |
| Explicit `ON DELETE` behaviour (CASCADE for owned children, SET NULL for assignee) and `PRAGMA foreign_keys=ON` | `database.py` | ⬜ |
| Idempotency table (`processed_events`) + transactional outbox (`outbox_events`) | schema | ⬜ |
| Alembic migrations — fresh install reproducible with one command | `alembic/` | ⬜ |
| Tests proving constraints (cascade, unique, check) actually fire | `tests/test_schema.py` | ⬜ |

## 4. Backend / API Design — "Clean, sensible API design and architecture"

| Evidence | Where | Status |
|----------|-------|--------|
| RESTful resource design, nested only where ownership is real | [API.md](API.md) | 🟨 |
| Router → Service → Repository layering; routers contain no SQL, repositories contain no HTTP | `app/routers`, `app/services`, `app/repositories` | ⬜ |
| Pydantic request/response schemas with field limits; `422` on bad input | `app/schemas` | ⬜ |
| Uniform error envelope `{ "error": { "code", "message", "details" } }` | exception handlers | ⬜ |
| Correct status codes: 200/201/204/400/404/409/413/415/422 | tests | ⬜ |
| Pagination (`limit`/`offset` + `total`) on list endpoint | `GET /api/meetings` | ⬜ |
| Auto-generated OpenAPI at `/docs` | FastAPI | ⬜ |
| Async processing via Kafka with outbox + idempotent consumer; CRUD stays synchronous | [EVENT_DRIVEN_ARCHITECTURE.md](EVENT_DRIVEN_ARCHITECTURE.md) | 🟨 |
| Health endpoints `/health` (liveness) and `/health/ready` (DB + broker) | both services | ⬜ |
| Environment-based config (`pydantic-settings`), `.env.example` | `config.py` | ⬜ |

## 5. Code Quality — "Clean, readable, and well-organized code"

| Evidence | Where | Status |
|----------|-------|--------|
| `ruff` lint + format (backend), `eslint` + `prettier` + `tsc --strict` (frontend) enforced in CI | `.github/workflows/ci.yml` | ⬜ |
| Typed everywhere: Python type hints + `mypy` on services; shared TS types mirroring API schemas | — | ⬜ |
| Backend coverage report with threshold gate | `pytest --cov` | ⬜ |
| No dead code, no magic numbers (named constants), no secrets in repo | review | ⬜ |
| Conventional commits, small PRs linked to issues | Git history | ⬜ |

## 6. Code Modularity — "Proper separation of concerns, reusable components"

| Evidence | Where | Status |
|----------|-------|--------|
| Two independently runnable/testable services with a single documented contract (event schemas) | `backend/*` | ⬜ |
| `SummaryProvider` interface with `MockSummaryProvider` (default) and optional `LLMSummaryProvider` | `ai-service/app/providers` | ⬜ |
| Transcript parsers as pluggable strategy per format (`txt`, `vtt`, `json`) | `meeting-service/app/services/transcript_parsers` | ⬜ |
| `EventBus` interface: Kafka implementation + in-memory implementation for tests | `app/events` | ⬜ |
| Reusable FE components: `AudioPlayer`, `TranscriptPanel`, `TranscriptLine`, `TranscriptSearch`, `SummaryPanel`, `Topics`, `ActionItems`, `Modal`, `EmptyState` | `frontend/components` | ⬜ |
| Logic in hooks / pure functions (`useMediaClock`, `useActiveSegment`, `splitByQuery`) — unit-testable, not buried in JSX | `frontend/hooks`, `frontend/lib` | ⬜ |

## 7. Code Understanding — "Ability to explain your code during evaluation"

| Evidence | Where | Status |
|----------|-------|--------|
| Architecture doc with request, event and failure flows | [ARCHITECTURE.md](ARCHITECTURE.md) | 🟨 |
| ADRs: context / decision / alternatives / consequences for each major choice | [adr/](adr/) | 🟨 |
| Development guide covering every technology & pattern, with "how to explain it" | [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) | 🟨 |
| Interview guide: 30-second / detailed / trade-off answers + follow-ups | [INTERVIEW_GUIDE.md](INTERVIEW_GUIDE.md) | ⬜ |
| Deliberately small architecture — every moving part justified, nothing decorative | [TRADEOFFS.md](TRADEOFFS.md) | 🟨 |
