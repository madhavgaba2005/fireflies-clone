"""SummaryProvider implementations. Only the deterministic mock exists today — see ADR-007 for how a
real LLM provider plugs in behind the same interface."""

from app.config import Settings
from app.providers.base import ProviderError, SummaryProvider
from app.providers.mock import MockSummaryProvider

__all__ = ["MockSummaryProvider", "ProviderError", "SummaryProvider", "build_provider"]


def build_provider(settings: Settings) -> SummaryProvider:
    # settings.summary_provider is validated to "mock"; an LLM provider would be selected here.
    return MockSummaryProvider()
