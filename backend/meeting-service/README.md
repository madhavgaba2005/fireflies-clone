# Meeting Service

System of record. Layers: `routers → services → repositories → SQLAlchemy → SQLite`, plus `events/`
(envelope, publishers, outbox relay, result consumer). Planned layout:
[docs/ARCHITECTURE.md §8](../../docs/ARCHITECTURE.md#8-repository--folder-structure). Scaffolded in Phase 2.
