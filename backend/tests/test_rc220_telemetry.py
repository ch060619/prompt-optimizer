from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from prompt_optimizer.privacy import TELEMETRY_CONSENT_VERSION, TelemetryService

# RC ID: RC-220. Verify versioned local consent and immediate opt-out boundaries.


def test_telemetry_starts_without_consent_or_pending_events() -> None:
    telemetry = TelemetryService()

    assert telemetry.consent.to_dict() == {
        "enabled": False,
        "include_content": False,
        "consent_version": None,
    }
    assert telemetry.pending_events() == ()


def test_opt_in_records_version_and_only_allowed_local_fields() -> None:
    telemetry = TelemetryService()
    consent = telemetry.opt_in()

    assert consent.consent_version == TELEMETRY_CONSENT_VERSION
    assert telemetry.record(
        "optimization_completed",
        {"provider": "offline", "duration_ms": 12, "prompt": "private"},
        content="private source",
    )

    event = telemetry.pending_events()[0]
    assert event["consent_version"] == TELEMETRY_CONSENT_VERSION
    assert event["metadata"] == {"provider": "offline", "duration_ms": 12}
    assert "content" not in event


def test_revoke_stops_new_collection_and_clear_deletes_pending_events() -> None:
    telemetry = TelemetryService()
    telemetry.opt_in()
    telemetry.record("before_revoke", {"app_version": "3.0.0"})

    telemetry.revoke()

    assert not telemetry.consent.enabled
    assert telemetry.consent.consent_version is None
    assert not telemetry.record("after_revoke", {"app_version": "3.0.0"})
    assert not telemetry.send(confirm=True, sender=lambda _events: None)
    telemetry.clear()
    assert telemetry.pending_events() == ()


def test_local_telemetry_does_not_require_a_remote_sender_until_explicit_send() -> None:
    telemetry = TelemetryService()
    telemetry.opt_in()
    telemetry.record("startup", {"app_version": "3.0.0"})
    sent: list[tuple[Mapping[str, Any], ...]] = []

    assert telemetry.send(confirm=True, sender=sent.append)
    assert len(sent) == 1
    assert telemetry.pending_events() == ()
