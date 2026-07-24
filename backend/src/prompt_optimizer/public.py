from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Literal, cast
from urllib.parse import urlsplit

from prompt_optimizer.core.models import ExecutionDestination, FallbackReason, RecoveryAction
from prompt_optimizer.providers.base import (
    ModelProviderError,
    ProviderBudgetExceededError,
    ProviderCancelledError,
    ProviderCircuitOpenError,
    ProviderErrorCategory,
    ProviderProxyError,
    ProviderRateLimitError,
    ProviderServerError,
    ProviderTimeoutError,
    ProviderUnauthorizedError,
)

# RC IDs: RC-141, RC-180. Keep optimization metadata useful without exposing secrets or prompts.

ExecutionLocation = Literal["local", "cloud"]


def execution_destination(
    provider: Any,
    provider_name: str,
    model: str | None = None,
) -> ExecutionDestination:
    display_name, provider_model, location, _credential_ref = provider_public_metadata(
        provider,
        provider_name,
    )
    selected_model = model or provider_model
    target_host = _target_host(provider) if location == "cloud" else None
    return ExecutionDestination(
        execution_location=location,
        provider=provider_name,
        provider_display_name=display_name,
        model=selected_model,
        target_service=display_name if location == "cloud" else "本机",
        target_host=target_host,
        network_access=location == "cloud",
    )


def declared_execution_destination(
    provider_name: str,
    provider_display_name: str,
    model: str | None,
    execution_location: ExecutionLocation,
) -> ExecutionDestination:
    return ExecutionDestination(
        execution_location=execution_location,
        provider=provider_name,
        provider_display_name=provider_display_name,
        model=model,
        target_service=provider_display_name if execution_location == "cloud" else "本机",
        network_access=execution_location == "cloud",
    )


@dataclass(frozen=True)
class ProviderErrorPresentation:
    category: str
    code: str
    exit_code: int
    recovery_action: str
    http_status: int
    retryable: bool
    request_id: str | None
    message: str


_CATEGORY_CODES = {
    ProviderErrorCategory.AUTH: "PROVIDER_AUTH",
    ProviderErrorCategory.BALANCE: "PROVIDER_BALANCE",
    ProviderErrorCategory.RATE_LIMIT: "PROVIDER_RATE_LIMIT",
    ProviderErrorCategory.REGION: "PROVIDER_REGION",
    ProviderErrorCategory.MODEL: "PROVIDER_MODEL_NOT_FOUND",
    ProviderErrorCategory.PARAMETER: "PROVIDER_PARAMETER",
    ProviderErrorCategory.FILTER: "PROVIDER_CONTENT_FILTER",
    ProviderErrorCategory.NETWORK: "PROVIDER_NETWORK",
    ProviderErrorCategory.TIMEOUT: "PROVIDER_TIMEOUT",
    ProviderErrorCategory.SERVER: "PROVIDER_SERVER",
    ProviderErrorCategory.CANCELLED: "REQUEST_CANCELLED",
}
_CATEGORY_EXIT_CODES = {
    ProviderErrorCategory.AUTH: 10,
    ProviderErrorCategory.BALANCE: 11,
    ProviderErrorCategory.RATE_LIMIT: 12,
    ProviderErrorCategory.REGION: 13,
    ProviderErrorCategory.MODEL: 14,
    ProviderErrorCategory.PARAMETER: 15,
    ProviderErrorCategory.FILTER: 16,
    ProviderErrorCategory.NETWORK: 17,
    ProviderErrorCategory.TIMEOUT: 18,
    ProviderErrorCategory.SERVER: 19,
    ProviderErrorCategory.CANCELLED: 20,
}
_CATEGORY_ACTIONS = {
    ProviderErrorCategory.AUTH: "configure_credentials",
    ProviderErrorCategory.BALANCE: "check_balance",
    ProviderErrorCategory.RATE_LIMIT: "wait_and_retry",
    ProviderErrorCategory.REGION: "change_region",
    ProviderErrorCategory.MODEL: "choose_model",
    ProviderErrorCategory.PARAMETER: "fix_parameters",
    ProviderErrorCategory.FILTER: "review_content",
    ProviderErrorCategory.NETWORK: "check_network",
    ProviderErrorCategory.TIMEOUT: "retry",
    ProviderErrorCategory.SERVER: "retry",
    ProviderErrorCategory.CANCELLED: "cancel",
}
_CATEGORY_HTTP_STATUS = {
    ProviderErrorCategory.AUTH: 401,
    ProviderErrorCategory.BALANCE: 402,
    ProviderErrorCategory.RATE_LIMIT: 429,
    ProviderErrorCategory.REGION: 403,
    ProviderErrorCategory.MODEL: 404,
    ProviderErrorCategory.PARAMETER: 400,
    ProviderErrorCategory.FILTER: 422,
    ProviderErrorCategory.NETWORK: 503,
    ProviderErrorCategory.TIMEOUT: 504,
    ProviderErrorCategory.SERVER: 502,
    ProviderErrorCategory.CANCELLED: 499,
}

