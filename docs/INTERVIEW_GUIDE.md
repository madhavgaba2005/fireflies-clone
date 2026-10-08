# Interview Guide

> Status: **Skeleton (Phase 0)**. Each answer is written once the corresponding code exists, so answers cite real files.
> Format per question: **30-second answer · Detailed answer · Trade-off answer · Likely follow-up.**

## Technology choices
1. Why FastAPI? 2. Why Next.js? 3. Why SQLite? 4. Why Kafka? 5. Why microservices? 6. Why only two services?
7. Why not Kafka for CRUD? 8. Why is the Meeting Service the system of record?

## Architecture & consistency
9. How do you handle eventual consistency? 10. What happens if Kafka is unavailable? 11. How do you prevent duplicate events?
12. How would you implement idempotency? 13. What happens if AI processing fails? 14. How would retries work?

## Backend design
15. Why repository pattern? 16. Why service layer? 17. How is the schema normalized? 18. Why many-to-many participants?

## Frontend
19. How does transcript synchronization work?

## AI
20. Why mocked AI? 21. How would you add a real LLM?

## Scaling & security
22. How would this scale beyond SQLite? 23. How would you migrate to PostgreSQL? 24. How would you scale transcript search?
25. How would you implement authentication? 26. How would you secure the APIs?

---

### Example (filled now because the design is settled)

#### 7. Why not Kafka for CRUD?
- **30 s:** CRUD is a request the user waits on and must immediately see reflected. One SQLite transaction already gives that. Kafka would add latency and eventual consistency for no benefit.
- **Detailed:** Kafka shines for work that is slow, retryable and can complete later — summary generation. Edits to a title or ticking an action item need read-your-own-writes; routing them through a broker means the response can't confirm the write happened, the UI would need reconciliation, and failure modes multiply.
- **Trade-off:** If many downstream systems needed to react to meeting edits (search index, analytics), we'd *also* emit events for them via the same outbox — but the write itself stays synchronous.
- **Follow-up:** "So how do other services learn about edits?" → outbox events like `transcript.updated`, published after commit.
