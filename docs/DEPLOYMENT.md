# Deployment

> Status: **Decision pending (D1)**. Constraints the target must satisfy:
> 1. SQLite file on a **persistent volume** (otherwise CRUD is lost on restart — violates R4.9).
> 2. Somewhere to run Kafka, or a documented fallback.
> 3. Free or near-free, stable through the evaluation window.

## Candidate topologies

| Option | Frontend | Meeting Service + SQLite | AI Service | Kafka | Cost | Risk |
|--------|----------|--------------------------|-----------|-------|------|------|
| **A (recommended)** | Vercel | Railway service + volume | Railway service | Railway service (single-node KRaft container, ~512 MB) | Railway Hobby ≈ $5/mo | Low; everything real |
| B | Vercel | Render web service + persistent disk (paid plan) | Render background worker | Managed (Redpanda Serverless / Confluent Cloud trial) | Free tier credits; trials expire | Medium: trial expiry, SASL config |
| C | Vercel | Any host with a volume | in-process (`EVENT_BUS=memory`) | none in prod; real Kafka only in compose + CI | Cheapest | Kafka not visible in the live demo (documented fallback) |
| D | One VM (e.g. Oracle Cloud free tier) running `docker compose` + Caddy for HTTPS | ← all on one VM → | | | Free | Setup time; VM availability |

_(Phase 18: chosen option, environment variables per service, smoke-test script, rollback steps.)_