_CREDENTIAL_ASSIGNMENT = re.compile(
    r"(?i)\b(?:api[_ -]?key|access[_ -]?token|bearer|secret|password)\b\s*[:=]\s*[^\s,;]+"
)
_BEARER_TOKEN = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
_API_KEY = re.compile(r"\bsk-[A-Za-z0-9_-]{10,}\b")
_PROVIDER_KEY_FORMATS = (
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{10,}\b", re.IGNORECASE),
    re.compile(r"\bsk-ant-[A-Za-z0-9_-]{10,}\b", re.IGNORECASE),
    re.compile(r"\bAIza[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bxai-[A-Za-z0-9_-]{10,}\b", re.IGNORECASE),
    re.compile(r"\b(?:ghp|gho|ghs|ghu)_[A-Za-z0-9_]{20,}\b", re.IGNORECASE),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b", re.IGNORECASE),
    re.compile(r"\bhf_[A-Za-z0-9_-]{10,}\b", re.IGNORECASE),
    re.compile(r"\br8_[A-Za-z0-9_-]{10,}\b", re.IGNORECASE),
)
_SECRET_CANDIDATE = re.compile(r"(?<![A-Za-z0-9])[A-Za-z0-9][A-Za-z0-9._~+/=-]{7,}(?![A-Za-z0-9])")
_INTERNAL_PROMPT = re.compile(
    r"(?i)\b(?:system[_ -]?prompt|developer[_ -]?message|internal prompt)\b"
)


class SecretRedactor:
    """Keep runtime fingerprints, never persisted secret values."""

    def __init__(self) -> None:
        self._fingerprints: set[tuple[int, bytes]] = set()

    def register(self, value: object) -> None:
        if not isinstance(value, str) or len(value) < 8:
            return
        self._fingerprints.add((len(value), hashlib.sha256(value.encode()).digest()))

    def redact_known(self, value: str) -> str:
        def replace(match: re.Match[str]) -> str:
            candidate = match.group(0)
            fingerprint = (len(candidate), hashlib.sha256(candidate.encode()).digest())
            return "[REDACTED]" if fingerprint in self._fingerprints else candidate

        return _SECRET_CANDIDATE.sub(replace, value)


_RUNTIME_SECRET_REDACTOR = SecretRedactor()
_SENSITIVE_FIELD_NAMES = frozenset(
    {
        "apikey",
        "accesstoken",
        "authorization",
        "bearer",
        "cookie",
        "credential",
        "password",
        "secret",
    }
)


def register_runtime_secret(value: object) -> None:
    _RUNTIME_SECRET_REDACTOR.register(value)


def sanitize_secret_text(value: object) -> str:
    message = str(value).strip()
    message = _CREDENTIAL_ASSIGNMENT.sub("[REDACTED]", message)
    message = _BEARER_TOKEN.sub("[REDACTED]", message)
    message = _API_KEY.sub("[REDACTED]", message)
    for pattern in _PROVIDER_KEY_FORMATS:
        message = pattern.sub("[REDACTED]", message)
    return _RUNTIME_SECRET_REDACTOR.redact_known(message)


def sanitize_error_message(value: object) -> str:
    message = str(value).strip()
    if not message:
        return "Provider request failed."
    if _INTERNAL_PROMPT.search(message):
        return "Provider error details were redacted."
    return sanitize_secret_text(message)[:240]


