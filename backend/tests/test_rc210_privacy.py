from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from prompt_optimizer.privacy import (
    DiagnosticBundleService,
    PrivacyConsentRequired,
    TelemetryService,
)

# RC ID: RC-210. Verify opt-in telemetry and preview-gated diagnostics.


def test_telemetry_is_closed_by_default_and_does_not_call_sender() -> None:
    telemetry = TelemetryService()
    sent: list[tuple[Mapping[str, Any], ...]] = []

    assert not telemetry.record("startup", {"app_version": "3.0.0"}, content="prompt")
    assert telemetry.pending_events() == ()
    assert not telemetry.send(confirm=True, sender=sent.append)
    assert sent == []


def test_telemetry_requires_opt_in_and_drops_content_unless_selected() -> None:
    telemetry = TelemetryService()
    telemetry.opt_in()
    assert telemetry.record(
        "optimization_completed",
        {"provider": "offline", "prompt": "secret source"},
        content="print('private')",
    )

    event = telemetry.pending_events()[0]
    assert event["metadata"] == {"provider": "offline"}
    assert "content" not in event

    sent: list[tuple[Mapping[str, Any], ...]] = []
    with pytest.raises(PrivacyConsentRequired, match="confirmation"):
        telemetry.send(confirm=False, sender=sent.append)
    assert sent == []
    assert telemetry.send(confirm=True, sender=sent.append)
    assert sent and sent[0][0]["event"] == "optimization_completed"
    telemetry.opt_in()
    assert telemetry.record("later_event", {"app_version": "3.0.0"})
    telemetry.revoke()
    assert not telemetry.consent.enabled
    assert not telemetry.record("blocked_after_revoke", {})
    assert not telemetry.send(confirm=True, sender=sent.append)
    telemetry.clear()
    assert telemetry.pending_events() == ()


def test_diagnostic_preview_redacts_content_and_send_requires_confirmation() -> None:
    bundle = DiagnosticBundleService()
    preview = bundle.preview(
        {
            "app_version": "3.0.0",
            "api_key": "sk-proj-1234567890abcdef",
            "prompt": "private prompt",
            "components": {"sidecar": "healthy", "source": "private code"},
        },
        {"logs/session.log": "private log with sk-proj-1234567890abcdef"},
    )
    payload = preview.to_dict()

    assert payload["metadata"] == {
        "api_key": "[REDACTED]",
        "app_version": "3.0.0",
        "components": {"sidecar": "healthy"},
    }
    assert payload["files"] == [{"name": "session.log", "size_bytes": 41}]
    redacted_fields = payload["redacted_fields"]
    assert isinstance(redacted_fields, list)
    assert {str(item) for item in redacted_fields} == {"prompt", "source"}
    assert "private prompt" not in json.dumps(payload)
    assert "private log" not in json.dumps(payload)

    sent: list[Mapping[str, object]] = []
    with pytest.raises(PrivacyConsentRequired, match="confirmation"):
        bundle.send(confirm=False, sender=sent.append)
    assert sent == []
    exported = bundle.export(confirm=True)
    assert json.loads(exported) == payload
    bundle.send(confirm=True, sender=sent.append)
    assert sent == [payload]
    assert bundle.pending is None


def test_diagnostic_preview_can_be_cleared_without_sending() -> None:
    bundle = DiagnosticBundleService()
    bundle.preview({"app_version": "3.0.0"}, {})
    bundle.clear()
    with pytest.raises(ValueError, match="preview"):
        bundle.send(confirm=True, sender=lambda _payload: None)
