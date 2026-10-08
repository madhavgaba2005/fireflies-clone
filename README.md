# Fireflies Clone — Meeting Notes & Transcription Platform

> **Status:** Phase 2 (project scaffolding) complete — both services and the frontend build, start and pass
> their checks; no business features yet (they start in Phase 3).
> Sections marked _(pending)_ are filled in by the phase that implements them. Live progress:
> [docs/REQUIREMENTS_MATRIX.md](docs/REQUIREMENTS_MATRIX.md).

## Overview
A Fireflies.ai-inspired meeting workspace built for the Scaler SDE Fullstack assignment. Browse a library of
meetings, open a meeting to read a speaker-labelled transcript synced to a media player, and review AI-generated
notes — keywords, overview, timestamped outline and action items. Real speech-to-text and live meeting bots are out
of scope (per the assignment): transcripts are seeded, uploaded (.txt / .vtt / .json) or pasted, and notes are
generated asynchronously by a separate AI Processing Service via Kafka.

## Demo
- Live app: _(pending — Phase 18)_
- API docs (Swagger): _(pending)_ `<api-url>/docs`
- Demo script: _(pending — Phase 19)_ `docs/FINAL_DEMO_SCRIPT.md`

## GitHub
- Repository: _(pending — public remote created before Phase 2 is merged)_
- Workflow: issue → feature branch → PR → CI → merge. See [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md).

## Features
**Core (assignment must-haves)**
- Meetings library: title, date, duration, participants · title search · date & participant filters · sort by recency · profile/settings placeholders
- Meeting workspace: speaker-labelled, timestamped transcript · media player with seek bar · click a line to seek, playback highlights and scrolls to the active line · in-transcript search with highlighted matches
- AI notes: keywords, overview, notes, timestamped outline/chapters, extracted action items — with a visible processing state (Processing → Ready / Failed + Retry)
- CRUD: create meetings (upload / paste / form), edit title, date & participants, delete; add / edit / complete / delete action items — all persisted
- Fireflies-style layout, modals, filters, toasts; "Coming soon" for live bot, speech-to-text, integrations, team sharing

**Bonus** (only after every must-have is done): global search · export TXT/Markdown · dark mode · tags — see [docs/BONUS_FEATURES.md](docs/BONUS_FEATURES.md)

## Tech Stack
| Layer | Choice |
|-------|--------|
| Frontend | Next.js 16 (App Router) · React 19 · TypeScript (strict) · Tailwind CSS v4 · Radix UI · TanStack Query · lucide-react · sonner (UI libraries are added in Phase 7 with their first use) |
| Meeting Service | Python 3.11 · FastAPI · SQLAlchemy 2.0 · Alembic · Pydantic v2 · aiokafka |
| AI Processing Service | Python 3.11 · FastAPI (health + HTTP-mode endpoint) · aiokafka · pluggable `SummaryProvider` |
| Database | SQLite (WAL, foreign keys enforced) |
| Messaging | Apache Kafka (single-node KRaft, Docker) |
| Testing | pytest · pytest-cov · pytest-asyncio · Vitest · Playwright |
| Tooling / CI | ruff · mypy · ESLint · Prettier · GitHub Actions · Docker Compose |

Every choice is justified in [docs/adr/](docs/adr/).

## Architecture
Two services with one clear seam. The **Meeting Service** is the system of record and serves all REST traffic.
The stateless **AI Processing Service** turns transcripts into notes. They communicate only through events, and
only for asynchronous work — CRUD never touches Kafka. Full detail: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Architecture Diagram
```mermaid
flowchart LR
    B[Browser] --> FE[Next.js frontend]
    FE -->|REST / JSON| MS[Meeting Service · FastAPI]
    MS --> DB[(SQLite)]
    MS -->|outbox relay → meeting.events| K[(Kafka)]
    K --> AI[AI Processing Service]
    AI -->|ai.events| K
    K -->|summary.generated| MS
```

