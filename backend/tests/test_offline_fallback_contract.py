from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from fastapi.testclient import TestClient
from pytest import fixture

from prompt_optimizer.api.app import create_app
from prompt_optimizer.export.service import ExportService
from prompt_optimizer.providers import (
    ModelProviderError,
    ModelRequest,
    ModelResponse,
    ProviderRegistry,
)
from prompt_optimizer.providers.offline import OfflineRuleProvider
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService

# RC ID: RC-050. Verify local fallback registration, triggers, metadata, and SSE behavior.


@fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    services = AppServices()
    services.versions = VersionService(StorageService(tmp_path / "offline-contract.sqlite3"))
    services.export = ExportService()
    services.providers = ProviderRegistry(
        services.optimizer,
        providers={"offline": services.providers.get("offline"), "openai": FailingProvider()},
    )
    with TestClient(create_app(services)) as test_client:
        yield test_client


def test_offline_provider_is_registered_as_a_local_non_model_backend() -> None:
    provider = ProviderRegistry().get("offline")

    assert isinstance(provider, OfflineRuleProvider)
    assert provider.name == "offline"
    assert provider.display_name == "离线规则"
    assert provider.is_model is False
    assert provider.network_access is False
    assert provider.fallback_triggers == (
        "provider_error",
        "provider_timeout",
        "provider_rate_limit",
        "provider_unavailable",
    )


def test_remote_failure_returns_offline_fallback_metadata(client: TestClient) -> None:
    response = client.post(
        "/api/optimize",
        json={"prompt": "请优化这段销售说明。", "provider": "openai"},
    )

    assert response.status_code == 200
    metadata = response.json()["metadata"]
    assert metadata["provider_used"] == "offline"
    assert metadata["fallback_used"] is True
    assert metadata["error_summary"] == "network unavailable"


def test_stream_failure_emits_offline_fallback_reason(client: TestClient) -> None:
    with client.stream(
        "POST",
        "/api/optimize/stream",
        json={"prompt": "请流式优化这段销售说明。", "provider": "openai"},
    ) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    assert "event: fallback" in body
    assert '"fallback_used": true' in body
    assert '"error_summary": "network unavailable"' in body
    assert '"provider_used": "offline"' in body


class FailingProvider:
    name = "openai"

    def optimize(self, request: ModelRequest) -> ModelResponse:
        raise ModelProviderError("network unavailable")

    def stream(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        raise ModelProviderError("network unavailable")
