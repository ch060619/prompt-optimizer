from __future__ import annotations

from collections.abc import Iterator
from time import perf_counter

from prompt_optimizer.contracts import PromptOptimizer
from prompt_optimizer.core.optimizer import Optimizer
from prompt_optimizer.providers.base import (
    ModelRequest,
    ModelResponse,
    ProviderCancelledError,
    ProviderCapabilities,
    ProviderEvent,
    ProviderEventType,
)

# RC ID: RC-050. Describe the offline rules backend without presenting it as a model.
# RC ID: RC-049. Adapt the existing offline stream to the shared Provider events.
# RC ID: RC-154. Apply requested optimization targets through the offline rule provider.
# RC ID: RC-155. Provide the rules-only path and model-failure fallback.


class OfflineRuleProvider:
    name = "offline"
    display_name = "离线规则"
    model = None
    is_model = False
    network_access = False
    execution_location = "local"
    credential_ref = None
    capabilities = ProviderCapabilities(streaming=True)
    fallback_triggers = (
        "provider_error",
        "provider_timeout",
        "provider_rate_limit",
        "provider_unavailable",
    )

    def __init__(self, optimizer: PromptOptimizer | None = None) -> None:
        self.optimizer = optimizer or Optimizer()

    def optimize(self, request: ModelRequest) -> ModelResponse:
        _check_cancelled(request)
        started = perf_counter()
        analysis = self.optimizer.optimize(
            request.prompt,
            request.template,
            request.language_profile,
            request.targets,
            request.protected_structure,
        )
        latency_ms = int((perf_counter() - started) * 1000)
        _check_cancelled(request)
        return ModelResponse(
            analysis=analysis,
            provider_used=self.name,
            latency_ms=latency_ms,
        )

    def stream(self, request: ModelRequest) -> Iterator[ProviderEvent]:
        try:
            response = self.optimize(request)
        except ProviderCancelledError:
            return
        optimized = response.analysis.optimized_prompt or ""
        yield ProviderEvent(ProviderEventType.STARTED)
        for start in range(0, len(optimized), 120):
            _check_cancelled(request)
            yield ProviderEvent(
                ProviderEventType.DELTA,
                text=optimized[start : start + 120],
            )
        yield ProviderEvent(ProviderEventType.COMPLETED)


def _check_cancelled(request: ModelRequest) -> None:
    if request.cancel_event is not None and request.cancel_event.is_set():
        raise ProviderCancelledError("优化请求已取消。")
