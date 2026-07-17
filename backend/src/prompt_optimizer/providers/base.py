from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from prompt_optimizer.core.models import PromptAnalysis, PromptTemplate

# RC ID: RC-049. Define the shared Provider protocol, capabilities, and events.


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


@dataclass(frozen=True)
class ProviderCapabilities:
    text: bool = True
    streaming: bool = False
    image: bool = False
    tools: bool = False
    structured_output: bool = False
    context_length: int | None = None
    model_listing: bool = False
    token_usage: bool = False
    cost_info: bool = False


class ProviderEventType(StrEnum):
    STARTED = "started"
    DELTA = "delta"
    COMPLETED = "completed"


@dataclass(frozen=True)
class ProviderEvent:
    type: ProviderEventType
    text: str | None = None


class ModelProviderError(RuntimeError):
    pass


class ProviderTimeoutError(ModelProviderError):
    pass


class ProviderRateLimitError(ModelProviderError):
    pass


@runtime_checkable
class ModelProvider(Protocol):
    name: str
    capabilities: ProviderCapabilities

    def optimize(self, request: ModelRequest) -> ModelResponse:
        pass

    def stream(self, request: ModelRequest) -> Iterator[ProviderEvent]:
        pass
