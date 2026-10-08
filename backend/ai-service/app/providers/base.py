"""The SummaryProvider interface. Adding a real LLM = one new class + one line in build_provider."""

from typing import Protocol

from app.events.payloads import ProcessingRequestPayload, SummaryGeneratedPayload


class ProviderError(Exception):
    """Generation failed. `retryable=False` means retrying can't help (e.g. empty transcript)."""

    def __init__(self, message: str, *, retryable: bool = True) -> None:
        super().__init__(message)
        self.retryable = retryable


class SummaryProvider(Protocol):
    name: str

    def generate(self, request: ProcessingRequestPayload) -> SummaryGeneratedPayload: ...
