import pytest

from app.events.payloads import ProcessingRequestPayload
from app.providers.base import ProviderError
from app.providers.mock import MockSummaryProvider, best_sentence, chapters, keywords
from tests.conftest import LINES, request_payload


def generate(lines: list[tuple[str, str]] = LINES) -> object:
    return MockSummaryProvider().generate(
        ProcessingRequestPayload.model_validate(request_payload(lines))
    )


def request() -> ProcessingRequestPayload:
    return ProcessingRequestPayload.model_validate(request_payload())


def test_output_is_deterministic_and_echoes_identity() -> None:
    first = MockSummaryProvider().generate(request())
    assert first == MockSummaryProvider().generate(request())
    assert (first.meeting_id, first.transcript_revision, first.provider) == (42, 3, "mock")


def test_keywords_are_frequent_meaningful_words_without_names() -> None:
    result = MockSummaryProvider().generate(request())
    assert result.keywords[:3] == ["Pricing", "Onboarding", "Checkout"]
    lowered = {k.lower() for k in result.keywords}
    assert not lowered & {"priya", "arjun", "sarah", "sharma", "the", "today", "sure"}


def test_keywords_rank_ties_by_first_appearance() -> None:
    segments = request().segments
    assert keywords(segments[:1], 2) == ["Morning", "Review"]


def test_chapters_start_at_their_first_segment_and_quote_substantial_sentences() -> None:
    segments = request().segments
    topics = chapters(segments)
    assert topics[0].start_ms == 0
    assert all(t.start_ms is not None for t in topics)
    assert [t.start_ms for t in topics] == sorted(t.start_ms or 0 for t in topics)
    assert all(t.summary != "Sure." for t in topics)


def test_best_sentence_ignores_short_replies() -> None:
    segments = request().segments
    assert (
        best_sentence(segments[-2:], ["pricing"])
        == "We need to announce the pricing change by next week."
    )


def test_overview_names_people_title_and_topics() -> None:
    result = MockSummaryProvider().generate(request())
    assert result.overview.startswith(
        "Priya Sharma, Arjun Mehta and Sarah Chen met for “Pricing launch sync”."
    )
    assert "Key point:" in result.overview


def test_action_items_detect_commitments_requests_and_deadlines() -> None:
    items = MockSummaryProvider().generate(request()).action_items
    by_title = {i.title: i.assignee_speaker_id for i in items}
    assert by_title == {
        "Fix the checkout integration before Friday": 2,  # "Arjun, can you …" → Arjun
        "Fix the annual plan checkout and add tests for it": 2,  # "I'll …" → speaker
        "Share the onboarding illustrations with the team tomorrow": 3,
        "Announce the pricing change by next week": None,  # team commitment with a deadline
    }
    assert items[0].start_ms == 20_000


def test_action_items_skip_vague_statements() -> None:
    lines = [
        ("Priya Sharma", "Let's keep this short."),  # no deadline
        ("Arjun Mehta", "I'll explain in a minute."),  # not a task
        ("Sarah Chen", "I'll share my screen now."),
        ("Priya Sharma", "Can you start with the numbers?"),
        ("Arjun Mehta", "I'll do it."),  # too short to be useful
    ]
    assert (
        MockSummaryProvider()
        .generate(ProcessingRequestPayload.model_validate(request_payload(lines)))
        .action_items
        == []
    )


def test_duplicate_commitments_are_listed_once() -> None:
    lines = [
        ("Arjun Mehta", "I'll update the roadmap doc."),
        ("Arjun Mehta", "I'll update the roadmap doc."),
    ]
    result = MockSummaryProvider().generate(
        ProcessingRequestPayload.model_validate(request_payload(lines))
    )
    assert len(result.action_items) == 1


def test_single_speaker_and_short_transcript() -> None:
    lines = [("Priya Sharma", "Quick note to self about the analytics dashboard.")]
    result = MockSummaryProvider().generate(
        ProcessingRequestPayload.model_validate(request_payload(lines))
    )
    assert result.overview.startswith("Priya Sharma met for")
    assert len(result.topics) == 1


def test_empty_transcript_is_a_non_retryable_error() -> None:
    payload = request_payload([("Priya Sharma", "   ")])
    with pytest.raises(ProviderError) as error:
        MockSummaryProvider().generate(ProcessingRequestPayload.model_validate(payload))
    assert error.value.retryable is False