def error_code_for(error: BaseException) -> str:
    local_codes = {
        "not_installed": "LOCAL_MODEL_NOT_INSTALLED",
        "not_ready": "LOCAL_MODEL_NOT_READY",
        "out_of_memory": "LOCAL_MODEL_OUT_OF_MEMORY",
        "timeout": "LOCAL_MODEL_TIMEOUT",
    }
    raw_reason = getattr(error, "fallback_reason", None)
    local_code = local_codes.get(raw_reason) if isinstance(raw_reason, str) else None
    if local_code is not None:
        return local_code
    if isinstance(error, ProviderCancelledError):
        return "REQUEST_CANCELLED"
    if isinstance(error, ProviderBudgetExceededError):
        return "BUDGET_EXCEEDED"
    if isinstance(error, ProviderUnauthorizedError):
        return "PROVIDER_UNAUTHORIZED"
    if isinstance(error, ProviderCircuitOpenError):
        return "PROVIDER_CIRCUIT_OPEN"
    if isinstance(error, ProviderTimeoutError):
        return "PROVIDER_TIMEOUT"
    if isinstance(error, ProviderRateLimitError):
        return "PROVIDER_RATE_LIMIT"
    if isinstance(error, ProviderProxyError):
        return "PROVIDER_PROXY"
    if isinstance(error, ProviderServerError):
        return "PROVIDER_SERVER"
    category = getattr(error, "category", None)
    if isinstance(category, ProviderErrorCategory):
        return _CATEGORY_CODES[category]
    if isinstance(error, ModelProviderError):
        return "PROVIDER_ERROR"
    if isinstance(error, ValueError):
        return "INVALID_PROVIDER_RESPONSE"
    return "PROVIDER_UNAVAILABLE"


def error_category_for(error: BaseException) -> str | None:
    category = getattr(error, "category", None)
    if isinstance(category, ProviderErrorCategory):
        return category.value
    if isinstance(error, ProviderUnauthorizedError):
        return ProviderErrorCategory.AUTH.value
    if isinstance(error, ProviderRateLimitError):
        return ProviderErrorCategory.RATE_LIMIT.value
    if isinstance(error, ProviderTimeoutError):
        return ProviderErrorCategory.TIMEOUT.value
    if isinstance(error, ProviderCancelledError):
        return ProviderErrorCategory.CANCELLED.value
    if isinstance(error, ModelProviderError):
        return ProviderErrorCategory.SERVER.value
    return None


def provider_error_presentation(error: BaseException) -> ProviderErrorPresentation:
    category_value = error_category_for(error) or ProviderErrorCategory.SERVER.value
    category = ProviderErrorCategory(category_value)
    return ProviderErrorPresentation(
        category=category.value,
        code=error_code_for(error),
        exit_code=_CATEGORY_EXIT_CODES[category],
        recovery_action=_CATEGORY_ACTIONS[category],
        http_status=_CATEGORY_HTTP_STATUS[category],
        retryable=bool(getattr(error, "retryable", category in {
            ProviderErrorCategory.RATE_LIMIT,
            ProviderErrorCategory.NETWORK,
            ProviderErrorCategory.TIMEOUT,
            ProviderErrorCategory.SERVER,
        })),
        request_id=getattr(error, "request_id", None),
        message=sanitize_error_message(error),
    )


def fallback_details_for(
    error: BaseException,
) -> tuple[FallbackReason | None, RecoveryAction | None]:
    reason = getattr(error, "fallback_reason", None)
    action = getattr(error, "recovery_action", None)
    if not isinstance(reason, str) or not isinstance(action, str):
        return None, None
    return cast(FallbackReason, reason), cast(RecoveryAction, action)


def provider_public_metadata(
    provider: Any,
    provider_used: str,
) -> tuple[str, str | None, ExecutionLocation, str | None]:
    display_name = str(getattr(provider, "display_name", provider_used))
    model = getattr(provider, "model", None)
    if not isinstance(model, str):
        model = None
    location = getattr(provider, "execution_location", None)
    if location not in {"local", "cloud"}:
        network_access = getattr(provider, "network_access", provider_used != "offline")
        execution_location: ExecutionLocation = "local" if network_access is False else "cloud"
    else:
        execution_location = location
    credential_ref = getattr(provider, "credential_ref", None)
    if not isinstance(credential_ref, str):
        credential_ref = None
    return display_name, model, execution_location, credential_ref


def _target_host(provider: Any) -> str | None:
    config = getattr(provider, "config", None)
    base_url = getattr(config, "base_url", None)
    if not isinstance(base_url, str):
        return None
    try:
        host = urlsplit(base_url).hostname
    except ValueError:
        return None
    return host
