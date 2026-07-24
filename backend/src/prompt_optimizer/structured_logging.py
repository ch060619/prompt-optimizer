from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from prompt_optimizer.public import sanitize_secret_text

# RC ID: RC-215. Keep structured logs correlated and content-free by default.

LogLevel = Literal["debug", "info", "warning", "error"]
type LogValue = str | int | float | bool | None

SAFE_METADATA_FIELDS = frozenset(
    {
        "action",
        "approval_id",
        "budget_blocked",
        "component",
        "decision",
        "duration_ms",
        "error_category",
        "error_code",
        "estimated_cost",
        "estimated_input_tokens",
        "estimated_output_tokens",
        "execution_location",
        "fallback_used",
        "latency_ms",
        "model",
        "permission_mode",
        "phase",
        "policy",
        "provider",
        "provider_request_id",
        "reason_code",
        "remote",
        "retryable",
        "scope",
        "status",
    }
)


class StructuredLogEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["v1"] = "v1"
    timestamp: datetime
    level: LogLevel
    event: str = Field(min_length=1, max_length=64, pattern=r"^[a-z][a-z0-9_.-]*$")
    request_id: str | None = None
    session_id: str | None = None
    tool_id: str | None = None
    task_id: str | None = None
    status: str | None = None
    metadata: dict[str, LogValue] = Field(default_factory=dict)
    redacted_fields: tuple[str, ...] = ()

    def to_json(self) -> str:
        return self.model_dump_json(exclude_none=False)


class StructuredLogEmitter:
    def __init__(
        self,
        sink: Callable[[str], None] | None = None,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.sink = sink
        self._clock = clock or (lambda: datetime.now(UTC))

    def emit(
        self,
        event: str,
        *,
        level: LogLevel = "info",
        request_id: str | None = None,
        session_id: str | None = None,
        tool_id: str | None = None,
        task_id: str | None = None,
        status: str | None = None,
        fields: Mapping[str, object] | None = None,
    ) -> StructuredLogEvent:
        metadata, redacted_fields = _redact_fields(fields or {})
        event_model = StructuredLogEvent(
            timestamp=_utc(self._clock()),
            level=level,
            event=event,
            request_id=_id_or_none(request_id, "request_id"),
            session_id=_id_or_none(session_id, "session_id"),
            tool_id=_id_or_none(tool_id, "tool_id"),
            task_id=_id_or_none(task_id, "task_id"),
            status=_safe_status(status),
            metadata=metadata,
            redacted_fields=redacted_fields,
        )
        if self.sink is not None:
            self.sink(event_model.to_json())
        return event_model


def redact_fields(fields: Mapping[str, object]) -> tuple[dict[str, LogValue], tuple[str, ...]]:
    """Return allowlisted metadata and names of fields omitted from the event."""
    return _redact_fields(fields)


def _redact_fields(fields: Mapping[str, object]) -> tuple[dict[str, LogValue], tuple[str, ...]]:
    metadata: dict[str, LogValue] = {}
    redacted: list[str] = []
    for raw_key, value in fields.items():
        key = str(raw_key)
        if key not in SAFE_METADATA_FIELDS:
            redacted.append(key[:64])
            continue
        if isinstance(value, str):
            metadata[key] = sanitize_secret_text(value[:240])
        elif isinstance(value, (bool, int, float)) or value is None:
            metadata[key] = value
        else:
            redacted.append(key)
    return metadata, tuple(sorted(set(redacted)))


def _id_or_none(value: str | None, name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip() or len(value) > 128:
        raise ValueError(f"{name} must be non-empty and at most 128 characters")
    return value.strip()


def _safe_status(value: str | None) -> str | None:
    if value is None:
        return None
    return _id_or_none(value, "status")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def validate_log_json(line: str) -> StructuredLogEvent:
    payload = json.loads(line)
    if not isinstance(payload, dict):
        raise ValueError("structured log must be a JSON object")
    return StructuredLogEvent.model_validate(payload)
