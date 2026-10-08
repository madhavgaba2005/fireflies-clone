# Deployment

> **Status: ready to deploy, not yet deployed.** The production stack below has been built and run locally, and it
> passed the checklist in §5. Two things are still pending:
> - **The hosting provider is the owner's decision.** Nothing has been purchased, and no public repository or URL
>   exists yet.
> - **Persistence and summary processing on the real host** will be claimed only after the checklist has been run
>   there.

## 1. Requirements the hosted demo must meet

| # | Requirement | Source |
|---|-------------|--------|
| H1 | Public, working link | PDF deliverable |
| H2 | CRUD survives a refresh **and** a server restart, so SQLite must be on a persistent disk | PDF R4.9 |
| H3 | New meetings get summaries | PDF R3.4 |
| H4 | Free, or an explicitly approved cost | Project constraint |
| H5 | Real Kafka where possible, otherwise the documented `PROCESSING_MODE=http` fallback | Project constraint |

## 2. Options (free-first; re-check free-tier terms before choosing, because they change often)

| Option | What runs where | Events | Cost | Main risk |
|--------|-----------------|--------|------|-----------|
| **A. One free VM + `deploy/docker-compose.prod.yml`** (recommended), e.g. an Oracle Cloud Always Free Ampere VM or any VM with Docker and ≥ 2 GB RAM | Everything on the VM behind Caddy, with automatic HTTPS | **Real Kafka** | Free (Oracle asks for a card to verify identity) | Setup time; free capacity in some regions |
| B. Free PaaS + HTTP fallback | Frontend on a static/Next host; both services on a PaaS **with a persistent volume** | `http` mode | Free only if the tier offers a volume | Many free tiers have ephemeral disks or sleep when idle, which breaks H2 |
| C. Low-cost PaaS (e.g. a hobby plan with volumes) | Same as A or B | Kafka container or `http` | About US$5/month: **needs the owner's approval** | Cost |

**Recommendation: A.** It is the only option where the hosted demo is the same system the tests verify, real Kafka
included, and it costs nothing. Fall back to B only if no free VM can be provisioned, and only on a tier with a
persistent volume.

## 3. Production stack (option A)

The files are in [`deploy/`](../deploy):

- `docker-compose.prod.yml`: Caddy, frontend (Next.js standalone image), Meeting Service, AI Service and Kafka (KRaft,
  256 MB heap).
- `Caddyfile`: one public origin. `/api/*`, `/health*` and `/docs` go to the Meeting Service; everything else goes to
  the frontend. The browser therefore never makes a cross-origin call, and one TLS certificate covers the whole app.
- `.env.example`: copy it to `deploy/.env`. This file holds no secrets: Kafka mode needs no internal token, because
  the AI Service exposes no ports.

Security posture:
- Only Caddy publishes ports (80/443). Kafka, both services and the database are reachable only on the internal Docker
  network.
- Containers run as unprivileged users, and each has `restart: unless-stopped`.

```bash
# On the VM (Docker + Compose plugin installed; ports 80/443 open in the VM firewall/security list)
git clone <repo-url> lumen && cd lumen
cp deploy/.env.example deploy/.env
#   SITE_ADDRESS=notes.example.com   → Caddy fetches a Let's Encrypt certificate automatically
#   (or SITE_ADDRESS=:80 to serve plain HTTP on the VM's IP)
#   PUBLIC_URL=https://notes.example.com
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env up -d --build --wait

# Update to a new version (the SQLite volume is kept)
git pull && docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env up -d --build --wait

# Back up the database
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env exec meeting-service \
  python -c "import sqlite3; s=sqlite3.connect('/data/meetings.db'); d=sqlite3.connect('/data/backup.db'); s.backup(d)"
```

**Persistence:**
- **SQLite** lives in the `meeting-data` named volume. It survives container restarts, rebuilds and redeploys, and
  is deleted only by `docker compose down -v`.
- **Kafka** keeps its log in the `kafka-data` volume, so a request already handed to the broker survives a broker
  restart. Verified: with the AI Service stopped, a new meeting's request sat in Kafka; after the broker restarted
  and the AI Service started, the meeting completed.
