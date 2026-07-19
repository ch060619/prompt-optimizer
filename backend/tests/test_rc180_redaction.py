from __future__ import annotations

import json

from backend.rabbit_code.public_output import safe_json_dumps

from prompt_optimizer.public import register_runtime_secret, sanitize_error_message

# RC ID: RC-180. Verify provider formats and runtime fingerprints never leak.


def test_provider_formats_and_runtime_fingerprints_are_redacted() -> None:
    register_runtime_secret("workspace-secret-value")
    message = " ".join(
        [
            "sk-proj-1234567890abcdef",
            "sk-ant-api03-1234567890",
            "AIzaSyA1234567890abcdefghijklmnop",
            "xai-1234567890abcdef",
            "ghp_123456789012345678901234567890",
            "github_pat_123456789012345678901234567890",
            "hf_1234567890abcdef",
            "r8_1234567890abcdef",
            "workspace-secret-value",
        ]
    )

    cleaned = sanitize_error_message(message)

    assert "sk-proj-" not in cleaned
    assert "sk-ant-" not in cleaned
    assert "AIza" not in cleaned
    assert "ghp_" not in cleaned
    assert "github_pat_" not in cleaned
    assert "workspace-secret-value" not in cleaned


def test_public_json_redacts_sensitive_fields_and_string_formats() -> None:
    payload = {
        "api_key": "plain-provider-secret",
        "authorization": "Bearer ghp_123456789012345678901234567890",
        "nested": {"message": "sk-proj-1234567890abcdef"},
        "status": "ok",
    }

    encoded = safe_json_dumps(payload)
    decoded = json.loads(encoded)

    assert decoded["api_key"] == "[REDACTED]"
    assert decoded["authorization"] == "[REDACTED]"
    assert decoded["nested"]["message"] == "[REDACTED]"
    assert decoded["status"] == "ok"
    assert "plain-provider-secret" not in encoded
