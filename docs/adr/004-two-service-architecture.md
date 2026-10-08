# ADR-004: Exactly two backend services

**Status:** Accepted (Phase 0)

## Context
We want to show service decomposition without creating services that have no independent reason to exist.

## Decision
**Meeting Service** (system of record: all data + REST) and **AI Processing Service** (stateless transformer: transcript in, notes out). The browser talks only to the Meeting Service.

## Alternatives
- **Monolith:** simplest and fully adequate for the PDF; loses the async-decoupling demonstration.
- **Split per entity (meeting / transcript / action-item services):** these share one transactional boundary (deleting a meeting cascades to all of them), so splitting would require distributed transactions — a classic microservice anti-pattern.
- **API gateway / BFF:** unnecessary with a single public backend.

## Trade-offs
+ The single seam is the one with a real difference in runtime characteristics (latency, failure, scaling, replaceability).
− Two deployables and a broker for a small app.

## Consequences
Data ownership is unambiguous: only the Meeting Service writes SQLite; the AI Service has no database.
