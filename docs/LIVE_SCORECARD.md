# Live Scorecard

Evidence-based status against the PDF's evaluation criteria. No numeric weights exist in the PDF; none are invented.
Statuses: **NOT STARTED** · **IN PROGRESS** · **VERIFIED** (implemented + tested + demonstrable) · **AT RISK**.

_Last updated: Milestone A (database + seed)._

| Criterion | Status | Evidence so far | Open risk |
|-----------|--------|-----------------|-----------|
| Functionality | NOT STARTED | Seed data ready (7 meetings) | All user-facing features pending |
| UI/UX | NOT STARTED | UI spec written | Fireflies fidelity is the largest effort |
| Database Design | VERIFIED | 3NF schema, constraints enforced in SQLite and tested; migration ≡ models | — |
| Backend / API Design | IN PROGRESS | Layering, error envelope, health; parser | Endpoints pending (Milestone B) |
| Code Quality | IN PROGRESS | ruff + strict mypy clean; ESLint/Prettier/tsc clean | CI not yet run on GitHub |
| Code Modularity | IN PROGRESS | Publisher abstraction, parser strategy, repositories | — |
| Code Understanding | IN PROGRESS | ADRs, development guide | Interview guide answers pending |
| Bonus | NOT STARTED | — | Only after all MUST rows are verified |
