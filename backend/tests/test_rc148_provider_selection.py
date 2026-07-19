from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from fastapi.testclient import TestClient

from prompt_optimizer.api.app import create_app
from prompt_optimizer.core.optimizer import Optimizer
from prompt_optimizer.providers import (
    ModelRequest,
    ModelResponse,
    ProviderCapabilities,
    ProviderEvent,
    ProviderEventType,
    ProviderRegistry,
)
from prompt_optimizer.providers.offline import OfflineRuleProvider
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService

# RC ID: RC-148. Verify session versus optimizer Provider/model selection and health fallback.


class HealthyProvider:
    name = "openai"
    display_name = "Configured Optimizer"
    model = "session-model"
    execution_location = "cloud"
    network_access = True
    capabilities = ProviderCapabilities(streaming=True)

    def optimize(self, request: ModelRequest) -> ModelResponse:
        analysis = Optimizer().optimize(request.prompt, request.template, request.language_profile)
        return ModelResponse(analysis=analysis, provider_used=self.name, latency_ms=1)

    def stream(self, request: ModelRequest) -> Iterator[ProviderEvent]:
        response = self.optimize(request)
        yield ProviderEvent(ProviderEventType.STARTED)
        yield ProviderEvent(ProviderEventType.DELTA, text=response.analysis.optimized_prompt or "")
        yield ProviderEvent(ProviderEventType.COMPLETED)


def services_for(tmp_path: Path, providers: ProviderRegistry) -> AppServices:
    storage = StorageService(tmp_path / "rc148.sqlite3")
    return AppServices(
        providers=providers,
        versions=VersionService(storage),
    )


def test_optimizer_selection_overrides_session_when_healthy(tmp_path: Path) -> None:
    registry = ProviderRegistry(
        providers={"offline": OfflineRuleProvider(), "openai": HealthyProvider()}
    )
    services = services_for(tmp_path, registry)

    result = services.optimization.optimize(
        original_prompt="写一个发布说明",
        prompt="写一个发布说明",
        template=None,
        provider_name="offline",
        optimizer_provider="openai",
        optimizer_model="optimizer-model",
        owner_id=None,
    )

    assert result.metadata.provider_used == "openai"
    assert result.metadata.model == "optimizer-model"
    assert result.metadata.selection_scope == "optimizer"
    assert result.metadata.provider_health == "healthy"


def test_unavailable_optimizer_falls_back_to_healthy_session_route(tmp_path: Path) -> None:
    registry = ProviderRegistry(providers={"offline": OfflineRuleProvider()})
    services = services_for(tmp_path, registry)

    result = services.optimization.optimize(
        original_prompt="写一个本地说明",
        prompt="写一个本地说明",
        template=None,
        provider_name="offline",
        optimizer_provider="openai",
        optimizer_model="not-configured",
        owner_id=None,
    )

    assert result.metadata.provider_used == "offline"
    assert result.metadata.selection_scope == "default"
    assert result.metadata.provider_health == "fallback"
    assert result.metadata.fallback_used is False


def test_selection_scope_and_health_are_persisted_and_exposed_by_api(tmp_path: Path) -> None:
    registry = ProviderRegistry(
        providers={"offline": OfflineRuleProvider(), "openai": HealthyProvider()}
    )
    services = services_for(tmp_path, registry)
    with TestClient(create_app(services)) as client:
        registered = client.post(
            "/api/v1/auth/register",
            json={"username": "rc148-user", "password": "secret123"},
        ).json()
        token = registered["access_token"]
        response = client.post(
            "/api/v1/optimize",
            json={
                "prompt": "记录选择",
                "optimizer_provider": "openai",
                "optimizer_model": "optimizer-model",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    payload = response.json()
    assert payload["metadata"]["selection_scope"] == "optimizer"
    assert payload["metadata"]["provider_health"] == "healthy"
    version = services.versions.get(payload["version_id"], registered["user"]["id"])
    assert version.selection_scope == "optimizer"
    assert version.provider_health == "healthy"
