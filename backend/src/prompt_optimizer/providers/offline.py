from __future__ import annotations

from time import perf_counter

from prompt_optimizer.core.optimizer import Optimizer
from prompt_optimizer.providers.base import ModelRequest, ModelResponse


class OfflineRuleProvider:
    name = "offline"

    def __init__(self, optimizer: Optimizer | None = None) -> None:
        self.optimizer = optimizer or Optimizer()

    def optimize(self, request: ModelRequest) -> ModelResponse:
        started = perf_counter()
        analysis = self.optimizer.optimize(request.prompt, request.template)
        latency_ms = int((perf_counter() - started) * 1000)
        return ModelResponse(
            analysis=analysis,
            provider_used=self.name,
            latency_ms=latency_ms,
        )
