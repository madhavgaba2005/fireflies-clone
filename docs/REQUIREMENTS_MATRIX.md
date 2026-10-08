# Requirements Matrix

Source of truth: *Meeting Notes & Transcription Platform (Fireflies.ai Clone) — SDE Fullstack Assignment* (PDF).
Every bullet in the PDF has a row below. Rows prefixed `X-` are **self-imposed engineering goals**
(Kafka, two services, CI…) — they are not in the PDF and must never displace a PDF requirement.

**Status legend:** ⬜ Planned · 🟨 In progress · ✅ Done (meets Definition of Done) · ⏸ Deferred · ❌ Dropped (with reason)

**Priority legend:** `MUST` (PDF core feature) · `MOCK` (placeholder allowed) · `BONUS` (optional) ·
`DELIV` (deliverable) · `CONSTR` (constraint / important note) · `EXTRA` (self-imposed)

Implementation paths refer to the planned structure in [ARCHITECTURE.md](ARCHITECTURE.md). `MS` = meeting-service, `AI` = ai-service, `FE` = frontend.

**Definition of Done for ✅:** implemented · integrated end-to-end · UI states (loading/empty/error) handled ·
persistence verified after reload · tests written and passing · docs/README/matrices updated · committed · CI green.
Code existing is **not** enough.

### Section map (assignment PDF → this file)
| PDF section | Matrix section |
|-------------|----------------|
| A. Core Features (Must Have) 1–5 | §1–§5 |
| B. Mocked / Placeholder Sections | §6 |
| C. Bonus (Optional) | §7 |
| F. Important Notes + Technical Stack | §8 |
| D. Deliverables + Submission | §9 |
| E. Evaluation Criteria | §10 (and [EVALUATION_MATRIX.md](EVALUATION_MATRIX.md)) |
| G. Timeline / constraints | §12 |
| Interpretations of ambiguous wording | §13 |

---

## 1. Meetings Library / Dashboard

| ID | Requirement (PDF wording) | Priority | Implementation | Test | Demo Verification | Status |
|----|---------------------------|----------|----------------|------|-------------------|--------|
| R1.1 | List of past meetings with **title, date, duration, participants** | MUST | MS `GET /api/meetings` → FE `app/meetings/page.tsx`, `components/meetings/MeetingList`, `MeetingRow` | MS integration: list returns fields; E2E: rows render seeded data | Open `/meetings`, see 6–8 seeded meetings with all 4 fields | ⬜ |
| R1.2 | **Search** meetings by title | MUST | MS query param `q` (title `LIKE`, case-insensitive) → FE `MeetingFilters` search box (debounced, URL-synced) | MS unit (repo filter) + integration; E2E type query → list narrows | Type "roadmap" → only matching meetings | ⬜ |
| R1.3 | **Filter** meetings by **date** | MUST | MS `date_from`, `date_to` params → FE date-range dropdown (Today / Last 7 days / Last 30 days / Custom) | MS integration (boundary dates inclusive); E2E select "Last 7 days" | Pick range → list narrows; count updates | ⬜ |
| R1.4 | **Filter** meetings by **participant** | MUST | MS `participant_id` param (join `meeting_participants`) → FE participant multi-select from `GET /api/participants` | MS integration; E2E choose participant | Choose "Priya Sharma" → only her meetings | ⬜ |
| R1.5 | **Sort by recency** | MUST | MS `sort=-meeting_date` (default) / `meeting_date`; FE sort toggle | MS integration asserts order; E2E toggles order | Newest first by default; toggle flips | ⬜ |
| R1.6 | **Navbar with profile/settings placeholders** | MUST | FE `components/layout/Sidebar`, `TopBar` (avatar menu → Profile / Settings), `app/settings/page.tsx` | E2E: navigate to Settings via avatar menu | Click avatar → Settings page with placeholder sections | ⬜ |

## 2. Meeting / Transcript Detail View

