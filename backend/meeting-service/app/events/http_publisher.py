"""HTTP transport — documented FALLBACK for hosts that cannot run a Kafka broker.

Sends the same envelope to the AI service's internal endpoint and hands the returned result
envelope to the same handler the Kafka consumer uses. Kafka remains the reference transport.
"""

import httpx

from app.events.envelope import EventEnvelope
from app.events.publisher import ResultHandler

PROCESS_PATH = "/internal/process"
TOKEN_HEADER = "X-Internal-Token"


class HttpEventPublisher:
    def __init__(
        self,
        base_url: str,
        token: str,
        on_result: ResultHandler,
        client: httpx.AsyncClient | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._base_url = base_url
        self._token = token
        self._on_result = on_result
        self._client = client
        self._timeout = timeout_seconds

    async def start(self) -> None:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout)

    async def stop(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def publish(self, event: EventEnvelope) -> None:
        if self._client is None:
            raise RuntimeError("HttpEventPublisher.publish() called before start()")
        response = await self._client.post(
            PROCESS_PATH,
            content=event.to_bytes(),
            headers={"Content-Type": "application/json", TOKEN_HEADER: self._token},
        )
        # Non-2xx raises → the outbox row stays unpublished and the relay retries later.
        response.raise_for_status()
        await self._on_result(EventEnvelope.from_bytes(response.content))
