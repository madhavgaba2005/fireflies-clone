from app.events.envelope import EventEnvelope, EventType
from app.events.payloads import (
    ProcessingRequestPayload,
    SummaryFailedPayload,
    SummaryGeneratedPayload,
)
from app.processors.meeting_processor import MeetingProcessor
from app.providers.base import ProviderError
from app.providers.mock import MockSummaryProvider
from tests.conftest import request_event, request_payload


class FlakyProvider:
    name = "flaky"

    def __init__(self, failures: int, error: Exception | None = None) -> None:
        self.failures = failures
        self.calls = 0
        self.error = error or RuntimeError("model timeout")

    def generate(self, request: ProcessingRequestPayload) -> SummaryGeneratedPayload:
        self.calls += 1
        if self.calls <= self.failures:
            raise self.error
        return MockSummaryProvider().generate(request)


def make(provider: object, retries: int = 3) -> tuple[MeetingProcessor, list[float]]:
    delays: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        delays.append(seconds)

    return MeetingProcessor(provider, max_retries=retries, sleep=fake_sleep), delays  # type: ignore[arg-type]


async def test_success_produces_summary_generated_for_same_meeting() -> None:
    processor, delays = make(MockSummaryProvider())
    result = await processor.process(request_event())
    assert result.event_type == EventType.SUMMARY_GENERATED
    assert result.aggregate_id == "42"
    payload = SummaryGeneratedPayload.model_validate(result.payload)
    assert payload.transcript_revision == 3 and payload.topics
    assert delays == []


async def test_transient_failures_are_retried_with_exponential_backoff() -> None:
    provider = FlakyProvider(failures=2)
    processor, delays = make(provider)
    result = await processor.process(request_event())
    assert result.event_type == EventType.SUMMARY_GENERATED
    assert provider.calls == 3 and delays == [1.0, 2.0]


async def test_exhausted_retries_produce_summary_failed() -> None:
    provider = FlakyProvider(failures=99)
    processor, delays = make(provider, retries=3)
    result = await processor.process(request_event())
    assert result.event_type == EventType.SUMMARY_FAILED
    failed = SummaryFailedPayload.model_validate(result.payload)
    assert failed.attempts == 3 and failed.transcript_revision == 3
    assert "RuntimeError: model timeout" in failed.reason
    assert delays == [1.0, 2.0]


async def test_non_retryable_errors_fail_immediately() -> None:
    provider = FlakyProvider(failures=99, error=ProviderError("empty", retryable=False))
    processor, delays = make(provider)
    result = await processor.process(request_event())
    assert result.event_type == EventType.SUMMARY_FAILED
    assert provider.calls == 1 and delays == []


async def test_retryable_provider_error_is_retried() -> None:
    provider = FlakyProvider(failures=1, error=ProviderError("rate limited"))
    processor, _ = make(provider)
    assert (await processor.process(request_event())).event_type == EventType.SUMMARY_GENERATED


async def test_invalid_request_payload_fails_without_calling_the_provider() -> None:
    provider = FlakyProvider(failures=0)
    processor, _ = make(provider)
    event = EventEnvelope(
        event_type=EventType.MEETING_CREATED, aggregate_id="42", payload={"transcript_revision": 7}
    )
    result = await processor.process(event)
    assert result.event_type == EventType.SUMMARY_FAILED
    assert SummaryFailedPayload.model_validate(result.payload).transcript_revision == 7
    assert provider.calls == 0


async def test_failed_result_for_non_numeric_aggregate_and_missing_revision() -> None:
    processor, _ = make(MockSummaryProvider())
    event = EventEnvelope(event_type=EventType.SUMMARY_REQUESTED, aggregate_id="abc", payload={})
    failed = SummaryFailedPayload.model_validate((await processor.process(event)).payload)
    assert (failed.meeting_id, failed.transcript_revision) == (0, -1)


async def test_max_retries_below_one_still_tries_once() -> None:
    processor, _ = make(MockSummaryProvider(), retries=0)
    payload = request_payload()
    result = await processor.process(request_event(payload))
    assert result.event_type == EventType.SUMMARY_GENERATED
