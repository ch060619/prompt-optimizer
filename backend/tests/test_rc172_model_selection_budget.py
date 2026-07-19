from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from prompt_optimizer.providers import (
    ModelRequest,
    ModelResponse,
    ModelSelectionStore,
    ProviderBudgetExceededError,
    ProviderConfig,
    ProviderErrorCategory,
    ProviderEvent,
    ProviderEventType,
    ProviderRegistry,
    ProviderServerError,
)
from prompt_optimizer.providers.budget import enforce_budget, estimate_request
from prompt_optimizer.providers.offline import OfflineRuleProvider
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService


class FailingProvider:
    name = "openai"
    model = "primary-model"
    display_name = "Primary Provider"
    execution_location = "cloud"
    network_access = True
    config = ProviderConfig(
        name="openai",
        model="primary-model",
        input_cost_per_1k_tokens=1.0,
        output_cost_per_1k_tokens=1.0,
    )

    def optimize(self, request: ModelRequest) -> ModelResponse:
        raise ProviderServerError("primary unavailable")

    def stream(self, request: ModelRequest) -> Iterator[ProviderEvent]:
        yield ProviderEvent(ProviderEventType.STARTED)
        raise ProviderServerError("primary unavailable")


def _services(tmp_path: Path, registry: ProviderRegistry) -> AppServices:
    return AppServices(
        providers=registry,
        versions=VersionService(StorageService(tmp_path / "rc172.sqlite3")),
    )


def test_model_routes_resolve_workspace_then_global_and_persist(tmp_path: Path) -> None:
    global_path = tmp_path / "global-route.json"
    workspace_path = tmp_path / "workspace-route.json"
    store = ModelSelectionStore(global_path=global_path, workspace_path=workspace_path)
    store.set("global", "offline", "global-model")
    store.set("workspace", "offline", "workspace-model")

    reloaded = ModelSelectionStore(global_path=global_path, workspace_path=workspace_path)
    route, scope = reloaded.resolve_session(provider=None, model=None)

    assert (route.provider, route.model, scope) == ("offline", "workspace-model", "workspace")
    reloaded.clear("workspace")
    route, scope = reloaded.resolve_session(provider=None, model=None)
    assert (route.model, scope) == ("global-model", "global")


def test_registry_keeps_optimizer_route_separate_from_session_route() -> None:
    store = ModelSelectionStore()
    store.set("global", "offline", "conversation-model")
    store.set("optimizer", "offline", "optimizer-model")
    registry = ProviderRegistry(
        providers={"offline": OfflineRuleProvider()},
        selection_store=store,
    )

    selection = registry.resolve(
        session_provider=None,
        session_model=None,
        optimizer_provider=None,
        optimizer_model=None,
    )

    assert selection.scope == "optimizer"
    assert selection.model == "optimizer-model"


def test_unavailable_route_exposes_fallback_chain() -> None:
    store = ModelSelectionStore()
    store.set("global", "openai", "primary-model")
    registry = ProviderRegistry(
        providers={"offline": OfflineRuleProvider()},
        selection_store=store,
    )

    selection = registry.resolve(
        session_provider=None,
        session_model=None,
        optimizer_provider=None,
        optimizer_model=None,
    )

    assert selection.name == "openai"
    assert selection.health == "unavailable"
    assert selection.fallback_chain == ("offline",)


def test_budget_estimate_blocks_before_provider_call(tmp_path: Path) -> None:
    failing = FailingProvider()
    registry = ProviderRegistry(
        providers={"offline": OfflineRuleProvider(), "openai": failing}
    )
    services = _services(tmp_path, registry)

    request = ModelRequest(prompt="预算测试")
    estimate = estimate_request(request, failing)
    assert estimate.input_tokens > 0
    assert estimate.cost > 0

    with pytest.raises(ProviderBudgetExceededError) as raised:
        services.optimization.optimize(
            original_prompt="预算测试",
            prompt="预算测试",
            template=None,
            provider_name="openai",
            max_tokens=estimate.total_tokens,
            max_cost=estimate.cost / 2,
            owner_id=None,
        )

    assert raised.value.category == ProviderErrorCategory.PARAMETER
    assert "cost" in raised.value.limit


def test_budget_helper_reports_token_limit() -> None:
    request = ModelRequest(prompt="超过预算")
    estimate = estimate_request(request, object())

    with pytest.raises(ProviderBudgetExceededError) as raised:
        enforce_budget(estimate, max_tokens=1, max_cost=None)

    assert "tokens" in str(raised.value)


def test_stream_fallback_exposes_reason_and_new_model(tmp_path: Path) -> None:
    offline = OfflineRuleProvider()
    offline.model = "offline-rules"  # type: ignore[attr-defined]
    registry = ProviderRegistry(
        providers={"offline": offline, "openai": FailingProvider()}
    )
    services = _services(tmp_path, registry)

    events = list(
        services.optimization.stream(
            original_prompt="需要回退",
            prompt="需要回退",
            template=None,
            provider_name="openai",
            owner_id=None,
        )
    )
    fallback = next(event.data for event in events if event.event == "fallback")

    assert fallback.provider_used == "offline"
    assert fallback.model == "offline-rules"
    assert fallback.fallback_chain == ["offline"]
    assert fallback.error_category == "server"
