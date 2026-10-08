# Project Plan — Phases, Issues, Branches, PRs

## 1. Git workflow

```
GitHub issue #N → branch <type>/<N>-<slug> → small conventional commits → PR "Closes #N" → CI green
→ self-review against the PR template → merge commit into main → delete branch
```

* `main` is always deployable. After the initial commit, nothing lands on `main` except through a PR.
* Branch prefixes: `feature/`, `fix/`, `docs/`, `test/`, `ci/`, `chore/`.
* Merge strategy: **merge commits** (keeps each conventional commit visible — the history is part of the evaluation).
* Commits: Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `ci:`, `chore:`, `refactor:`), imperative,
  ≤ 72-char subject. Never `final`, `changes`, `wip`, `minor changes`.
* PRs use [.github/pull_request_template.md](../.github/pull_request_template.md): what changed · why · modules ·
  testing evidence · screenshots · known limitations · requirement IDs · `Closes #N`.

## 2. Phases → issues → branches

| Phase | Work | Issue | Branch | Req IDs | Exit criterion |
|-------|------|-------|--------|---------|----------------|
| 0 | Assignment analysis | #1 | `docs/1-requirements-analysis` | all | Requirements & evaluation matrices |
| 1 | Architecture, schema, API, events, UI spec, docs, ADRs, Git plan | #1 | same branch | all | **Your approval** |
| 2 | Project scaffolding (both services, frontend, tooling, compose, `.env.example`) | #2 | `chore/2-project-scaffolding` | C1–C3 | `docker compose up` starts empty services; lint passes |
| 3 | Database schema, migrations, seed data | #3, #8 | `feature/3-database-schema`, `feature/8-seed-data` | C3, C6, C7, R4.9 | Fresh DB → migrate → seed; schema tests pass |
| 4 | Meeting API + transcript parsing/API | #4, #5 | `feature/4-meeting-api`, `feature/5-transcript-api` | R1.1–R1.5, R2.1, R4.* | Integration tests green |
| 5 | Kafka infrastructure (envelope, publishers, outbox, consumer) | #6 | `feature/6-kafka-events` | X2, X2a, X2b | In-memory pipeline test green |
| 6 | AI processing service | #7 | `feature/7-ai-processing` | R3.* | Kafka E2E: create → summary persisted |
| 7 | Frontend shell (layout, sidebar, top bar, settings, placeholders) | #9 | `feature/9-meetings-dashboard` | R1.6, R5.1, R5.5, M* | Navigation works |
| 8 | Meetings dashboard | #9 | same | R1.* | E2E list/search/filter/sort |
| 9 | Meeting detail page | #10 | `feature/10-meeting-detail` | R2.1, R3.*, R5.2 | Workspace renders seeded meeting |
| 10 | Transcript synchronization | #11 | `feature/11-transcript-sync` | R2.2–R2.4 | E2E click-to-seek + active line follows |
| 11 | Meeting CRUD UI | #13 | `feature/13-meeting-crud` | R4.1–R4.5, R5.3, R5.4 | E2E CRUD + reload |
| 12 | Action items | #14 | `feature/14-action-items` | R4.6–R4.8 | E2E + reload |
| 13 | Transcript search | #12 | `feature/12-transcript-search` | R2.5 | Unit + E2E |
| 14 | Testing gaps | #17 | `test/17-coverage` | X3, X4 | All MUST rows have passing tests |
| 15 | CI | #18 | `ci/18-github-actions` | X5 | Required checks on PRs |
| 16 | UI polish / Fireflies fidelity | #15 | `feature/15-ui-polish` | R5.*, X7 | UI checklist ticked |
| 17 | Bonus features | #16 | `feature/16-<bonus>` (one per bonus) | B* | Each with tests |
| 18 | Deployment | #19 | `chore/19-deployment` | D8 | Verification checklist passed on the live URL |
| 19 | Full assignment audit | #21 | `docs/21-final-audit` | all | FINAL_EVALUATION_REPORT, HIGH/CRITICAL fixed |
| 20 | Interview preparation | #20 | `docs/20-documentation` | C9 | INTERVIEW_GUIDE, FINAL_DEMO_SCRIPT complete |

**Pulled forward (deliberately):** a minimal CI workflow (lint + backend tests) is added in Phase 3 so that every
later PR is gated; Phase 15 extends it with frontend build, E2E and the Kafka job.

**Time budget** (PDF estimates ≈ 24 h for the core; extras on top): backend ~7 h · events/AI ~4 h · frontend ~10 h ·
tests/CI ~4 h · deploy ~2 h · docs/audit ~3 h. If time runs short, cut in this order: bonuses → Kafka CI job →
polish extras. **Never** a MUST row.

## 3. Issue list

| # | Title | Labels |
|---|-------|--------|
| 1 | Analyze assignment requirements and design architecture | docs |
| 2 | Project scaffolding | chore |
| 3 | Database schema and migrations | backend, database |
| 4 | Meeting API (CRUD, search, filters, sort) | backend |
| 5 | Transcript parsing and transcript API | backend |
| 6 | Kafka event infrastructure | backend, events |
| 7 | AI processing service | backend, events |
| 8 | Realistic seed data | backend |
| 9 | Meetings dashboard | frontend |
| 10 | Meeting detail workspace | frontend |
| 11 | Transcript ↔ player synchronization | frontend |
| 12 | Transcript search with highlighting | frontend |
| 13 | Meeting CRUD UI | frontend |
| 14 | Action item CRUD | frontend, backend |
| 15 | Fireflies UI polish | frontend |
| 16 | Bonus features | enhancement |
| 17 | Automated testing | test |
| 18 | GitHub Actions CI | ci |
| 19 | Deployment | chore |
| 20 | Documentation and interview preparation | docs |
| 21 | Final rubric audit | docs |

## 4. Creating the issues

The GitHub CLI is **not installed** on the development machine yet. Install it (`winget install --id GitHub.cli`),
run `gh auth login`, then from the repository root (Git Bash):

```bash
while IFS='|' read -r title labels; do
  gh issue create --title "$title" --body "See docs/PROJECT_PLAN.md and docs/REQUIREMENTS_MATRIX.md." \
    $(for l in ${labels//,/ }; do printf -- '--label %s ' "$l"; done)
done <<'EOF'
Analyze assignment requirements and design architecture|docs
Project scaffolding|chore
Database schema and migrations|backend,database
Meeting API (CRUD, search, filters, sort)|backend
Transcript parsing and transcript API|backend
Kafka event infrastructure|backend,events
AI processing service|backend,events
Realistic seed data|backend
Meetings dashboard|frontend
Meeting detail workspace|frontend
Transcript player synchronization|frontend
Transcript search with highlighting|frontend
Meeting CRUD UI|frontend
Action item CRUD|frontend,backend
Fireflies UI polish|frontend
Bonus features|enhancement
Automated testing|test
GitHub Actions CI|ci
Deployment|chore
Documentation and interview preparation|docs
Final rubric audit|docs
EOF
```
Labels must exist first: `for l in docs chore backend database events frontend enhancement test ci; do gh label create "$l" --force; done`.
Issues are created in order, so the numbers match the table on a fresh repository.
