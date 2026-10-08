# ADR-002: Use FastAPI for both backend services

**Status:** Accepted (Phase 0)

## Context
The PDF allows FastAPI or Django. We need a REST API with strong validation, auto-generated docs, and an async runtime that can host a Kafka consumer/relay alongside HTTP.

## Decision
FastAPI + Pydantic v2 for the Meeting Service and the AI Service.

## Alternatives
- **Django + DRF:** batteries included (admin, ORM, migrations), but heavier; hosting an async Kafka consumer next to its sync ORM is awkward, and much of it (auth, templates, admin) would go unused.
- **Flask:** minimal, but validation and OpenAPI need extra libraries.

## Trade-offs
+ Type-driven validation and OpenAPI for free; lifespan hooks host background tasks; small, explainable code.
− We assemble our own pieces (SQLAlchemy, Alembic) instead of an integrated stack.

## Consequences
Pydantic models are both the API contract and the event contract. SQLAlchemy + Alembic are added explicitly (ADR-003).