| ID | Requirement | Priority | Implementation | Test | Demo Verification | Status |
|----|-------------|----------|----------------|------|-------------------|--------|
| R2.1 | **Interactive transcript** with **speaker labels** and **timestamps** | MUST | MS `GET /api/meetings/{id}/transcript` → FE `TranscriptPanel`, `TranscriptLine` (avatar, speaker, `mm:ss`, text) | MS integration (ordered by `sequence`); E2E lines visible | Open a meeting; each line shows speaker + timestamp | ⬜ |
| R2.2 | **Media player area with seek bar** (placeholder or sample file) | MUST | FE `components/audio/AudioPlayer` (play/pause, seek bar, ±15 s, speed 1×–2×, time display) over a `usePlaybackClock` hook (`PlaybackClock` interface; `SimulatedClock` now, `<audio>` later) | Unit (hook logic via Playwright component/E2E); E2E drag/click seek bar | Play → time advances; drag seek bar → time jumps | ⬜ |
| R2.3 | **Clicking a transcript line seeks the player** to that timestamp | MUST | `TranscriptLine.onClick → player.seek(segment.start_ms)` | E2E: click line at 02:15 → player time 02:15 | Click any line → player jumps, starts playing | ⬜ |
| R2.4 | **…and vice versa** (player position highlights the active line) | MUST | `useActiveSegment(segments, currentMs)` (binary search) → active style + `scrollIntoView` (only if user isn't manually scrolling) | Unit test of `findActiveSegmentIndex`; E2E: seek bar → active line changes | Drag seek bar → highlighted line follows and auto-scrolls | ⬜ |
| R2.5 | **Search within the transcript** with **highlighted matches** | MUST | FE `TranscriptSearch` (case-insensitive, `<mark>` via safe text splitting, match count "3 of 12", ↑/↓ navigation) | Unit test of `splitByQuery` (incl. regex chars); E2E search highlights | Type "budget" → matches highlighted, count shown, Enter jumps to next | ⬜ |

## 3. AI Summary & Notes

| ID | Requirement | Priority | Implementation | Test | Demo Verification | Status |
|----|-------------|----------|----------------|------|-------------------|--------|
| R3.1 | **AI-generated meeting summary** section | MUST | AI `MockSummaryProvider` → event `summary.generated` → MS persists `summaries` → FE `SummaryPanel` (Overview) | AI unit tests; MS consumer test; E2E summary visible | Detail page shows Overview paragraph | ⬜ |
| R3.2 | **Action items / tasks extracted** from the meeting | MUST | AI extracts (heuristic: "I'll / we need to / can you / by Friday"…) → `action_items` (`source='ai'`) → FE `ActionItems` | AI unit tests on extraction; MS integration | Action items tab lists extracted tasks with assignee | ⬜ |
| R3.3 | **Key topics / outline / chapters** | MUST | AI groups segments into chapters → `summary_topics` (title, bullets, `start_ms`) → FE `Topics` outline; click chapter → seek | AI unit; E2E click chapter → player seeks | Outline shows timestamped chapters; click seeks | ⬜ |
| R3.4 | Summaries **seeded, mocked, or LLM-generated** from transcript text | MUST | Seed writes summaries directly; new meetings go through AI pipeline (`SummaryProvider` interface; Mock default, optional LLM) | AI provider contract test; seed test | New uploaded meeting gets a summary within seconds | ⬜ |

## 4. Meeting Management (CRUD)

| ID | Requirement | Priority | Implementation | Test | Demo Verification | Status |
|----|-------------|----------|----------------|------|-------------------|--------|
| R4.1 | **Create a meeting** by **uploading** a transcript | MUST | FE `CreateMeetingModal` → Upload tab (.txt / .vtt / .json) → MS `POST /api/meetings` (multipart) → `transcript_parsers/` | MS unit tests per parser (valid + malformed); integration; E2E upload fixture | Upload `sample.vtt` → new meeting opens, summary "Processing…" then appears | ⬜ |
| R4.2 | **Create** by **pasting** a transcript | MUST | Paste tab → same endpoint (JSON body `transcript_text`) | Parser unit; integration; E2E | Paste text → meeting created | ⬜ |
| R4.3 | **Create** via a **form** | MUST | Form tab: title, date, participants (no transcript → empty transcript state) | Integration; E2E | Meeting created with metadata only | ⬜ |
| R4.4 | **Edit meeting metadata** (title, participants) | MUST | `EditMeetingModal` → `PATCH /api/meetings/{id}` (title, meeting_date, participant list) | Validation unit; integration; E2E edit → reload → persisted | Rename meeting; add/remove participant; refresh → kept | ⬜ |
| R4.5 | **Delete a meeting** | MUST | Confirm dialog → `DELETE /api/meetings/{id}` (cascade transcript/summary/actions) → toast + redirect | Integration (children gone; 404 after); E2E | Delete → toast, gone from list after refresh | ⬜ |
| R4.6 | **Add** action items | MUST | `POST /api/meetings/{id}/action-items` → `ActionItemComposer` | Integration; E2E | Add task → appears, persists after refresh | ⬜ |
| R4.7 | **Edit** action items | MUST | Inline edit → `PATCH /api/action-items/{id}` (title, assignee, due date) | Integration; E2E | Edit text → persists | ⬜ |
| R4.8 | **Complete** action items | MUST | Checkbox → `PATCH {completed}` (optimistic update + rollback on error) | Integration (`completed_at` set/cleared); E2E | Tick → strikethrough, persists after refresh | ⬜ |
| R4.9 | **All meetings, transcripts, summaries, action items must persist** | MUST | SQLite file via SQLAlchemy; Alembic migrations; persistent volume in deployment | Integration tests across new sessions; E2E "reload and verify" in every CRUD spec | Do any CRUD → hard refresh → state preserved | ⬜ |

## 5. Fireflies Experience

| ID | Requirement | Priority | Implementation | Test | Demo Verification | Status |
|----|-------------|----------|----------------|------|-------------------|--------|
| R5.1 | **Navigation and layout** (library + detail view) resembling Fireflies | MUST | Left icon+label sidebar, top bar with global search + "Upload"/"New meeting" CTA; detail = two-panel workspace + bottom player bar ([UI_DESIGN_SPEC.md](UI_DESIGN_SPEC.md)) | E2E navigation; manual visual review vs reference | Side-by-side visual check | ⬜ |
| R5.2 | **Transcript and summary panels** | MUST | Left: summary/notes (Overview · Outline · Action items · Keywords); right: transcript | E2E | Both panels visible, independently scrollable | ⬜ |
| R5.3 | **Forms, modals, search, filters** | MUST | Radix Dialog-based modals (create, edit, confirm delete), filter dropdowns, search inputs | E2E covers each modal | All modals open/close (Esc, overlay click), focus trapped | ⬜ |
| R5.4 | **Notifications / toasts** | MUST | `sonner` toasts on every mutation success/failure + "Summary ready" notification | E2E asserts toast text | Create/delete/edit shows toast; API failure shows error toast | ⬜ |
| R5.5 | **Settings placeholders** | MUST | `app/settings` with Profile, Notifications, Integrations, Team tabs ("Coming soon") | E2E route loads | Settings page renders each tab | ⬜ |
| R5.6 | Feel like Fireflies **rather than a generic notes app** | MUST | Purple accent, dense list rows, speaker avatars/colours, AI sparkle labels, keyword chips, talk-time stats | Manual review checklist in UI spec | Evaluator impression | ⬜ |

## 6. Mocked / Placeholder Sections (a "Coming Soon" is sufficient)

| ID | Requirement | Priority | Implementation | Test | Demo Verification | Status |
|----|-------------|----------|----------------|------|-------------------|--------|
| M1 | Real-time bot that joins live calls | MOCK | "Add to live meeting" button → Coming Soon modal | E2E opens modal | Click → modal | ⬜ |
| M2 | Actual speech-to-text transcription | MOCK | Upload accepts transcripts only; audio upload tab shows Coming Soon | E2E | Audio tab says Coming Soon | ⬜ |
| M3 | Integrations (Zoom, Google Meet, calendar, CRM) | MOCK | Sidebar "Integrations" page with cards marked Coming Soon | E2E route loads | Page lists integrations | ⬜ |
| M4 | Team / sharing & collaboration | MOCK | "Share" button + sidebar "Team" → Coming Soon | E2E | Click → Coming Soon | ⬜ |
| M5 | Real user authentication (assume default logged-in user) | MOCK | Hardcoded default user in FE config (name/avatar); no auth on API (documented) | — (documented assumption) | Avatar shows default user | ⬜ |

## 7. Bonus (only after all MUST rows are ✅) — see [BONUS_FEATURES.md](BONUS_FEATURES.md)

| ID | Requirement | Priority | Implementation | Test | Demo Verification | Status |
|----|-------------|----------|----------------|------|-------------------|--------|
| B1 | Comments / highlights / soundbites on transcript segments | BONUS | `segment_comments` table, comment popover on line hover | Integration; E2E | Add comment on a line, persists | ⏸ |
| B2 | Export transcript or summary (PDF / Markdown / TXT) | BONUS | `GET /api/meetings/{id}/export?format=txt|md&content=transcript|summary` + Download modal (timestamps / speakers toggles, like Fireflies) | Unit (formatters); integration; E2E download | Download .md and .txt | ⬜ |
| B3 | Global search across all meetings | BONUS | `GET /api/search?q=` over titles + transcript text (SQLite FTS5) → results with snippet + jump to timestamp | Integration; E2E | Top-bar search finds phrase in any meeting, deep-links to timestamp | ⬜ |
| B4 | Tags / topics and filtering by them | BONUS | `tags` + `meeting_tags`; AI keywords become tags; dashboard tag filter | Integration; E2E | Filter by tag | ⬜ |
| B5 | LLM-powered "ask a question about this meeting" chat | BONUS | "AskFred"-style panel; `LLMProvider` if key present, else keyword-retrieval answer | Unit; manual | Ask question → answer with cited timestamps | ⏸ |
| B6 | Dark mode | BONUS | CSS variables + `class="dark"` toggle, persisted in localStorage | E2E toggle | Toggle → dark theme | ⬜ |

## 8. Technical Stack & Important Notes (constraints)

| ID | Requirement | Priority | Implementation | Test | Demo Verification | Status |
|----|-------------|----------|----------------|------|-------------------|--------|
| C1 | Frontend: **Next.js (TypeScript)** | CONSTR | `frontend/` Next.js 16 App Router, `strict: true` (Phase 2) | `npm run typecheck` + `npm run build` pass locally; in CI | `npm run dev` → placeholder routes | 🟨 scaffolded |
| C2 | Backend: **Python with FastAPI** | CONSTR | `backend/meeting-service`, `backend/ai-service` (app factories, health, error envelope — Phase 2) | 36 + 11 pytest tests pass | `/docs` OpenAPI page on :8000 / :8001 | 🟨 scaffolded |
| C3 | Database: **SQLite (design your own schema)** | CONSTR | `app/models/` (SQLAlchemy 2.0), Alembic `0001_initial_schema`, `app/database.py` | `test_schema.py`, `test_migrations.py` (migration ≡ models), `test_database.py` | Fresh DB migrates + seeds; integrity check ok | ✅ |
| C4 | Real audio transcription **out of scope**; may seed / upload .txt/.vtt/.json / optionally LLM | CONSTR | Parsers for .txt, .vtt, .json; Mock provider default | Parser unit tests | — | ⬜ |
| C5 | **UI should totally resemble Fireflies's design** — study it first | CONSTR | [UI_DESIGN_SPEC.md](UI_DESIGN_SPEC.md) written before UI phase | Manual review | — | ⬜ |
| C6 | **Seed several meetings** with full transcripts, summaries, action items | CONSTR | `app/seed/` — 7 meetings, 3–5 participants each, 183 segments, 34 chapters, 35 action items | `test_seed.py` (completeness, idempotency, shared people) | `python -m app.seed` → app populated | ✅ |
| C7 | **Database design will be evaluated** | CONSTR | 3NF schema, CHECK/UNIQUE/FK constraints, explicit ON DELETE, justified indexes, UTC type — [DATABASE_DESIGN.md](DATABASE_DESIGN.md) | `test_schema.py` proves each constraint fires | — | ✅ |
| C8 | **Original work** — plagiarism ⇒ disqualification | CONSTR | All code written from scratch; Fireflies used only as visual reference; no copied assets/logos | Review | — | ⬜ |
| C9 | Must understand every line (AI tools allowed) | CONSTR | [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md), [INTERVIEW_GUIDE.md](INTERVIEW_GUIDE.md), ADRs | — | Interview | ⬜ |

## 9. Deliverables & Submission

| ID | Requirement | Priority | Implementation | Test | Demo Verification | Status |
|----|-------------|----------|----------------|------|-------------------|--------|
| D1 | **Public GitHub repo** containing `frontend/` and `backend/` | DELIV | Monorepo root with both folders | — | Repo visible logged-out | ⬜ |
| D2 | README: **setup instructions** | DELIV | `README.md#local-setup` (Phase 2: native + docker compose) | Fresh-clone dry run following README verbatim | — | 🟨 |
| D3 | README: **tech stack** | DELIV | `README.md#tech-stack` | — | — | 🟨 |
| D4 | README: **architecture overview** | DELIV | `README.md#architecture` + [ARCHITECTURE.md](ARCHITECTURE.md) | — | — | 🟨 |
| D5 | README: **database schema** | DELIV | `README.md#database-schema` + [DATABASE_DESIGN.md](DATABASE_DESIGN.md) | — | — | 🟨 |
| D6 | README: **API overview** | DELIV | `README.md#api-overview` + [API.md](API.md) + `/docs` | — | — | 🟨 |
| D7 | README: **assumptions made** | DELIV | `README.md#assumptions` | — | — | 🟨 |
| D8 | **Hosted, working demo link** | DELIV | See [DEPLOYMENT.md](DEPLOYMENT.md) (target pending decision) | Smoke test script against deployed URL | Link opens populated app; CRUD persists | ⬜ |
| D9 | Submit repo link + deployed link | DELIV | Final checklist in `FINAL_EVALUATION_REPORT.md` | — | — | ⬜ |

## 10. Evaluation Criteria (exact PDF wording — no numeric weights are given, none are invented)

| ID | Criterion | What the PDF says they look for | Evidence plan |
|----|-----------|---------------------------------|---------------|
| E1 | Functionality | All core features working correctly, **including the interactive transcript and summary views** | [EVALUATION_MATRIX §1](EVALUATION_MATRIX.md#1-functionality) |
| E2 | UI/UX | Visual similarity to the original app's design and UX patterns | [§2](EVALUATION_MATRIX.md#2-uiux) |
| E3 | Database Design | Well-structured schema with proper relationships | [§3](EVALUATION_MATRIX.md#3-database-design) |
| E4 | Backend / API Design | Clean, sensible API design and architecture | [§4](EVALUATION_MATRIX.md#4-backend--api-design) |
| E5 | Code Quality | Clean, readable, and well-organized code | [§5](EVALUATION_MATRIX.md#5-code-quality) |
| E6 | Code Modularity | Proper separation of concerns, reusable components | [§6](EVALUATION_MATRIX.md#6-code-modularity) |
| E7 | Code Understanding | Ability to explain your code during evaluation | [§7](EVALUATION_MATRIX.md#7-code-understanding) |

## 11. Self-imposed engineering goals (not in the PDF)

| ID | Goal | Priority | Implementation | Test | Verification | Status |
|----|------|----------|----------------|------|--------------|--------|
| X1 | Two services: Meeting Service (system of record) + stateless AI Processing Service | EXTRA | `backend/meeting-service`, `backend/ai-service` | Each service has its own test suite | docker compose up | ⬜ |
| X2 | Kafka for async processing only (never CRUD) | EXTRA | Topics `meeting.events`, `ai.events`; transactional outbox; idempotent consumers | Kafka integration test in CI (service container) | Upload → summary arrives via Kafka | ⬜ |
| X2a | Visible processing state `not_requested → pending → processing → completed / failed` | EXTRA (supports R3.4) | `meetings.processing_status`; FE `SummaryStatus` ("Generating notes…" / Ready / Failed + Retry) | Service unit (state transitions); integration; E2E | New meeting shows Processing… then Ready | ⬜ |
| X2b | `PROCESSING_MODE=kafka\|http\|inline-test` — free-hosting fallback reusing the same envelope, processor and idempotent apply path | EXTRA (supports D8) | `EventPublisher` implementations in MS; AI `POST /internal/process` | Tests run the pipeline through `InMemoryEventPublisher`; HTTP mode integration test | Deployed demo generates summaries even without a broker | ⬜ |
| X3 | Backend coverage ~90%+ (where practical) | EXTRA | pytest-cov, `--cov-fail-under` | CI gate | Coverage badge/report | ⬜ |
| X4 | Playwright E2E for critical flows | EXTRA | `frontend/tests/e2e` | CI job | — | ⬜ |
| X5 | GitHub Actions CI on PR + push to main | EXTRA | `.github/workflows/ci.yml` (Phase 2: backend lint/format/types/tests+coverage, contract check, Kafka job, frontend lint/format/types/unit/build/E2E smoke) | Every step run locally; first CI run happens when the GitHub repo exists | Green checks on PRs | 🟨 written, not yet run on GitHub |
| X6 | Professional Git workflow: issues → branches → PRs | EXTRA | [PROJECT_PLAN.md](PROJECT_PLAN.md) | — | GitHub history | ⬜ |
| X7 | Loading / empty / error states on every screen | EXTRA (supports R5) | Shared `ui/EmptyState`, `ui/ErrorState`, skeletons | E2E with mocked API failure | — | ⬜ |
| X8 | Security basics: validation, CORS, env config, no secrets, safe rendering of uploads | EXTRA | Done in Phase 2: env-based config + `.env.example` only, CORS allow-list, generic 500s, non-root Docker users. Later: Pydantic limits, upload checks, React escaping | `test_config.py`, `test_health.py` (CORS), `test_errors.py` (no internals leaked) | — | 🟨 |

## 12. Timeline & constraints (PDF "Timeline", "AI Tools Usage")

| ID | Constraint | Consequence for this project |
|----|-----------|------------------------------|
| G1 | Estimated effort ≈ **24 hours** | Must-haves first; Kafka/CI/extra docs are budgeted on top and are the first thing cut if time runs short (never a MUST row) |
| G2 | Submission deadline "as communicated" | Deployment (Phase 18) must be stable **before** the deadline, not on it — the hosted link is a deliverable |
| G3 | AI tools allowed, but **every line must be understood** | DEVELOPMENT_GUIDE, ADRs, INTERVIEW_GUIDE; small architecture; no unexplained generated code |
| G4 | Plagiarism ⇒ disqualification | No Fireflies-clone repos consulted; Fireflies only as a visual/UX reference; original name & logo |

## 13. Interpretations of ambiguous wording (decided, documented, revisitable)

| # | PDF wording | Our interpretation | Why |
|---|------------|--------------------|-----|
| I1 | Description: "search across transcripts" | Must-have = library search (title/date/participant) + in-transcript search. Cross-meeting transcript search = Bonus B3 (**first** bonus to build) | The Core Features list scopes search to the library and to "within the transcript"; the Bonus list explicitly names "Global search across all meetings" |
| I2 | "seeks the player to that timestamp (and vice versa)" | Vice versa = player position drives the active transcript line (highlight + auto-scroll), including when the user drags the seek bar | The only meaningful inverse of "line → player" |
| I3 | "audio/video can be a placeholder or a sample file" | A simulated playback clock with real controls (play/pause, seek bar, ±15 s, speed); a real `<audio>` source can be plugged in behind the same `PlaybackClock` interface | Sync behaviour is fully real; no fake media to generate |
| I4 | "Navbar with profile/settings placeholders" | Fireflies uses a left sidebar + top bar; we provide both (Settings in sidebar, avatar menu in top bar) | Matches both the PDF wording and the reference UI |
| I5 | "Create a meeting (by uploading or pasting a transcript, **or** via a form)" | We implement all three | Cheap once the parser exists; removes any doubt |
| I6 | "Add / edit / complete action items" (delete not listed) | Also implement delete and uncomplete | Expected CRUD; trivial; avoids a UX dead end |
| I7 | "Edit meeting metadata (title, participants)" | Title, participants **and** meeting date | Date is metadata; needed for date-filter demos |
| I8 | "Real user authentication (assume a default logged-in user)" | Hard-coded default user shown in the top bar; API has no auth | Explicitly allowed |
