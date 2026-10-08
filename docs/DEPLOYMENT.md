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
- The SQLite file lives in the `meeting-data` named volume. It survives container restarts, rebuilds and
  redeploys, and is deleted only by `docker compose down -v`.
- Kafka keeps no state of its own that matters. The transactional outbox in SQLite is the source of truth, and
  unpublished events are re-sent after a restart (see [EVENT_DRIVEN_ARCHITECTURE.md](EVENT_DRIVEN_ARCHITECTURE.md)).

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

Last run: **locally**, with `deploy/docker-compose.prod.yml` on `http://localhost:8088`. The results are recorded in
[PROGRESS.md](PROGRESS.md). The same checklist must be repeated on the real host.

- [ ] Frontend loads, and the library shows the seeded meetings
- [ ] `/health/ready` is OK; both services are healthy
- [ ] Create a meeting by pasting a transcript; its summary goes from Processing to Ready (through Kafka)
- [ ] Edit and delete a meeting; add, edit and complete an action item
- [ ] Refresh: state persists. **Restart the stack: state persists**
- [ ] Transcript click-to-seek, playback highlight, transcript search
- [ ] No CORS or console errors
