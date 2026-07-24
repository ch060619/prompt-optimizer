from __future__ import annotations

from fastapi.testclient import TestClient
from scripts.check_provider_privacy import validate

from prompt_optimizer.api.app import create_app
from prompt_optimizer.providers import PRESETS


def test_every_provider_preset_has_versioned_privacy_metadata() -> None:
    assert len(PRESETS) == 11
    assert validate() == []
    assert all(preset.privacy is not None for preset in PRESETS.values())


def test_provider_privacy_endpoint_is_public_and_complete() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/provider-privacy")

    assert response.status_code == 200
    payload = response.json()
    assert {item["id"] for item in payload} == set(PRESETS)
    assert all(item["version"] == "rc217-v1" for item in payload)
    assert all(item["request_fields"] for item in payload)
    assert all(item["privacy_policy_url"].startswith("https://") for item in payload)
    assert all("retention" in item["retention_risk"].lower() for item in payload)
