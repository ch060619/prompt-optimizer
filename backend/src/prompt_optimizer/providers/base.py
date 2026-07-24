from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from enum import StrEnum
from threading import Event
from typing import Any, Literal, Protocol, runtime_checkable

import httpx

from prompt_optimizer.core.language import LanguageProfile
from prompt_optimizer.core.models import (
    OptimizationSuggestion,
    OptimizationTargets,
    PromptAnalysis,
    PromptTemplate,
)
from prompt_optimizer.core.structure import StructuredPrompt
from prompt_optimizer.prompts.system import SYSTEM_PROMPT, SYSTEM_PROMPT_VERSION

# RC IDs: RC-049, RC-154, RC-155, RC-160, RC-161, RC-162, RC-163, RC-166.
# Define the shared Provider protocol,
# capabilities, and request context.


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None
    organization: str | None = None
    project: str | None = None
    api_protocol: Literal[
        "chat_completions",
        "responses",
        "gemini",
        "anthropic",
        "azure_openai",
        "vertex",
        "bedrock",
    ] = "chat_completions"
    api_version: str | None = None
    beta_features: tuple[str, ...] = ()
    prompt_caching: bool = False
    region: str | None = None
    deployment: str | None = None
    project_id: str | None = None
    credential_mode: Literal["api_key", "bearer", "aws_sigv4"] = "api_key"
    custom_headers: tuple[tuple[str, str], ...] = ()
    proxy_url: str | None = None
    no_proxy: tuple[str, ...] = ()
    ca_bundle: str | None = None
    ip_version: Literal["any", "ipv4", "ipv6"] = "any"
    proxy_credential_ref: str | None = None
    input_cost_per_1k_tokens: float = 0.0
    output_cost_per_1k_tokens: float = 0.0
    output_token_reserve: int = 256
    timeout_seconds: float = 20.0
    max_retries: int = 2
    rate_limit_per_minute: int = 30
    authorized: bool = True
    circuit_failure_threshold: int = 3
    circuit_reset_seconds: float = 30.0


@dataclass(frozen=True)
class ModelRequest:
    prompt: str
    protected_structure: StructuredPrompt | None = None
    template: PromptTemplate | None = None
    language_profile: LanguageProfile | None = None
    language_instruction: str | None = None
    request_id: str | None = None
    cancel_event: Event | None = None
    system_prompt: str = SYSTEM_PROMPT
    system_prompt_version: str = SYSTEM_PROMPT_VERSION
    targets: OptimizationTargets | None = None
    strategy: Literal["rules", "model", "combined"] = "combined"
    rule_suggestions: tuple[OptimizationSuggestion, ...] = ()
    tools: tuple[dict[str, Any], ...] = ()
    tool_choice: str | dict[str, Any] | None = None
    response_format: dict[str, Any] | None = None
    safety_settings: tuple[dict[str, Any], ...] = ()
    tool_results: tuple[dict[str, Any], ...] = ()
    cache_prompt: bool = False


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: str


@dataclass(frozen=True)
class ModelResponse:
    analysis: PromptAnalysis
    provider_used: str
    latency_ms: int
    tool_calls: tuple[ToolCall, ...] = ()
    usage: dict[str, int] | None = None


@dataclass(frozen=True)
class ProviderCapabilities:
    text: bool = True
    streaming: bool = False
    image: bool = False
    tools: bool = False
    structured_output: bool = False
    reasoning: bool = False
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
    tool_calls: tuple[ToolCall, ...] = ()


class ModelProviderError(RuntimeError):
    category = "server"

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        request_id: str | None = None,
        retryable: bool | None = None,
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.request_id = sanitize_provider_request_id(request_id)
        self.retry_after_seconds = retry_after_seconds
        self.retryable = retryable if retryable is not None else self.category in {
            "rate_limit",
            "network",
            "timeout",
            "server",
        }


class ProviderErrorCategory(StrEnum):
    AUTH = "auth"
    BALANCE = "balance"
    RATE_LIMIT = "rate_limit"
    REGION = "region"
    MODEL = "model"
    PARAMETER = "parameter"
    FILTER = "filter"
    NETWORK = "network"
    TIMEOUT = "timeout"
    SERVER = "server"
    CANCELLED = "cancelled"


_SAFE_REQUEST_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}")
_SECRET_VALUE = re.compile(
    r"(?i)\b(?:api[_ -]?key|access[_ -]?token|bearer|secret|password)\b\s*[:=]\s*[^\s,;]+"
)


def sanitize_provider_request_id(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    return candidate if _SAFE_REQUEST_ID.fullmatch(candidate) else None


def _provider_error_body(response: httpx.Response) -> tuple[str, str]:
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        return "", ""
    error = payload.get("error")
    if isinstance(error, dict):
        code = error.get("code") or error.get("type") or error.get("status")
        message = error.get("message") or error.get("detail")
        return str(code or ""), str(message or "")
    code = payload.get("code") or payload.get("type") or payload.get("status")
    message = payload.get("message") or payload.get("detail")
    return str(code or ""), str(message or "")


def _retry_after_seconds(response: httpx.Response) -> float | None:
    value = response.headers.get("Retry-After")
    if value is None:
        return None
    try:
        seconds = float(value.strip())
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError):
            return None
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=UTC)
        seconds = (retry_at - datetime.now(UTC)).total_seconds()
    return max(0.0, min(seconds, 300.0))


