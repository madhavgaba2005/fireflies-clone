# CI / CD

> **Status:** the workflow is written ([`.github/workflows/ci.yml`](../.github/workflows/ci.yml)) and every job's
> commands pass locally. The backend job was also re-run in a clean `python:3.11-slim` Linux container.
> It has **not run on GitHub yet**: that happens on the first push, once the author publishes the repository.
> Branch protection is configured at that point.

## Why CI
Every PR proves it doesn't break lint, types, tests, coverage or the build. With a one-person team, CI is the
reviewer that never gets tired, and green checks on PRs are visible evidence for the evaluator.

## Pipeline (`on: pull_request` and `push` to `main`; concurrent runs per ref are cancelled)

| Job | Steps | Fails when |
|-----|-------|-----------|
| `backend (meeting-service)`, `backend (ai-service)` (matrix) | Python 3.11 (pip cache) → `ruff check` → `ruff format --check` → `mypy app` (strict) → `pytest --cov --cov-fail-under=90` → upload `coverage.xml` | lint, format, types, tests, or coverage below 90 % |
| `event-contract` | `cmp` both `envelope_v1.schema.json` and `payloads_v1.schema.json` between the two services | the services' event contracts drifted |
| `kafka` (after `backend`) | `docker compose up -d --build --wait kafka ai-service` → `pytest -m kafka -v` (round trip, full pipeline through the AI container, duplicate delivery) → AI and Kafka logs on failure | real Kafka publish/consume or the async pipeline is broken |
| `frontend` | Node 22 (npm cache) → `npm ci` → ESLint → Prettier check → `next typegen && tsc` → Vitest → `next build` → install both services' requirements → Playwright (report uploaded on failure) | lint, format, types, unit, build or E2E |

**How the E2E job works** (`frontend/playwright.config.ts`):
1. It starts the AI Service and the Meeting Service in `PROCESSING_MODE=http`, so no broker is needed here; the
   `kafka` job covers the broker.
2. It resets and seeds a dedicated SQLite file.
3. It builds and starts the production frontend.
4. Chromium then drives the real stack, with one worker.

## Verified locally (latest run)

| Job | Result |
|-----|--------|
| backend × 2 | ruff, format, mypy clean; 183 + 39 tests; 97.45 % / 98.84 % coverage (gate 90 %) |
| event-contract | both schema files identical |
| kafka | 3 passed against the compose broker and AI container |
| frontend | lint, format, typecheck, build clean; 75 Vitest + 42 Playwright tests passed |
| workflow file | parsed as valid YAML (4 jobs) |

## Branch protection (to set once the repository is public)
- Require a PR to merge into `main`.
- Require all four jobs to pass, with the branch up to date.
- Disallow force-pushes.

## Deployment flow
There is no automatic deployment: the host is still the author's choice (see [DEPLOYMENT.md](DEPLOYMENT.md)).
After choosing one, deploying is `git pull && docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env
up -d --build --wait` on the VM, followed by the post-deploy checklist in DEPLOYMENT §5. A deploy job triggered on
`main` could run that command over SSH later.
