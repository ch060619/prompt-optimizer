"""A deterministic Provider-shaped adapter; it never opens a network connection."""

from __future__ import annotations

from collections.abc import Iterator

from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.providers.base import (
    ModelRequest,
    ModelResponse,
    ProviderCapabilities,
    ProviderEvent,
    ProviderEventType,
)


class ExampleAdapter:
    name = "example-local"
    capabilities = ProviderCapabilities(text=True, streaming=True)

    def __init__(self) -> None:
        self._analyzer = Analyzer()

    def optimize(self, request: ModelRequest) -> ModelResponse:
        analysis = self._analyzer.analyze(request.prompt)
        return ModelResponse(analysis, self.name, latency_ms=0)

    def stream(self, request: ModelRequest) -> Iterator[ProviderEvent]:
        analysis = self.optimize(request)
        yield ProviderEvent(ProviderEventType.STARTED)
        yield ProviderEvent(ProviderEventType.DELTA, text=analysis.analysis.optimized_prompt)
        yield ProviderEvent(ProviderEventType.COMPLETED)
