# Deployment

> **Status: deployed on Fly.io.** Frontend https://lumen-mg.fly.dev · API https://lumen-api-mg.fly.dev. The post-deploy checklist (§5) passed
> against the live site on 2026-10-09. The single-VM compose stack (§3) remains a documented, verified alternative.

## 0. Live deployment: Fly.io

Four apps in region `sin`, connected over Fly's private IPv6 network (`<app>.internal`):

| App | Config | What runs | Exposure | Machine |
|-----|--------|-----------|----------|---------|
| `lumen-kafka-mg` | [`deploy/fly/kafka.toml`](../deploy/fly/kafka.toml) | Kafka 3.9 KRaft, log on volume `kafka_data` (1 GB) | private: `lumen-kafka-mg.internal:9092` | shared 1 CPU / 1 GB |
| `lumen-ai-mg` | [`deploy/fly/ai-service.toml`](../deploy/fly/ai-service.toml) | AI service, Kafka consumer | private | shared 1 CPU / 512 MB |
| `lumen-api-mg` | [`deploy/fly/meeting-service.toml`](../deploy/fly/meeting-service.toml) | Meeting Service; SQLite on volume `meeting_data` (1 GB); health check `/health/ready` | public HTTPS | shared 1 CPU / 512 MB, always on |
| `lumen-mg` | [`deploy/fly/frontend.toml`](../deploy/fly/frontend.toml) | Next.js standalone, built with `NEXT_PUBLIC_API_URL=https://lumen-api-mg.fly.dev` | public HTTPS | shared 1 CPU / 512 MB, always on |

**Fly-specific details:**
- **Volumes mount owned by root.** `backend/meeting-service/Dockerfile.fly` starts as root, hands `/data` to
  `appuser`, then runs the server as `appuser` via `runuser`.
- **Kafka** runs as root inside its private microVM (`deploy/fly/kafka.Dockerfile`).
  - It listens on `[::]` and advertises `lumen-kafka-mg.internal:9092`.
  - Its log dir is a subdirectory of the volume, avoiding `lost+found`.
  - A fixed `CLUSTER_ID` keeps the storage valid across restarts.
- **Always-on machines.** The Meeting Service runs the outbox relay and the result consumer, so it must not
  auto-stop. The frontend stays on to avoid cold starts.
- **CORS:** `CORS_ORIGINS=https://lumen-mg.fly.dev`.

**Deploy or redeploy** from the repo root, in this order:
```bash
flyctl deploy deploy/fly --config kafka.toml --ha=false
flyctl deploy backend/ai-service --config ../../deploy/fly/ai-service.toml --ha=false
flyctl deploy backend/meeting-service --config ../../deploy/fly/meeting-service.toml --dockerfile Dockerfile.fly --ha=false
flyctl deploy frontend --config ../deploy/fly/frontend.toml --ha=false
```
**First-time setup** (already done for this deployment):
```bash
flyctl apps create <app>
flyctl volumes create kafka_data   --app lumen-kafka-mg --region sin --size 1
flyctl volumes create meeting_data --app lumen-api-mg   --region sin --size 1
```

**Verified live (2026-10-09):**
- All 22 requirement checks pass in Chromium against https://lumen-mg.fly.dev, with no console errors.
- A new meeting completes through outbox → Kafka → AI → Kafka in about 1 s.
- After `flyctl machine restart` of both the API and the Kafka machines, an earlier meeting was still there, and a
  new meeting was processed through Kafka.
- The Lumen favicon is served.

**Cost:** four small always-on machines plus 2 GB of volumes, billed to the owner's Fly account.

**Operations:**
- `flyctl logs --app <app>` and `flyctl status --app <app>`.
- Back up the database with `flyctl ssh console --app lumen-api-mg`, then `sqlite3`-copy `/data/meetings.db`.
- Volumes also have Fly's scheduled snapshots (5-day retention).

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
git clone https://github.com/madhavgaba2005/fireflies-clone.git lumen && cd lumen
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