## Services
| Service | Port | Responsibility |
|---------|------|----------------|
| `frontend` | 3000 | UI |
| `meeting-service` | 8000 | REST API, persistence, transcript parsing, outbox relay, AI-result consumer |
| `ai-service` | 8001 | Consumes processing requests, generates notes, publishes results |
| `kafka` | 9092 | Event broker (local / where hostable) |

## Kafka / Event Flow
`POST /api/meetings` → meeting + outbox row committed in one transaction (`pending`) → relay publishes
`meeting.created` (`processing`) → AI service generates notes → `summary.generated` → Meeting Service applies it
idempotently (`completed`) → the UI, polling while processing, shows "Notes ready".
`PROCESSING_MODE=kafka | http | inline-test` selects the transport; `http` is a documented fallback for hosts that
can't run a broker and reuses the same envelope and handlers.
Details: [docs/EVENT_DRIVEN_ARCHITECTURE.md](docs/EVENT_DRIVEN_ARCHITECTURE.md).

## Database Schema
`meetings` ⟷ `participants` (M:N via `meeting_participants`) · `transcript_segments` (speaker FK → participants) ·
`summaries` (1:1) → `summary_topics`, `summary_keywords` · `action_items` (assignee FK → participants) ·
infrastructure: `outbox_events`, `processed_events`.
ER diagram, constraints, indexes and rationale: [docs/DATABASE_DESIGN.md](docs/DATABASE_DESIGN.md).

## API Overview
| Method | Path |
|--------|------|
| GET / POST | `/api/meetings` (`q`, `participant_id`, `date_from`, `date_to`, `sort`, `limit`, `offset`) |
| GET / PATCH / DELETE | `/api/meetings/{id}` |
| GET | `/api/meetings/{id}/transcript` |
| GET | `/api/meetings/{id}/summary` · POST `/api/meetings/{id}/summary/regenerate` |
| GET / POST | `/api/meetings/{id}/action-items` |
| PATCH / DELETE | `/api/action-items/{id}` |
| GET | `/api/participants` |
| GET | `/health`, `/health/ready` |

Full contract with examples and error codes: [docs/API.md](docs/API.md).

