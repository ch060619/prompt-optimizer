from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from prompt_optimizer.structured_logging import (
    StructuredLogEmitter,
    StructuredLogEvent,
    redact_fields,
    validate_log_json,
)

# RC ID: RC-215. Verify schema validation, correlation, and field-level redaction.


def test_structured_logs_correlate_requests_without_sensitive_values() -> None:
    lines: list[str] = []
    emitter = StructuredLogEmitter(
        lines.append,
        clock=lambda: datetime(2026, 7, 19, 0, 0, tzinfo=UTC),
    )

    event = emitter.emit(
        "provider.request",
        request_id="request-1",
        session_id="session-1",
        tool_id="tool-1",
        task_id="task-1",
        status="started",
        fields={
            "provider": "offline",
            "model": "local-model",
            "prompt": "private prompt",
            "source": "private source",
            "path": "C:/private/source.py",
            "api_key": "private credential",
            "duration_ms": 12,
        },
    )

    assert event.request_id == "request-1"
    assert event.session_id == "session-1"
    assert event.tool_id == "tool-1"
    assert event.task_id == "task-1"
    assert event.metadata == {"duration_ms": 12, "model": "local-model", "provider": "offline"}
    assert {"api_key", "path", "prompt", "source"} <= set(event.redacted_fields)
    serialized = lines[0]
    assert "private prompt" not in serialized
    assert "private source" not in serialized
    assert "C:/private/source.py" not in serialized
    assert validate_log_json(serialized) == event


def test_unknown_and_nested_fields_are_dropped_and_schema_rejects_extra() -> None:
    metadata, redacted = redact_fields(
        {"provider": "offline", "nested": {"prompt": "private"}, "content": "secret"}
    )
    assert metadata == {"provider": "offline"}
    assert redacted == ("content", "nested")
    with pytest.raises(ValidationError):
        StructuredLogEvent.model_validate(
            {
                "timestamp": "2026-07-19T00:00:00Z",
                "level": "info",
                "event": "test",
                "unexpected": "value",
            }
        )


def test_correlation_ids_are_bounded_and_json_is_stable() -> None:
    emitter = StructuredLogEmitter()
    with pytest.raises(ValueError, match="request_id"):
        emitter.emit("request.started", request_id=" ")
    event = emitter.emit(
        "request.started",
        request_id="r",
        fields={"provider_request_id": "provider-42", "retryable": True},
    )
    payload = json.loads(event.to_json())
    assert payload["schema_version"] == "v1"
    assert payload["metadata"] == {"provider_request_id": "provider-42", "retryable": True}
