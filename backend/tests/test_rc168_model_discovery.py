from __future__ import annotations

import httpx

from prompt_optimizer.providers import (
    ModelDiscoveryService,
    ProviderConfig,
    ProviderRegistry,
    validate_model_id,
)

# RC ID: RC-168. Verify paginated discovery, cache behavior, failures, and manual IDs.


def config(name: str = "openrouter") -> ProviderConfig:
    return ProviderConfig(
        name=name,
        base_url="https://provider.example/v1",
        api_key="provider-key",
        model="saved-model",
        custom_headers=(("X-Discovery-Test", "enabled"),),
    )


def test_discovery_fetches_pages_and_reuses_ttl_cache() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.url.path == "/v1/models"
        assert request.headers["Authorization"] == "Bearer provider-key"
        assert request.headers["X-Discovery-Test"] == "enabled"
        if request.url.params.get("cursor") == "page-2":
            return httpx.Response(200, json={"data": [{"id": "model-two"}]})
        return httpx.Response(
            200,
            json={"data": [{"id": "model-one"}], "next_cursor": "page-2"},
        )

    service = ModelDiscoveryService(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        ttl_seconds=30,
    )
    first = service.discover(config(), stored_models=("saved-model",), manual_model="new/model")
    cached = service.discover(config(), stored_models=("saved-model",), manual_model="new/model")

    assert first.succeeded
    assert first.models == ("model-one", "model-two", "saved-model", "new/model")
    assert cached.from_cache
    assert cached.models == first.models
    assert len(calls) == 2


def test_empty_model_list_is_successful_and_does_not_drop_manual_model() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"data": []}))
    )
    result = ModelDiscoveryService(client=client).discover(
        config(), stored_models=("saved-model",), manual_model="manual/new-model"
    )

    assert result.succeeded
    assert result.models == ("saved-model", "manual/new-model")


def test_timeout_and_forbidden_preserve_saved_and_manual_models() -> None:
    timeout_client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: (_ for _ in ()).throw(httpx.ReadTimeout("slow"))
        )
    )
    timeout = ModelDiscoveryService(client=timeout_client).discover(
        config(), stored_models=("saved-model",), manual_model="manual/model"
    )
    assert timeout.error_code == "timeout"
    assert timeout.models == ("saved-model", "manual/model")

    forbidden_client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(403, json={"error": "denied"}))
    )
    forbidden = ModelDiscoveryService(client=forbidden_client).discover(
        config(), stored_models=("saved-model",), manual_model="manual/model"
    )
    assert forbidden.error_code == "forbidden"
    assert forbidden.models == ("saved-model", "manual/model")


def test_manual_model_validation_is_format_only_and_registry_uses_preset() -> None:
    assert validate_model_id("provider/model:2026")
    assert not validate_model_id("provider model")
    assert not validate_model_id(" ")

    client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"data": []}))
    )
    registry = ProviderRegistry(model_discovery=ModelDiscoveryService(client=client))
    result = registry.discover_models("openrouter", manual_model="new-provider/model")
    assert result.succeeded
    assert result.models == ("new-provider/model",)
