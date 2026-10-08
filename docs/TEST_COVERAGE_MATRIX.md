# Test Coverage Matrix

Every MUST-have needs ≥ 1 automated verification. **P** = planned, **✓** = test exists and passes. Test file names are filled in as written.

| Req | Requirement | Unit | Integration | E2E | Manual |
|-----|-------------|------|-------------|-----|--------|
| R1.1 | Meeting list fields | | P | P | |
| R1.2 | Title search | P (repo filter) | P | P | |
| R1.3 | Date filter | | P (inclusive bounds, 422 on inverted range) | P | |
| R1.4 | Participant filter | | P | P | |
| R1.5 | Sort by recency | | P | P | |
| R1.6 | Navbar profile/settings | | | P | |
| R2.1 | Transcript with speakers + timestamps | | P (ordering) | P | |
| R2.2 | Player + seek bar | | | P | |
| R2.3 | Transcript → player | | | P | |
| R2.4 | Player → transcript highlight/scroll | P (`findActiveSegmentIndex`) | | P | |
| R2.5 | Transcript search + highlight | P (`splitByQuery`, regex chars) | | P | |
| R3.1 | Overview | P (provider) | P (consumer persists) | P | |
| R3.2 | Action items extracted | P (extraction heuristics) | P | P | |
| R3.3 | Topics / chapters | P | P | P (click chapter seeks) | |
| R3.4 | Async generation for new meetings | | P (memory-bus pipeline) + P (`kafka`) | P | |
| R4.1 | Create via upload | P (txt/vtt/json parsers, malformed) | P (413/415/400) | P | |
| R4.2 | Create via paste | P | P | P | |
| R4.3 | Create via form | | P | P | |
| R4.4 | Edit metadata | P (participant diff, 409 rule) | P | P (+ reload) | |
| R4.5 | Delete meeting | | P (cascade, 404 after) | P (+ reload) | |
| R4.6–4.8 | Action item add / edit / complete | P (`completed_at` rule) | P | P (+ reload) | |
| R4.9 | Persistence | | P (new session reads) | P (reload in every CRUD spec) | |
| R5.1–5.6 | Fireflies experience, modals, toasts, settings | | | P (toast/modal assertions) | P (visual checklist) |
| M1–M5 | Placeholders | | | P | |
| C3/C7 | Schema constraints & migrations | | P (`test_schema.py`, migration up/down) | | |
| X2 | Idempotency & stale results | P | P (duplicate event_id ignored; older revision ignored) | | |
