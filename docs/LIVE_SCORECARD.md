# Live Scorecard

Evidence-based status against the PDF's evaluation criteria. No numeric weights exist in the PDF; none are invented.
Statuses: **NOT STARTED** · **IN PROGRESS** · **VERIFIED** (implemented + tested + demonstrable) · **AT RISK**.

_Last updated: Milestone L (final audit, interview prep). Strict summary: [FINAL_EVALUATION_REPORT.md](../FINAL_EVALUATION_REPORT.md)._

| Criterion | Status | Evidence so far | Open risk |
|-----------|--------|-----------------|-----------|
| Functionality | VERIFIED | All 30 MUST rows ✅ — 39 E2E tests against the real stack + 222 backend tests + 2 real-Kafka tests; production stack verified locally | Hosted demo needs the owner to pick a host |
| UI/UX | VERIFIED | Fireflies-style shell, notepad layout, section order, speaker colours, states, toasts, responsive (E2E) — screenshots in README | Subjective similarity |
| Database Design | VERIFIED | 3NF schema, constraints enforced in SQLite and tested; migration ≡ models | — |
| Backend / API Design | VERIFIED | 14 REST endpoints, router→service→repository, one error envelope, OpenAPI; real Kafka pipeline (outbox, idempotent consumer) verified end-to-end; 183 + 39 tests | — |
| Code Quality | VERIFIED | ruff + strict mypy clean; ESLint/Prettier/tsc clean; backend CI job reproduced in a clean Linux container | CI not yet run on GitHub (repo not published) |
| Code Modularity | VERIFIED | Publisher / provider / parser / PlaybackClock abstractions; pure tested logic in `lib/`; reusable UI kit; one hooks module for server state | — |
| Code Understanding | PREPARED | ADRs 001–008, DEVELOPMENT_GUIDE, INTERVIEW_GUIDE (29 answers citing real files), FINAL_DEMO_SCRIPT | Demonstrated only in the interview itself |
| Bonus | VERIFIED | 4 of 6: global search, export TXT/MD, dark mode, tags — each with unit + E2E tests | Comments and Ask chat deliberately deferred |