## Project Structure
```
backend/meeting-service   FastAPI system of record (routers → services → repositories → SQLAlchemy)
backend/ai-service        Stateless event consumer/producer with pluggable summary providers
frontend/                 Next.js + TypeScript app
docs/                     Requirements, evaluation, architecture, schema, API, events, testing, ADRs, guides
.github/                  CI workflows, PR template
```
Detailed tree: [docs/ARCHITECTURE.md §8](docs/ARCHITECTURE.md#8-repository--folder-structure).

## Local Setup
**Prerequisites:** Python 3.11, Node.js 22, Docker Desktop (for Kafka).

**Option A — backend in Docker, frontend native (closest to the real architecture)**
```bash
docker compose up -d --build            # Kafka (KRaft) + meeting-service :8000 + ai-service :8001
cd frontend && npm install && cp .env.example .env.local && npm run dev   # http://localhost:3000
```

**Option B — everything native (fast iteration)**
```bash
docker compose up -d kafka              # or set PROCESSING_MODE=inline-test in the Meeting Service .env to skip Kafka

cd backend/meeting-service
python -m venv .venv && source .venv/Scripts/activate      # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt && cp .env.example .env
uvicorn app.main:create_app --factory --reload --port 8000  # http://localhost:8000/docs

cd ../ai-service                          # second terminal
python -m venv .venv && source .venv/Scripts/activate
pip install -r requirements-dev.txt && cp .env.example .env
uvicorn app.main:create_app --factory --reload --port 8001

cd ../../frontend                         # third terminal
npm install && cp .env.example .env.local && npm run dev
```
Health checks: `GET :8000/health`, `GET :8000/health/ready` (database), `GET :8001/health`.

## Environment Variables
Each deployable reads its own environment (12-factor); every variable is documented in its `.env.example`.
Real `.env` files are git-ignored.

| File | Key variables |
|------|---------------|
| [backend/meeting-service/.env.example](backend/meeting-service/.env.example) | `DATABASE_URL`, `CORS_ORIGINS`, `PROCESSING_MODE` (`kafka` \| `http` \| `inline-test`), `KAFKA_*`, `AI_SERVICE_URL`, `INTERNAL_API_TOKEN` |
| [backend/ai-service/.env.example](backend/ai-service/.env.example) | `PROCESSING_MODE` (`kafka` \| `http`), `KAFKA_*`, `INTERNAL_API_TOKEN`, `SUMMARY_PROVIDER` (`mock` \| `llm`), `LLM_API_KEY` |
| [frontend/.env.example](frontend/.env.example) | `NEXT_PUBLIC_API_URL` |

`PROCESSING_MODE=http` and `SUMMARY_PROVIDER=llm` refuse to start without their secret — misconfiguration fails fast.

## Seed Data
Seven meetings at a fictional company (Northwind, makers of a route-planning product): product sync, sprint review,
client discovery call, design review, hiring debrief, marketing strategy and Q1 planning. Each has 3–5 participants
drawn from 11 recurring people, a full timestamped transcript, an overview, keywords, a chaptered outline and action
items. Dates are relative to today so the date filters always have something to show.
```bash
cd backend/meeting-service && python -m app.seed          # skips if data exists; --reset wipes and reseeds
```
Docker / deployments can set `SEED_ON_STARTUP=true` to seed an empty database automatically.

## Testing
```bash
cd backend/meeting-service && pytest --cov     # + `pytest -m kafka` with Kafka running
cd backend/ai-service      && pytest --cov
cd frontend && npm test && npm run build && npm run test:e2e
```
Strategy: [docs/TESTING.md](docs/TESTING.md). Requirement → test mapping:
[docs/TEST_COVERAGE_MATRIX.md](docs/TEST_COVERAGE_MATRIX.md).

## Coverage
Figures are copied from generated reports only. End of Phase 2 (scaffolding only): meeting-service 98 %,
ai-service 99 % (line + branch). CI fails below 90 %. Details: [docs/TESTING.md](docs/TESTING.md).

## CI/CD
[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on pull requests and pushes to `main`: backend
lint/format/strict types/tests + 90 % coverage gate (both services), event-contract check, a real-Kafka job, and frontend
lint/format/types/unit/build/E2E smoke. See [docs/CI_CD.md](docs/CI_CD.md).

## Deployment
_(pending — Phase 18)_ Free-first options and verification checklist: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Assumptions
- Single default logged-in user; no authentication (explicitly allowed by the assignment).
- One shared workspace: a participant's display name identifies them (case-insensitive) when transcripts are uploaded.
- Transcripts are text inputs; there is no real audio. The player uses a simulated playback clock with real controls.
- AI notes come from a deterministic mock provider by default; an LLM provider is optional and off unless configured.
- Ambiguous assignment wording and how we interpreted it: [docs/REQUIREMENTS_MATRIX.md §13](docs/REQUIREMENTS_MATRIX.md#13-interpretations-of-ambiguous-wording-decided-documented-revisitable).

## Out of Scope
Live meeting bot · real speech-to-text · Zoom/Meet/calendar/CRM integrations · team sharing · real authentication —
each shown as a "Coming soon" placeholder.

## Bonus Features
See [docs/BONUS_FEATURES.md](docs/BONUS_FEATURES.md).

## Design Trade-offs
See [docs/TRADEOFFS.md](docs/TRADEOFFS.md) and [docs/adr/](docs/adr/).

## Known Limitations
- SQLite allows one writer, so the Meeting Service runs as a single instance.
- Free hosting may not run Kafka; the hosted demo may use the documented HTTP processing mode.
_(maintained as implementation progresses)_

## Future Improvements
_(maintained as implementation progresses)_

## Screenshots
_(pending — Phase 16)_
