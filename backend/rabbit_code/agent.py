from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum
from threading import Event

from prompt_optimizer.providers.base import ModelProvider, ModelRequest, ProviderEventType

# RC ID: RC-057. Keep the candidate Agent Core independent from API and CLI presentation.


class AgentEventType(StrEnum):
    STARTED = "started"
    DELTA = "delta"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class AgentEvent:
    type: AgentEventType
    text: str | None = None


class AgentCore:
    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    def stream(
        self,
        request: ModelRequest,
        cancellation: Event | None = None,
    ) -> Iterator[AgentEvent]:
        yield AgentEvent(AgentEventType.STARTED)
        if cancellation and cancellation.is_set():
            yield AgentEvent(AgentEventType.CANCELLED)
            return

        for provider_event in self.provider.stream(request):
            if cancellation and cancellation.is_set():
                yield AgentEvent(AgentEventType.CANCELLED)
                return
            if provider_event.type is ProviderEventType.DELTA and provider_event.text:
                yield AgentEvent(AgentEventType.DELTA, text=provider_event.text)
            elif provider_event.type is ProviderEventType.COMPLETED:
                yield AgentEvent(AgentEventType.COMPLETED)
                return
