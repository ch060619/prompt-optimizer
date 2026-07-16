from __future__ import annotations

from collections.abc import Iterator
from time import perf_counter

from prompt_optimizer.core.optimizer import Optimizer
from prompt_optimizer.providers.base import ModelRequest, ModelResponse

# RC ID: RC-050. Describe the offline rules backend without presenting it as a model.


class OfflineRuleProvider:
    name = "offline"
    display_name = "离线规则"
    is_model = False
    network_access = False
    fallback_triggers = (
        "provider_error",
        "provider_timeout",
        "provider_rate_limit",
        "provider_unavailable",
    )

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

    def stream(self, request: ModelRequest) -> Iterator[str]:
        response = self.optimize(request)
        optimized = response.analysis.optimized_prompt or ""
        for start in range(0, len(optimized), 120):
            yield optimized[start : start + 120]
