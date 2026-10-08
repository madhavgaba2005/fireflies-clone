# ADR-006: Pluggable SummaryProvider with a deterministic mock default

**Status:** Accepted (Phase 0)

## Context
The PDF allows seeded, mocked or LLM summaries. The deployed demo must work with no API key and no cost, and tests need deterministic output.

## Decision
A `SummaryProvider` protocol (`generate(transcript) -> SummaryResult`).
`MockSummaryProvider` (default) uses transparent heuristics: chapters from time windows + speaker turns, keywords from term frequency minus stop-words, overview from the leading sentences of each chapter, action items from commitment phrases ("I'll…", "can you…", "by Friday").
`LLMSummaryProvider` is selected only when `SUMMARY_PROVIDER=llm` and an API key is set.

## Alternatives
- **Always LLM:** best quality, but needs a key, costs money, makes tests non-deterministic, and the demo can break.
- **Static canned summaries:** trivial, but new uploads would get irrelevant text.

## Trade-offs
+ Works offline, deterministic, explainable; a real provider is a drop-in.
− Heuristic summaries are visibly simpler than an LLM's.

## Consequences
Seeded meetings carry hand-written, realistic summaries; uploaded meetings use the mock heuristics.
