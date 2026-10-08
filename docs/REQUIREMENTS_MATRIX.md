# Requirements Matrix

Source of truth: *Meeting Notes & Transcription Platform (Fireflies.ai Clone) — SDE Fullstack Assignment* (PDF).
Every bullet in the PDF has a row below. Rows prefixed `X-` are **self-imposed engineering goals**
(Kafka, two services, CI…) — they are not in the PDF and must never displace a PDF requirement.

**Status legend:** ⬜ Planned · 🟨 In progress · ✅ VERIFIED (meets the Definition of Done, backed by passing tests) · ⏳ Ready, waiting on the author · ⏸ Deferred · ❌ Dropped (with reason)

**Priority legend:** `MUST` (PDF core feature) · `MOCK` (placeholder allowed) · `BONUS` (optional) ·
`DELIV` (deliverable) · `CONSTR` (constraint / important note) · `EXTRA` (self-imposed)

Implementation paths refer to the planned structure in [ARCHITECTURE.md](ARCHITECTURE.md). `MS` = meeting-service, `AI` = ai-service, `FE` = frontend.

**Definition of Done for ✅:** implemented · integrated end-to-end · UI states (loading/empty/error) handled ·
persistence verified after reload · tests written and passing · docs/README/matrices updated · committed · CI checks
pass locally (the first GitHub Actions run happens when the repository is published).
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
| R1.1 | List of past meetings with **title, date, duration, participants** | MUST | MS `GET /api/meetings` → FE `app/meetings/page.tsx`, `components/meetings/MeetingList`, `MeetingRow` | MS integration: list returns fields; E2E: rows render seeded data | Open `/meetings`, see 6–8 seeded meetings with all 4 fields | ✅ VERIFIED — API + UI + E2E |
| R1.2 | **Search** meetings by title | MUST | MS query param `q` (title `LIKE`, case-insensitive) → FE `MeetingFilters` search box (debounced, URL-synced) | MS unit (repo filter) + integration; E2E type query → list narrows | Type "roadmap" → only matching meetings | ✅ VERIFIED — debounced, URL-synced; API + E2E |
| R1.3 | **Filter** meetings by **date** | MUST | MS `date_from`, `date_to` params → FE date-range dropdown (Today / Last 7 days / Last 30 days / Custom) | MS integration (boundary dates inclusive); E2E select "Last 7 days" | Pick range → list narrows; count updates | ✅ VERIFIED — presets + custom range; API + E2E |
| R1.4 | **Filter** meetings by **participant** | MUST | MS `participant_id` param (join `meeting_participants`) → FE participant multi-select from `GET /api/participants` | MS integration; E2E choose participant | Choose "Priya Sharma" → only her meetings | ✅ VERIFIED — multi-select popover; API + E2E |
| R1.5 | **Sort by recency** | MUST | MS `sort=-meeting_date` (default) / `meeting_date`; FE sort toggle | MS integration asserts order; E2E toggles order | Newest first by default; toggle flips | ✅ VERIFIED — newest/oldest toggle; API + E2E |
| R1.6 | **Navbar with profile/settings placeholders** | MUST | FE `components/layout/Sidebar`, `TopBar` (avatar menu → Profile / Settings), `app/settings/page.tsx` | E2E: navigate to Settings via avatar menu | Click avatar → Settings page with placeholder sections | ✅ VERIFIED — sidebar + top bar + avatar menu + /settings; E2E |

## 2. Meeting / Transcript Detail View

