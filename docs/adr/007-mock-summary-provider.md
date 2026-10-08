# ADR-007: Pluggable SummaryProvider with a deterministic mock default

**Status:** Accepted (Phase 0)

## Context
The PDF allows seeded, mocked or LLM summaries. The deployed demo must work with no API key and no cost, and tests need deterministic output.

## Decision
A `SummaryProvider` protocol (`generate(transcript) -> SummaryResult`).
`MockSummaryProvider` (default) uses transparent heuristics: chapters from time windows + speaker turns, keywords from term frequency minus stop-words, overview from the leading sentences of each chapter, action items from commitment phrases ("I'll…", "can you…", "by Friday").
An LLM provider plugs in behind the same interface (see Implementation notes).

## Alternatives
- **Always LLM:** best quality, but needs a key, costs money, makes tests non-deterministic, and the demo can break.
- **Static canned summaries:** trivial, but new uploads would get irrelevant text.

## Trade-offs
+ Works offline, deterministic, explainable; a real provider is a drop-in.
− Heuristic summaries are visibly simpler than an LLM's.

## Implementation notes (Milestone C)
- `ai-service/app/providers/mock.py`: keywords (stop-words, numbers and participant names removed), chapters (equal
  runs of segments titled by their own keywords, summarized by their most informative sentence), overview, and action
  items from commitment phrases (`I'll …` → speaker, `<Name>, can you …` → that person, `we need to … by Friday` →
  unassigned). Deterministic; 13 unit tests.
- **No LLM provider ships.** `SUMMARY_PROVIDER` only accepts `mock`. An untested, key-dependent provider would be
  decorative code. Adding one = a class implementing `generate(request) -> SummaryGeneratedPayload`, a `Literal`
  value in `config.py`, a branch in `build_provider`, and an API-key setting. The processor already runs providers in
  a worker thread and retries `ProviderError(retryable=True)` (e.g. rate limits) with exponential backoff.

## Consequences
Seeded meetings carry hand-written, realistic summaries; uploaded meetings use the mock heuristics.
