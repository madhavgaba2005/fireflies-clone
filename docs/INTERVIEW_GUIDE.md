# Interview Guide

> Status: **Skeleton (Phase 1)** — answers are completed in Phase 20 so they can cite real files and real test names.
> Format per question: **30-second answer · Deeper answer · Trade-off · Likely follow-up.**
> Short versions of most answers already exist in [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) and the [ADRs](adr/).

## Questions

### Technology choices
1. Why Next.js? — [ADR-001](adr/001-use-nextjs.md)
2. Why TypeScript?
3. Why FastAPI? — [ADR-002](adr/002-use-fastapi.md)
4. Why SQLite? — [ADR-003](adr/003-use-sqlite.md)
5. Why SQLAlchemy?

### Backend design
6. Why the repository pattern? — [ADR-006](adr/006-service-repository-layer.md)
7. Why a service layer?
8. How is the schema normalized? Why a many-to-many for participants? — [DATABASE_DESIGN.md](DATABASE_DESIGN.md)

### Architecture
9. Why microservices? — [ADR-004](adr/004-two-service-architecture.md)
10. Why only two services?
11. Why Kafka? — [ADR-005](adr/005-use-kafka-for-async-processing.md)
12. Why not Kafka for CRUD? *(answered below)*
13. Why asynchronous processing?
14. How is eventual consistency handled?
15. What if Kafka is down? — [ADR-008](adr/008-transactional-outbox.md)
16. How do you prevent duplicate events?
17. What happens if AI processing fails?
18. How would retry work?

### Frontend
19. How does transcript synchronization work?
20. Why simulated audio?

### AI
21. Why mock AI? — [ADR-007](adr/007-mock-summary-provider.md)
22. How would you add a real LLM?

### Scaling, security, operations
23. How would you scale the system?
24. How would you migrate from SQLite?
25. How would you introduce authentication?
26. How would you secure the APIs?
27. How would search scale?
28. How does CI work?
29. Why this Git branching strategy?

---

## Answers

### 12. Why not Kafka for CRUD?
- **30 s:** CRUD is a request the user waits on and must immediately see reflected. One SQLite transaction already gives that. Kafka would add latency and eventual consistency for no benefit.
- **Deeper:** Kafka shines for work that is slow, retryable and can complete later — summary generation. Renaming a meeting or ticking an action item needs read-your-own-writes; routing it through a broker means the response can't confirm the write happened, the UI would need reconciliation, and failure modes multiply.
- **Trade-off:** If many downstream systems needed to react to edits (search index, analytics), we would *also* emit events via the same outbox — but the write itself stays synchronous.
- **Follow-up:** "So how do other services learn about edits?" → outbox events such as `transcript.updated`, published after commit.

*(Remaining answers: Phase 20.)*