| ID | Requirement | Priority | Implementation | Test | Demo Verification | Status |
|----|-------------|----------|----------------|------|-------------------|--------|
| R2.1 | **Interactive transcript** with **speaker labels** and **timestamps** | MUST | MS `GET /api/meetings/{id}/transcript` → FE `TranscriptPanel`, `TranscriptLine` (avatar, speaker, `mm:ss`, text) | MS integration (ordered by `sequence`); E2E lines visible | Open a meeting; each line shows speaker + timestamp | ✅ VERIFIED — API + E2E |
| R2.2 | **Media player area with seek bar** (placeholder or sample file) | MUST | FE `components/audio/AudioPlayer` (play/pause, seek bar, ±15 s, speed 1×–2×, time display) over a `usePlaybackClock` hook (`PlaybackClock` interface; `SimulatedClock` now, `<audio>` later) | Unit (hook logic via Playwright component/E2E); E2E drag/click seek bar | Play → time advances; drag seek bar → time jumps | ✅ VERIFIED — simulated clock (13 unit tests) + E2E |
| R2.3 | **Clicking a transcript line seeks the player** to that timestamp | MUST | `TranscriptLine.onClick → player.seek(segment.start_ms)` | E2E: click line at 02:15 → player time 02:15 | Click any line → player jumps, starts playing | ✅ VERIFIED — lines, chapters and action-item timestamps seek + play; E2E |
| R2.4 | **…and vice versa** (player position highlights the active line) | MUST | `useActiveSegment(segments, currentMs)` (binary search) → active style + `scrollIntoView` (only if user isn't manually scrolling) | Unit test of `findActiveSegmentIndex`; E2E: seek bar → active line changes | Drag seek bar → highlighted line follows and auto-scrolls | ✅ VERIFIED — binary search (unit) + highlight/scroll on play and seek; E2E incl. exact-boundary and paused-seek E2E |
| R2.5 | **Search within the transcript** with **highlighted matches** | MUST | FE `TranscriptSearch` (case-insensitive, `<mark>` via safe text splitting, match count "3 of 12", ↑/↓ navigation) | Unit test of `splitByQuery` (incl. regex chars); E2E search highlights | Type "budget" → matches highlighted, count shown, Enter jumps to next | ✅ VERIFIED — highlights, n/m counter, ↑/↓, Enter/Shift+Enter; unit + E2E |

## 3. AI Summary & Notes

| ID | Requirement | Priority | Implementation | Test | Demo Verification | Status |
|----|-------------|----------|----------------|------|-------------------|--------|
| R3.1 | **AI-generated meeting summary** section | MUST | AI `MockSummaryProvider` → event `summary.generated` → MS persists `summaries` → FE `SummaryPanel` (Overview) | AI unit tests; MS consumer test; E2E summary visible | Detail page shows Overview paragraph | ✅ VERIFIED — seeded + generated; E2E shows async completion |
| R3.2 | **Action items / tasks extracted** from the meeting | MUST | AI extracts (heuristic: "I'll / we need to / can you / by Friday"…) → `action_items` (`source='ai'`) → FE `ActionItems` | AI unit tests on extraction; MS integration | Action items tab lists extracted tasks with assignee | ✅ VERIFIED — grouped by assignee in UI; unit + API + E2E |
| R3.3 | **Key topics / outline / chapters** | MUST | AI groups segments into chapters → `summary_topics` (title, bullets, `start_ms`) → FE `Topics` outline; click chapter → seek | AI unit; E2E click chapter → player seeks | Outline shows timestamped chapters; click seeks | ✅ VERIFIED — timestamped, clickable outline; E2E |
| R3.4 | Summaries **seeded, mocked, or LLM-generated** from transcript text | MUST | Seed writes summaries directly; new meetings go through AI pipeline (`SummaryProvider` interface; Mock default, optional LLM) | AI provider contract test; seed test | New uploaded meeting gets a summary within seconds | ✅ VERIFIED — seeded + mock provider through Kafka (real broker test) and HTTP fallback (E2E) |

## 4. Meeting Management (CRUD)

| ID | Requirement | Priority | Implementation | Test | Demo Verification | Status |
|----|-------------|----------|----------------|------|-------------------|--------|
| R4.1 | **Create a meeting** by **uploading** a transcript | MUST | FE `CreateMeetingModal` → Upload tab (.txt / .vtt / .json) → MS `POST /api/meetings` (multipart) → `transcript_parsers/` | MS unit tests per parser (valid + malformed); integration; E2E upload fixture | Upload `sample.vtt` → new meeting opens, summary "Processing…" then appears | ✅ VERIFIED — .txt/.vtt/.json upload; E2E with sample file |
| R4.2 | **Create** by **pasting** a transcript | MUST | Paste tab → same endpoint (JSON body `transcript_text`) | Parser unit; integration; E2E | Paste text → meeting created | ✅ VERIFIED — E2E |
| R4.3 | **Create** via a **form** | MUST | Form tab: title, date, participants (no transcript → empty transcript state) | Integration; E2E | Meeting created with metadata only | ✅ VERIFIED — E2E |
| R4.4 | **Edit meeting metadata** (title, participants) | MUST | `EditMeetingModal` → `PATCH /api/meetings/{id}` (title, meeting_date, participant list) | Validation unit; integration; E2E edit → reload → persisted | Rename meeting; add/remove participant; refresh → kept | ✅ VERIFIED — E2E incl. reload |
| R4.5 | **Delete a meeting** | MUST | Confirm dialog → `DELETE /api/meetings/{id}` (cascade transcript/summary/actions) → toast + redirect | Integration (children gone; 404 after); E2E | Delete → toast, gone from list after refresh | ✅ VERIFIED — from library and workspace; E2E incl. reload |
| R4.6 | **Add** action items | MUST | `POST /api/meetings/{id}/action-items` → `ActionItemComposer` | Integration; E2E | Add task → appears, persists after refresh | ✅ VERIFIED — E2E |
| R4.7 | **Edit** action items | MUST | Inline edit → `PATCH /api/action-items/{id}` (title, assignee, due date) | Integration; E2E | Edit text → persists | ✅ VERIFIED — inline editor; E2E |
| R4.8 | **Complete** action items | MUST | Checkbox → `PATCH {completed}` (optimistic update + rollback on error) | Integration (`completed_at` set/cleared); E2E | Tick → strikethrough, persists after refresh | ✅ VERIFIED — optimistic, rollback on error; E2E incl. reload |
| R4.9 | **All meetings, transcripts, summaries, action items must persist** | MUST | SQLite file via SQLAlchemy; Alembic migrations; persistent volume in deployment | Integration tests across new sessions; E2E "reload and verify" in every CRUD spec | Do any CRUD → hard refresh → state preserved | ✅ VERIFIED — fresh-session test, E2E reloads, Docker restart check |

## 5. Fireflies Experience

| ID | Requirement | Priority | Implementation | Test | Demo Verification | Status |
|----|-------------|----------|----------------|------|-------------------|--------|
| R5.1 | **Navigation and layout** (library + detail view) resembling Fireflies | MUST | Left icon+label sidebar, top bar with global search + "Upload"/"New meeting" CTA; detail = two-panel workspace + bottom player bar ([UI_DESIGN_SPEC.md](UI_DESIGN_SPEC.md)) | E2E navigation; manual visual review vs reference | Side-by-side visual check | ✅ VERIFIED — E2E + screenshots |
| R5.2 | **Transcript and summary panels** | MUST | Left: summary/notes (Overview · Outline · Action items · Keywords); right: transcript | E2E | Both panels visible, independently scrollable | ✅ VERIFIED — E2E |
| R5.3 | **Forms, modals, search, filters** | MUST | Radix Dialog-based modals (create, edit, confirm delete), filter dropdowns, search inputs | E2E covers each modal | All modals open/close (Esc, overlay click), focus trapped | ✅ VERIFIED — Radix dialogs/menus/popovers; E2E |
| R5.4 | **Notifications / toasts** | MUST | `sonner` toasts on every mutation success/failure + "Summary ready" notification | E2E asserts toast text | Create/delete/edit shows toast; API failure shows error toast | ✅ VERIFIED — sonner toasts on every mutation and failure; E2E |
| R5.5 | **Settings placeholders** | MUST | `app/settings` with Profile, Notifications, Integrations, Team tabs ("Coming soon") | E2E route loads | Settings page renders each tab | ✅ VERIFIED — Profile / Notifications / Integrations / Team tabs; E2E (+ Appearance: System / Light / Dark) |
| R5.6 | Feel like Fireflies **rather than a generic notes app** | MUST | Purple accent, dense list rows, speaker avatars/colours, AI sparkle labels, keyword chips, talk-time stats | Manual review checklist in UI spec | Evaluator impression | ✅ VERIFIED — visual review against the Fireflies Notepad guide (screenshots in README); two visual QA passes recorded in [UI_FIDELITY_AUDIT.md](UI_FIDELITY_AUDIT.md) |

## 6. Mocked / Placeholder Sections (a "Coming Soon" is sufficient)

| ID | Requirement | Priority | Implementation | Test | Demo Verification | Status |
|----|-------------|----------|----------------|------|-------------------|--------|
| M1 | Real-time bot that joins live calls | MOCK | "Add to live meeting" button → Coming Soon modal | E2E opens modal | Click → modal | ✅ 'Add to live meeting' + sidebar card → Coming soon dialog; E2E |
| M2 | Actual speech-to-text transcription | MOCK | Upload accepts transcripts only; audio upload tab shows Coming Soon | E2E | Audio tab says Coming Soon | ✅ transcripts only; audio not accepted; documented |
| M3 | Integrations (Zoom, Google Meet, calendar, CRM) | MOCK | Sidebar "Integrations" page with cards marked Coming Soon | E2E route loads | Page lists integrations | ✅ Integrations sidebar item + settings tab (Coming soon); E2E |
| M4 | Team / sharing & collaboration | MOCK | "Share" button + sidebar "Team" → Coming Soon | E2E | Click → Coming Soon | ✅ Share button + Team item → Coming soon |
| M5 | Real user authentication (assume default logged-in user) | MOCK | Hardcoded default user in FE config (name/avatar); no auth on API (documented) | — (documented assumption) | Avatar shows default user | ✅ default user 'Alex Morgan' in top bar/profile; API has no auth (documented) |

## 7. Bonus (only after all MUST rows are ✅) — see [BONUS_FEATURES.md](BONUS_FEATURES.md)

| ID | Requirement | Priority | Implementation | Test | Demo Verification | Status |
|----|-------------|----------|----------------|------|-------------------|--------|
| B1 | Comments / highlights / soundbites on transcript segments | BONUS | `segment_comments` table, comment popover on line hover | Integration; E2E | Add comment on a line, persists | ⏸ |
| B2 | Export transcript or summary (PDF / Markdown / TXT) | BONUS | Client-side formatters in `lib/export.ts` (no endpoint needed: the data is already loaded) + Download dialog in the ⋯ menu with timestamps / speakers toggles. PDF not offered | `lib/export.test.ts`; E2E `export.spec.ts` checks the downloaded files | ⋯ → Download → .txt / .md | ✅ TXT + Markdown |
| B3 | Global search across all meetings | BONUS | `GET /api/search?q=` (escaped LIKE over titles + transcript lines, grouped per meeting, snippets) → top-bar combobox → deep link `?t=…&find=…` | `test_search_api.py` (12); E2E `global-search.spec.ts` | Top-bar search finds a phrase in any meeting, deep-links to the moment | ✅ |
| B4 | Tags / topics and filtering by them | BONUS | AI keywords (`summary_keywords`) are the tags; `GET /api/meetings?keyword=`; chips on rows and notes filter the library | `test_filter_by_keyword_tag`; E2E keyword-chip test | Click a chip → filtered library | ✅ |
| B5 | LLM-powered "ask a question about this meeting" chat | BONUS | "AskFred"-style panel; `LLMProvider` if key present, else keyword-retrieval answer | Unit; manual | Ask question → answer with cited timestamps | ⏸ |
| B6 | Dark mode | BONUS | Dark token values under `.dark`; account-menu toggle; localStorage + `prefers-color-scheme` default; pre-paint script | `lib/theme.test.ts`; E2E `dark-mode.spec.ts` | Toggle → dark theme, survives reload | ✅ |

## 8. Technical Stack & Important Notes (constraints)

| ID | Requirement | Priority | Implementation | Test | Demo Verification | Status |
|----|-------------|----------|----------------|------|-------------------|--------|
| C1 | Frontend: **Next.js (TypeScript)** | CONSTR | `frontend/` Next.js 16 App Router, React 19, `strict: true` | `npm run typecheck` + `npm run build`; 74 Vitest + 39 Playwright tests | Every screen | ✅ |
| C2 | Backend: **Python with FastAPI** | CONSTR | `backend/meeting-service`, `backend/ai-service` (app factories, router → service → repository, one error envelope) | 183 + 39 pytest tests | `/docs` OpenAPI page | ✅ |
| C3 | Database: **SQLite (design your own schema)** | CONSTR | `app/models/` (SQLAlchemy 2.0), Alembic `0001_initial_schema`, `app/database.py` | `test_schema.py`, `test_migrations.py` (migration ≡ models), `test_database.py` | Fresh DB migrates + seeds; integrity check ok | ✅ |
| C4 | Real audio transcription **out of scope**; may seed / upload .txt/.vtt/.json / optionally LLM | CONSTR | Upload or paste .txt/.vtt/.json (`transcript_parser.py`); seeded meetings; deterministic mock AI provider | Parser unit tests; E2E upload | Create a meeting from a sample file in `samples/` | ✅ |
| C5 | **UI should totally resemble Fireflies's design** — study it first | CONSTR | [UI_DESIGN_SPEC.md](UI_DESIGN_SPEC.md) written before any UI; fidelity checklist §9 | Screenshot review (README) | All screens | ✅ (subjective; one checklist item open — see UI_DESIGN_SPEC §9) |
| C6 | **Seed several meetings** with full transcripts, summaries, action items | CONSTR | `app/seed/` — 7 meetings, 3–5 participants each, 183 segments, 34 chapters, 35 action items | `test_seed.py` (completeness, idempotency, shared people) | `python -m app.seed` → app populated | ✅ |
| C7 | **Database design will be evaluated** | CONSTR | 3NF schema, CHECK/UNIQUE/FK constraints, explicit ON DELETE, justified indexes, UTC type — [DATABASE_DESIGN.md](DATABASE_DESIGN.md) | `test_schema.py` proves each constraint fires | — | ✅ |
| C8 | **Original work** — plagiarism ⇒ disqualification | CONSTR | Written from scratch; no Fireflies-clone repositories consulted; Fireflies used only as a visual reference; own name ("Lumen") and logo | Review | — | ✅ |
| C9 | Must understand every line (AI tools allowed) | CONSTR | [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md), [INTERVIEW_GUIDE.md](INTERVIEW_GUIDE.md), ADRs, small and layered code | — | Interview | ✅ docs complete; the interview itself is the test |

## 9. Deliverables & Submission

| ID | Requirement | Priority | Implementation | Test | Demo Verification | Status |
|----|-------------|----------|----------------|------|-------------------|--------|
| D1 | **Public GitHub repo** containing `frontend/` and `backend/` | DELIV | Monorepo with both folders; local history of issue branches + merges ready to push | — | Repo visible logged-out | ⏳ ready; publishing needs the author's authorization |
| D2 | README: **setup instructions** | DELIV | `README.md#local-setup` (Phase 2: native + docker compose) | Fresh-clone dry run following README verbatim | — | ✅ README section: Local Setup (native + docker compose) |
| D3 | README: **tech stack** | DELIV | `README.md#tech-stack` | — | — | ✅ README section: Tech Stack |
| D4 | README: **architecture overview** | DELIV | `README.md#architecture` + [ARCHITECTURE.md](ARCHITECTURE.md) | — | — | ✅ README section: Architecture + diagram, Services, Kafka / Event Flow |
| D5 | README: **database schema** | DELIV | `README.md#database-schema` + [DATABASE_DESIGN.md](DATABASE_DESIGN.md) | — | — | ✅ README section: Database Schema + DATABASE_DESIGN.md |
| D6 | README: **API overview** | DELIV | `README.md#api-overview` + [API.md](API.md) + `/docs` | — | — | ✅ README section: API Overview + API.md + `/docs` |
| D7 | README: **assumptions made** | DELIV | `README.md#assumptions` | — | — | ✅ README section: Assumptions |
| D8 | **Hosted, working demo link** | DELIV | `deploy/docker-compose.prod.yml` (Caddy + real Kafka) — verified locally incl. restart persistence; [DEPLOYMENT.md](DEPLOYMENT.md) | Post-deploy checklist (DEPLOYMENT §5) | Link opens populated app; CRUD persists | ⏳ ready; host choice needs the author |
| D9 | Submit repo link + deployed link | DELIV | Checklist in [FINAL_EVALUATION_REPORT.md](../FINAL_EVALUATION_REPORT.md) | — | — | ⏳ after D1 + D8 |

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
| X1 | Two services: Meeting Service (system of record) + stateless AI Processing Service | EXTRA | `backend/meeting-service`, `backend/ai-service` | Each service has its own test suite | docker compose up | ✅ Two services, independently tested (183 + 39 tests) and deployed by compose |
| X2 | Kafka for async processing only (never CRUD) | EXTRA | Topics `meeting.events`, `ai.events`; transactional outbox; idempotent consumers | Kafka integration test in CI (service container) | Upload → summary arrives via Kafka | ✅ Outbox relay + idempotent consumer; real-broker pipeline test passes locally (CI job defined) |
| X2a | Visible processing state `not_requested → pending → processing → completed / failed` | EXTRA (supports R3.4) | `meetings.processing_status`; FE `SummaryStatus` ("Generating notes…" / Ready / Failed + Retry) | Service unit (state transitions); integration; E2E | New meeting shows Processing… then Ready | ✅ status chip, generating skeleton, failed + Retry, 'Notes ready' toast; E2E |
| X2b | `PROCESSING_MODE=kafka\|http\|inline-test` — free-hosting fallback reusing the same envelope, processor and idempotent apply path | EXTRA (supports D8) | `EventPublisher` implementations in MS; AI `POST /internal/process` | Tests run the pipeline through `InMemoryEventPublisher`; HTTP mode integration test | Deployed demo generates summaries even without a broker | ✅ HTTP fallback tested in-process (`test_http_fallback_pipeline_end_to_end`) and in the AI service |
| X3 | Backend coverage ~90%+ (where practical) | EXTRA | pytest-cov, `--cov-fail-under=90` in CI | CI gate (reproduced in a Linux container) | Coverage report | ✅ 97 % / 99 % line + branch |
| X4 | Playwright E2E for critical flows | EXTRA | `frontend/tests/e2e` | CI job | — | ✅ 39 Playwright tests against the real stack |
| X5 | GitHub Actions CI on PR + push to main | EXTRA | `.github/workflows/ci.yml`: backend lint/format/types/tests+coverage, contract check, Kafka job, frontend lint/format/types/unit/build/E2E | Every job's commands run locally; backend job reproduced in `python:3.11-slim` | Green checks on PRs | 🟨 verified locally; first GitHub run when the repo is published |
| X6 | Professional Git workflow: issues → branches → PRs | EXTRA | [PROJECT_PLAN.md](PROJECT_PLAN.md); feature branches merged with `--no-ff`; PR descriptions in [PULL_REQUESTS.md](PULL_REQUESTS.md) | — | Git history | ✅ locally; PRs become real once published |
| X7 | Loading / empty / error states on every screen | EXTRA (supports R5) | Shared `ui/EmptyState`, `ui/ErrorState`, skeletons | E2E with mocked API failure | — | ✅ shared EmptyState/ErrorState/Skeleton on every screen; E2E failure specs |
| X8 | Security basics: validation, CORS, env config, no secrets, safe rendering of uploads | EXTRA | Env-based config, `.env.example` only; CORS allow-list; generic 500s; non-root containers; Pydantic limits on every field incl. transcript size (`MAX_TRANSCRIPT_CHARS`); strict transcript parsers with line-numbered errors; React escaping (search highlights are `<mark>` elements, no HTML injection); internal token compared in constant time; prod publishes only Caddy's ports | `test_config.py`, `test_health.py` (CORS), `test_errors.py`, internal API auth tests | Secrets scan of the repo: clean | ✅ |

## 12. Timeline & constraints (PDF "Timeline", "AI Tools Usage")

| ID | Constraint | Consequence for this project |
|----|-----------|------------------------------|
| G1 | Estimated effort ≈ **24 hours** | Must-haves first; Kafka/CI/extra docs are budgeted on top and are the first thing cut if time runs short (never a MUST row) |
| G2 | Submission deadline "as communicated" | Deployment must be stable **before** the deadline, not on it — the hosted link is a deliverable |
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
