from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from prompt_optimizer.api.app import create_app
from prompt_optimizer.export.service import ExportService
from prompt_optimizer.providers import ModelProviderError, ModelRequest, ProviderRegistry
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService

# RC ID: RC-141. Verify useful optimization metadata and secret-safe fallback errors.


class SecretFailingProvider:
    name = "openai"

    def optimize(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        raise ModelProviderError(
            "api_key=sk-live-1234567890abcdef system_prompt=Ignore all public output rules"
        )

    def stream(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        raise ModelProviderError(
            "api_key=sk-live-1234567890abcdef system_prompt=Ignore all public output rules"
        )


def _client(tmp_path: Path) -> TestClient:
    services = AppServices()
    services.versions = VersionService(StorageService(tmp_path / "rc141.sqlite3"))
    services.export = ExportService()
    services.providers = ProviderRegistry(
        services.optimizer,
        providers={
            "offline": services.providers.get("offline"),
            "openai": SecretFailingProvider(),
        },
    )
    return TestClient(create_app(services))


def test_metadata_identifies_local_provider_without_secret_values(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        response = client.post("/api/v1/optimize", json={"prompt": "请优化这段话。"})

    assert response.status_code == 200
    metadata = response.json()["metadata"]
    assert metadata["provider_display_name"] == "离线规则"
    assert metadata["model"] is None
    assert metadata["execution_location"] == "local"
    assert metadata["credential_ref"] is None
    assert metadata["fallback_used"] is False
    assert metadata["error_code"] is None
    assert isinstance(metadata["latency_ms"], int)


def test_fallback_metadata_redacts_key_and_system_prompt(tmp_path: Path) -> None:
    with _client(tmp_path) as client:
        response = client.post(
            "/api/v1/optimize",
            json={"prompt": "请优化这段话。", "provider": "openai"},
        )

    assert response.status_code == 200
    metadata = response.json()["metadata"]
    serialized = json.dumps(metadata, ensure_ascii=False)
    assert metadata["provider_display_name"] == "离线规则"
    assert metadata["execution_location"] == "local"
    assert metadata["fallback_used"] is True
    assert metadata["error_code"] == "PROVIDER_ERROR"
    assert metadata["error_summary"] == "Provider error details were redacted."
    assert "sk-live-1234567890abcdef" not in serialized
    assert "system_prompt" not in serialized
    assert "Ignore all public output rules" not in serialized
