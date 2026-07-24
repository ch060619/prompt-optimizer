#!/usr/bin/env python3
"""RC ID: RC-215. Validate the structured log contract and redaction boundary."""

from __future__ import annotations

import json
from pathlib import Path

from prompt_optimizer.structured_logging import StructuredLogEmitter, StructuredLogEvent

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "docs/logging/schema-v1.json"
REQUIRED = {
    "schema_version",
    "timestamp",
    "level",
    "event",
    "request_id",
    "session_id",
    "tool_id",
    "task_id",
    "status",
    "metadata",
    "redacted_fields",
}


def main() -> int:
    document = json.loads(SCHEMA.read_text(encoding="utf-8"))
    if set(document.get("required", ())) != REQUIRED:
        print("ERROR: structured log schema required fields are stale")
        return 1
    if set(StructuredLogEvent.model_fields) != REQUIRED:
        print("ERROR: Pydantic structured log fields drift from schema")
        return 1
    event = StructuredLogEmitter().emit(
        "schema.check",
        request_id="request-check",
        session_id="session-check",
        fields={"provider": "offline", "prompt": "must not persist"},
    )
    payload = json.loads(event.to_json())
    if payload["metadata"] != {"provider": "offline"} or "prompt" not in payload["redacted_fields"]:
        print("ERROR: structured log redaction check failed")
        return 1
    print("Structured log schema and default redaction are current.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
