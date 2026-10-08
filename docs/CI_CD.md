# CI / CD

> Status: **Planned (Phase 1)** — workflow added right after the schema phase so all later PRs are gated.

## Why CI
Every PR proves it doesn't break lint, types, tests, coverage or the build. With a one-person team it is the "reviewer
that never gets tired", and the green checks on PRs are visible evidence for the evaluator.

## Pipeline (`.github/workflows/ci.yml`, on `pull_request` and `push` to `main`)

| Job | Steps | Fails when |
|-----|-------|-----------|
| `meeting-service` | setup Python 3.11 (pip cache) → `ruff check` → `ruff format --check` → `mypy app` → `pytest --cov --cov-fail-under=90` → upload coverage artifact | lint/type/test/coverage |
| `ai-service` | same | same |
| `kafka-integration` | Kafka service container → `pytest -m kafka` | event pipeline broken |
| `frontend` | setup Node 22 (npm cache) → `npm ci` → `eslint` → `prettier --check` → `tsc --noEmit` → `next build` | lint/type/build |
| `e2e` (needs backend + frontend) | start meeting-service (memory bus, fresh seeded DB) → `next start` → `playwright test` → upload report on failure | any critical flow broken |

## Branch protection (recommended, set in GitHub settings)
Require PR to merge into `main`, require all CI jobs to pass, require branch up to date, disallow force-push.

## Deployment flow
Merge to `main` → hosting platforms auto-deploy from `main` (see [DEPLOYMENT.md](DEPLOYMENT.md)) → post-deploy smoke script hits `/health/ready` and `GET /api/meetings`.
