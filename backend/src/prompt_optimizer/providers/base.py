from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from prompt_optimizer.core.models import PromptAnalysis, PromptTemplate


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None
    timeout_seconds: float = 20.0
    max_retries: int = 2
    rate_limit_per_minute: int = 30


@dataclass(frozen=True)
class ModelRequest:
    prompt: str
    template: PromptTemplate | None = None


@dataclass(frozen=True)
class ModelResponse:
    analysis: PromptAnalysis
    provider_used: str
    latency_ms: int


class ModelProviderError(RuntimeError):
    pass


class ProviderTimeoutError(ModelProviderError):
    pass


class ProviderRateLimitError(ModelProviderError):
    pass


class ModelProvider(Protocol):
    name: str

    def optimize(self, request: ModelRequest) -> ModelResponse:
        pass
