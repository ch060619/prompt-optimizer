from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

# RC IDs: RC-079, RC-180. Keep provider reasoning fields and secrets out of public outputs.


HIDDEN_FIELD_NAMES = frozenset(
    {
        "chainofthought",
        "deliberation",
        "hiddenreasoning",
        "internalreasoning",
        "reasoning",
        "scratchpad",
        "thought",
        "thinking",
    }
)
SENSITIVE_FIELD_NAMES = frozenset(
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
SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(?:api[_ -]?key|access[_ -]?token|authorization|bearer|secret|password|cookie)\b"
    r"\s*[:=]\s*[^\s,;]+"
)
SECRET_FORMATS = (
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{10,}\b", re.IGNORECASE),
    re.compile(r"\bsk-ant-[A-Za-z0-9_-]{10,}\b", re.IGNORECASE),
    re.compile(r"\bAIza[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bxai-[A-Za-z0-9_-]{10,}\b", re.IGNORECASE),
    re.compile(r"\b(?:ghp|gho|ghs|ghu)_[A-Za-z0-9_]{20,}\b", re.IGNORECASE),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b", re.IGNORECASE),
    re.compile(r"\bhf_[A-Za-z0-9_-]{10,}\b", re.IGNORECASE),
    re.compile(r"\br8_[A-Za-z0-9_-]{10,}\b", re.IGNORECASE),
)

PROGRESS_MESSAGES = {
    "started": "Starting response",
    "context": "Preparing context",
    "model": "Preparing response",
    "tool": "Running approved tool",
    "completed": "Response ready",
    "failed": "Response failed",
    "cancelled": "Response cancelled",
}
ALLOWED_USAGE_FIELDS = frozenset({"input_tokens", "output_tokens", "cost", "latency_ms"})


def sanitize_public_payload(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): (
                "[REDACTED]"
                if _normalize_key(str(key)) in SENSITIVE_FIELD_NAMES
                else sanitize_public_payload(item)
            )
            for key, item in value.items()
            if _normalize_key(str(key)) not in HIDDEN_FIELD_NAMES
        }
    if isinstance(value, (list, tuple)):
        return [sanitize_public_payload(item) for item in value]
    if isinstance(value, Enum):
        return sanitize_public_payload(value.value)
    if is_dataclass(value):
        return sanitize_public_payload(asdict(value))  # type: ignore[arg-type]
    if hasattr(value, "model_dump"):
        return sanitize_public_payload(value.model_dump(mode="json"))
    if isinstance(value, str):
        return sanitize_secret_text(value)
    return value


def safe_json_dumps(value: Any) -> str:
    return json.dumps(
        sanitize_public_payload(value),
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )


def public_progress(status: str, *, fallback: str = "Working") -> str:
    return PROGRESS_MESSAGES.get(status.lower(), fallback)


def public_log_event(
    event: str,
    *,
    status: str,
    basis: str | None = None,
    usage: Mapping[str, Any] | None = None,
    raw: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    del raw
    result: dict[str, Any] = {
        "event": event,
        "status": status,
        "progress": public_progress(status),
    }
    if basis:
        result["basis"] = basis[:240]
    if usage:
        result["usage"] = sanitize_public_payload(
            {key: value for key, value in usage.items() if key in ALLOWED_USAGE_FIELDS}
        )
    return result


def _normalize_key(value: str) -> str:
    return value.replace("_", "").replace("-", "").lower()


def sanitize_secret_text(value: str) -> str:
    message = SECRET_ASSIGNMENT.sub("[REDACTED]", value)
    for pattern in SECRET_FORMATS:
        message = pattern.sub("[REDACTED]", message)
    return message