def _provider_error_category(
    status_code: int,
    code: str,
    message: str,
) -> ProviderErrorCategory:
    signal = f"{code} {message}".lower()
    if any(token in signal for token in ("region", "location", "country", "geo")):
        return ProviderErrorCategory.REGION
    if any(
        token in signal
        for token in (
            "content_filter",
            "content filter",
            "safety",
            "harm",
            "blocked",
            "policy",
        )
    ):
        return ProviderErrorCategory.FILTER
    if status_code == 402 or any(
        token in signal
        for token in ("insufficient_quota", "billing", "credit", "balance", "payment", "quota")
    ):
        return ProviderErrorCategory.BALANCE
    if status_code in {401, 403} or any(
        token in signal
        for token in ("authentication", "unauthorized", "invalid_api_key", "api key", "permission")
    ):
        return ProviderErrorCategory.AUTH
    if status_code == 429 or any(
        token in signal for token in ("rate_limit", "rate limit", "too many requests")
    ):
        return ProviderErrorCategory.RATE_LIMIT
    if status_code == 404 or any(
        token in signal
        for token in ("model_not_found", "model does not exist", "unknown model", "model not found")
    ):
        return ProviderErrorCategory.MODEL
    if status_code in {400, 409, 413, 422} or any(
        token in signal
        for token in (
            "invalid_request",
            "invalid parameter",
            "unsupported parameter",
            "invalid argument",
            "context length",
        )
    ):
        return ProviderErrorCategory.PARAMETER
    if status_code in {408, 504, 524}:
        return ProviderErrorCategory.TIMEOUT
    if status_code >= 500:
        return ProviderErrorCategory.SERVER
    return ProviderErrorCategory.SERVER


_ERROR_CLASS_BY_CATEGORY: dict[ProviderErrorCategory, type[ModelProviderError]] = {}


def raise_provider_http_error(response: httpx.Response, provider_name: str) -> None:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        code, message = _provider_error_body(response)
        category = _provider_error_category(response.status_code, code, message)
        error_class = _ERROR_CLASS_BY_CATEGORY[category]
        detail = _SECRET_VALUE.sub("[REDACTED]", message).strip()[:240]
        if not detail:
            detail = f"{provider_name} request failed."
        raise error_class(
            detail,
            status_code=response.status_code,
            request_id=(
                response.headers.get("x-request-id")
                or response.headers.get("request-id")
                or response.headers.get("x-amzn-requestid")
            ),
            retry_after_seconds=_retry_after_seconds(response),
        ) from exc


class ProviderTimeoutError(ModelProviderError):
    category = ProviderErrorCategory.TIMEOUT


class ProviderRateLimitError(ModelProviderError):
    category = ProviderErrorCategory.RATE_LIMIT


class ProviderUnauthorizedError(ModelProviderError):
    category = ProviderErrorCategory.AUTH


class ProviderBalanceError(ModelProviderError):
    category = ProviderErrorCategory.BALANCE


class ProviderRegionError(ModelProviderError):
    category = ProviderErrorCategory.REGION


class ProviderModelError(ModelProviderError):
    category = ProviderErrorCategory.MODEL


class ProviderParameterError(ModelProviderError):
    category = ProviderErrorCategory.PARAMETER


class ProviderBudgetExceededError(ModelProviderError):
    category = ProviderErrorCategory.PARAMETER

    def __init__(
        self,
        message: str,
        *,
        estimated_tokens: int,
        estimated_cost: float,
        limit: str,
    ) -> None:
        super().__init__(message, retryable=False)
        self.estimated_tokens = estimated_tokens
        self.estimated_cost = estimated_cost
        self.limit = limit


class ProviderContentFilterError(ModelProviderError):
    category = ProviderErrorCategory.FILTER


class ProviderNetworkError(ModelProviderError):
    category = ProviderErrorCategory.NETWORK


class ProviderProxyError(ProviderNetworkError):
    """A network failure caused by the configured HTTP proxy."""


class ProviderServerError(ModelProviderError):
    category = ProviderErrorCategory.SERVER


class ProviderCircuitOpenError(ModelProviderError):
    category = ProviderErrorCategory.NETWORK


class ProviderCancelledError(ModelProviderError):
    category = ProviderErrorCategory.CANCELLED


_ERROR_CLASS_BY_CATEGORY.update(
    {
        ProviderErrorCategory.AUTH: ProviderUnauthorizedError,
        ProviderErrorCategory.BALANCE: ProviderBalanceError,
        ProviderErrorCategory.RATE_LIMIT: ProviderRateLimitError,
        ProviderErrorCategory.REGION: ProviderRegionError,
        ProviderErrorCategory.MODEL: ProviderModelError,
        ProviderErrorCategory.PARAMETER: ProviderParameterError,
        ProviderErrorCategory.FILTER: ProviderContentFilterError,
        ProviderErrorCategory.NETWORK: ProviderNetworkError,
        ProviderErrorCategory.TIMEOUT: ProviderTimeoutError,
        ProviderErrorCategory.SERVER: ProviderServerError,
        ProviderErrorCategory.CANCELLED: ProviderCancelledError,
    }
)


@runtime_checkable
class ModelProvider(Protocol):
    name: str
    capabilities: ProviderCapabilities

    def optimize(self, request: ModelRequest) -> ModelResponse:
        pass

    def stream(self, request: ModelRequest) -> Iterator[ProviderEvent]:
        pass
