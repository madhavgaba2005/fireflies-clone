# Live Scorecard

Evidence-based status against the PDF's evaluation criteria. No numeric weights exist in the PDF; none are invented.
Statuses: **NOT STARTED** · **IN PROGRESS** · **VERIFIED** (implemented + tested + demonstrable) · **AT RISK**.

_Last updated: Milestone C (Kafka + AI service)._

| Criterion | Status | Evidence so far | Open risk |
|-----------|--------|-----------------|-----------|
| Functionality | IN PROGRESS | Every CRUD/search/filter capability works at the API level | No UI yet |
| UI/UX | NOT STARTED | UI spec written | Fireflies fidelity is the largest effort |
| Database Design | VERIFIED | 3NF schema, constraints enforced in SQLite and tested; migration ≡ models | — |
| Backend / API Design | VERIFIED | 14 REST endpoints, router→service→repository, one error envelope, OpenAPI; real Kafka pipeline (outbox, idempotent consumer) verified end-to-end; 171 + 39 tests | — |
| Code Quality | IN PROGRESS | ruff + strict mypy clean; ESLint/Prettier/tsc clean | CI not yet run on GitHub |
| Code Modularity | IN PROGRESS | Publisher / provider / parser abstractions; one processor shared by Kafka and HTTP; services share nothing but a pinned contract | Frontend modularity pending |
| Code Understanding | IN PROGRESS | ADRs, development guide | Interview guide answers pending |
| Bonus | NOT STARTED | — | Only after all MUST rows are verified |