- **Outbox:** events not yet published stay in the SQLite outbox and are re-sent when Kafka is back (see
  [EVENT_DRIVEN_ARCHITECTURE.md](EVENT_DRIVEN_ARCHITECTURE.md)).

### Option B notes (HTTP fallback)
- Meeting Service settings: `PROCESSING_MODE=http`, `AI_SERVICE_URL=<ai service URL>`, and
  `INTERNAL_API_TOKEN=<long random value>`. Set the same token on the AI Service; both services refuse to start
  without it in http mode.
- `DATABASE_URL` must point at the mounted volume.
- `CORS_ORIGINS` must be the frontend origin.
- Build the frontend with `NEXT_PUBLIC_API_URL=<meeting service URL>`.

## 4. Configuration reference

| Variable | Service | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | meeting-service | e.g. `sqlite:////data/meetings.db` (must be on the persistent disk) |
| `CORS_ORIGINS` | meeting-service | Frontend origin(s), comma-separated |
| `PROCESSING_MODE` | both | `kafka` (default) \| `http` (fallback) \| `inline-test` (tests only) |
| `KAFKA_BOOTSTRAP_SERVERS` | both | Broker address (kafka mode) |
| `AI_SERVICE_URL`, `INTERNAL_API_TOKEN` | meeting-service / ai-service | HTTP fallback only |
| `SEED_ON_STARTUP` | meeting-service | Load demo meetings when the database is empty |
| `SUMMARY_PROVIDER` | ai-service | `mock` (the only provider implemented; see TRADEOFFS) |
| `NEXT_PUBLIC_API_URL` | frontend (build time) | Meeting Service base URL; empty means same origin |
| `SITE_ADDRESS`, `PUBLIC_URL`, `HTTP_PORT`, `HTTPS_PORT` | deploy/.env | Caddy site, CORS origin, host ports |

## 5. Post-deploy verification checklist

Run **locally** against `deploy/docker-compose.prod.yml` on `http://localhost:8088`, rebuilt from the final code
(2026-10-09). **It must be repeated on the real host**: nothing below means a live deployment exists.

- [x] Frontend loads, and the library shows the 7 seeded meetings
- [x] `/health/ready` is OK; all five containers are healthy
- [x] Create a meeting by pasting a transcript: Processing → Ready through Kafka in about 2 s
- [x] Edit a meeting; add, edit, complete and delete an action item; delete a meeting (→ 404 afterwards)
- [x] **Restart the whole stack: the data persists.** Restart Kafka mid-request: the request still completes
- [x] Transcript click-to-seek, active-line highlight, expanded panels, theme settings (headless browser)
- [x] No console or CORS errors (same origin through Caddy)

## 6. Readiness review

| Item | Status |
|------|--------|
| Environment variables | Documented in §4 and in each `.env.example`; production needs no secrets in Kafka mode |
| CORS | Same origin through Caddy. `CORS_ORIGINS=${PUBLIC_URL}` is still set for direct API access |
| Production builds | Next.js standalone image; both Python images non-root; `next build` clean |
| Health endpoints | `/health` (liveness) and `/health/ready` (database) on the Meeting Service, `/health` on the AI Service; used by compose healthchecks |
| Startup order | `depends_on: service_healthy`: Kafka → services → Caddy. The services also retry the broker with backoff |
| Persistence | SQLite and Kafka on named volumes (verified above) |
| Kafka configuration | KRaft single node, internal listener only, 256 MB heap, auto-created topics with 3 partitions, key = meeting ID |
| AI service | `SUMMARY_PROVIDER=mock`; no API key needed; no public port |
| Frontend API URL | Built with `NEXT_PUBLIC_API_URL=""` (same origin), so there are no `localhost` URLs in the bundle |
| Dev-only assumptions | None in the prod stack: no dev servers, no `--reload`, no hard-coded localhost |
| Live deployment | **Not done.** The host is the author's decision; nothing has been purchased |
