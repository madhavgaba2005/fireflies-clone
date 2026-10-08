# Live Scorecard

Evidence-based status against the PDF's evaluation criteria. No numeric weights exist in the PDF; none are invented.
Statuses: **NOT STARTED** · **IN PROGRESS** · **VERIFIED** (implemented + tested + demonstrable) · **AT RISK**.

_Last updated: Milestone F (frontend complete)._

| Criterion | Status | Evidence so far | Open risk |
|-----------|--------|-----------------|-----------|
| Functionality | VERIFIED | All 30 MUST rows ✅ — 33 E2E tests against the real stack + 210 backend tests + real-Kafka test | Hosted demo not deployed yet (Milestone J) |
| UI/UX | VERIFIED | Fireflies-style shell, notepad layout, section order, speaker colours, states, toasts, responsive (E2E) — screenshots in README | Subjective similarity; polish continues in Milestone G |
| Database Design | VERIFIED | 3NF schema, constraints enforced in SQLite and tested; migration ≡ models | — |
| Backend / API Design | VERIFIED | 14 REST endpoints, router→service→repository, one error envelope, OpenAPI; real Kafka pipeline (outbox, idempotent consumer) verified end-to-end; 171 + 39 tests | — |
| Code Quality | IN PROGRESS | ruff + strict mypy clean; ESLint/Prettier/tsc clean | CI not yet run on GitHub |
| Code Modularity | VERIFIED | Publisher / provider / parser / PlaybackClock abstractions; pure tested logic in `lib/`; reusable UI kit; one hooks module for server state | — |
| Code Understanding | IN PROGRESS | ADRs, development guide | Interview guide answers pending |
| Bonus | NOT STARTED | — | Only after all MUST rows are verified |
