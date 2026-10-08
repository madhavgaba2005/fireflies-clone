# Deployment

> Status: **Planned (Phase 1) — target chosen in Phase 18.** Nothing will be purchased automatically.
> Persistence and summary processing will be claimed **only after** being verified on the chosen host.

## 1. Requirements the hosted demo must meet

| # | Requirement | Source |
|---|-------------|--------|
| H1 | Public, working link | PDF deliverable |
| H2 | CRUD survives refresh **and** a server restart → SQLite on a persistent disk | PDF R4.9 |
| H3 | New meetings get summaries | PDF R3.4 |
| H4 | Free (or explicitly approved cost) | Project constraint |
| H5 | Real Kafka where possible; otherwise the documented `PROCESSING_MODE=http` fallback | Project constraint |

## 2. Candidate topologies (to be re-verified in Phase 18 — free-tier terms change often)

| Option | Frontend | Meeting Service + SQLite | AI Service | Events | Cost | Main risk |
|--------|----------|--------------------------|-----------|--------|------|-----------|
| **A. One free VM** (e.g. Oracle Cloud Always Free) running `docker compose` + Caddy (HTTPS) | Vercel (free) or on the VM | VM disk (persistent) | VM | **Real Kafka** on the VM | Free (sign-up needs a card for verification) | Setup time; regional capacity availability |
| **B. Free PaaS + HTTP fallback** | Vercel (free) | PaaS service with a persistent volume, if the free tier offers one | PaaS service | `http` mode | Free if a volume is available | Many free tiers have **ephemeral** disks and sleep when idle → would violate H2 |
| C. Low-cost PaaS (e.g. Railway hobby) | Vercel | Service + volume | Service | Kafka container or `http` | ~US$5/month — **requires your approval** | Cost |
| D. Managed Kafka free/trial tier | Vercel | as A/B | as A/B | Managed Kafka (SASL) | Trials expire | Expiry during evaluation window |

**Current recommendation:** A if a free VM can be provisioned (everything real, including Kafka); otherwise B with
`http` mode, provided a persistent volume is verified. This becomes a "Decision needed" item at Phase 18.

## 3. Configuration (finalized in Phase 2 `.env.example` files)

| Variable | Service | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | meeting-service | e.g. `sqlite:////data/meetings.db` (must point at the persistent disk) |
| `CORS_ORIGINS` | meeting-service | Frontend origin(s), comma-separated |
| `PROCESSING_MODE` | meeting-service | `kafka` \| `http` \| `inline-test` |
| `KAFKA_BOOTSTRAP_SERVERS` | both | Broker address (kafka mode) |
| `AI_SERVICE_URL`, `INTERNAL_API_TOKEN` | meeting-service / ai-service | HTTP fallback |
| `SUMMARY_PROVIDER`, `LLM_API_KEY` | ai-service | `mock` (default) \| `llm` |
| `NEXT_PUBLIC_API_URL` | frontend | Meeting Service base URL |

## 4. Post-deploy verification checklist (Phase 18)
- [ ] Frontend loads; library shows seeded meetings
- [ ] `/health/ready` OK for both services
- [ ] Create (paste) → summary goes Processing → Ready
- [ ] Edit / delete meeting; add / edit / complete action item
- [ ] Refresh → state persists; **restart service → state persists**
- [ ] Transcript click-to-seek, playback highlight, transcript search
- [ ] CORS: no browser console errors
