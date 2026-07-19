from __future__ import annotations

import json

from backend.rabbit_code.public_output import (
    public_log_event,
    public_progress,
    safe_json_dumps,
    sanitize_public_payload,
)

# RC ID: RC-079. Verify hidden reasoning fields never enter public logs or snapshots.


def test_sanitizer_removes_hidden_reasoning_fields_recursively() -> None:
    payload = {
        "text": "公开回答",
        "reasoning": "内部推理",
        "nested": {
            "thinking": "隐藏内容",
            "basis": "简短依据",
            "items": [{"chain_of_thought": "隐藏"}, {"value": 1}],
        },
    }

    cleaned = sanitize_public_payload(payload)

    assert cleaned == {
        "text": "公开回答",
        "nested": {"basis": "简短依据", "items": [{}, {"value": 1}]},
    }
    assert "reasoning" not in safe_json_dumps(payload)


def test_public_log_has_only_allowed_summary_usage_and_status_fields() -> None:
    event = public_log_event(
        "model_completed",
        status="completed",
        basis="依据摘要",
        usage={"input_tokens": 3, "output_tokens": 2, "reasoning": "隐藏"},
        raw={"thinking": "隐藏", "provider": "offline"},
    )

    encoded = json.loads(safe_json_dumps(event))

    assert encoded == {
        "basis": "依据摘要",
        "event": "model_completed",
        "progress": "Response ready",
        "status": "completed",
        "usage": {"input_tokens": 3, "output_tokens": 2},
    }


def test_progress_messages_are_predefined_and_do_not_echo_hidden_content() -> None:
    assert public_progress("model") == "Preparing response"
    assert public_progress("unknown", fallback="Working") == "Working"
