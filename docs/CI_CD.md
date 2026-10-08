# CI / CD

> Status: **Workflow written (Phase 2)** — [`.github/workflows/ci.yml`](../.github/workflows/ci.yml). Every step has been run
> locally; it runs on GitHub for the first time when the repository is published. Branch protection is configured then.

## Why CI
Every PR proves it doesn't break lint, types, tests, coverage or the build. With a one-person team it is the "reviewer
that never gets tired", and the green checks on PRs are visible evidence for the evaluator.

## Pipeline (`.github/workflows/ci.yml`, on `pull_request` and `push` to `main`)

| Job | Steps | Fails when |
|-----|-------|-----------|
| `backend (meeting-service)`, `backend (ai-service)` (matrix) | Python 3.11 (pip cache) → `ruff check` → `ruff format --check` → `mypy app` (strict) → `pytest --cov --cov-fail-under=90` → coverage artifact | lint / format / types / tests / coverage < 90 % |
| `event-contract` | `cmp` the two `envelope_v1.schema.json` files | the services' event contracts drifted |
| `kafka` (after backend) | `docker compose up -d --wait kafka` (same config as local) → `pytest -m kafka` | real Kafka publish/consume broken |
| `frontend` | Node 22 (npm cache) → `npm ci` → ESLint → Prettier check → `next typegen && tsc` → Vitest → `next build` → Playwright smoke (report uploaded on failure) | lint / format / types / unit / build / E2E |

From Phase 8, the E2E step also starts a seeded Meeting Service (`PROCESSING_MODE=inline-test`) before Playwright runs.

## Branch protection (recommended, set in GitHub settings)
Require PR to merge into `main`, require all CI jobs to pass, require branch up to date, disallow force-push.

## Deployment flow
Merge to `main` → hosting platforms auto-deploy from `main` (see [DEPLOYMENT.md](DEPLOYMENT.md)) → post-deploy smoke script hits `/health/ready` and `GET /api/meetings`.
