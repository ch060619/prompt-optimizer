from __future__ import annotations

from threading import Event

import httpx
import pytest

from prompt_optimizer.providers import (
    ModelRequest,
    ProviderCircuitOpenError,
    ProviderConfig,
    ProviderTimeoutError,
    ProviderUnauthorizedError,
)
from prompt_optimizer.providers.openai import OpenAICompatibleAdapter
from prompt_optimizer.providers.registry import ProviderRegistry

# RC ID: RC-151. Verify authorization, idempotent retries, circuit transitions, and cancellation.


def _config(**overrides: object) -> ProviderConfig:
    values: dict[str, object] = {
        "name": "openai",
        "base_url": "https://example.test/chat",
        "api_key": "test-key",
        "model": "demo",
        "authorized": True,
        "max_retries": 0,
        "circuit_failure_threshold": 1,
        "circuit_reset_seconds": 0,
    }
    values.update(overrides)
    return ProviderConfig(**values)  # type: ignore[arg-type]


def test_unauthorized_provider_stops_before_http_request() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={})

    provider = OpenAICompatibleAdapter(
        _config(authorized=False),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ProviderUnauthorizedError):
        provider.optimize(ModelRequest(prompt="禁止外发"))

    assert calls == 0


def test_retry_reuses_idempotency_key() -> None:
    headers: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        headers.append(request.headers.get("Idempotency-Key"))
        if len(headers) == 1:
            raise httpx.TimeoutException("temporary timeout", request=request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "目标：重试。输出格式：列表。"}}]},
        )

    provider = OpenAICompatibleAdapter(
        _config(max_retries=1, circuit_failure_threshold=3),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    response = provider.optimize(ModelRequest(prompt="重试任务", request_id="rc151-1"))

    assert response.provider_used == "openai"
    assert headers == ["rc151-1", "rc151-1"]
    assert provider.circuit_state == "closed"


def test_circuit_transitions_open_half_open_and_closed() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise httpx.TimeoutException("first failure", request=request)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "目标：恢复。输出格式：列表。"}}]},
        )

    provider = OpenAICompatibleAdapter(
        _config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ProviderTimeoutError):
        provider.optimize(ModelRequest(prompt="首次失败", request_id="rc151-open"))
    assert provider.circuit_state == "open"

    response = provider.optimize(ModelRequest(prompt="恢复请求", request_id="rc151-half-open"))

    assert response.provider_used == "openai"
    assert provider.circuit_state == "closed"
    assert calls == 2


def test_open_circuit_blocks_requests_until_reset_window() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.TimeoutException("failure", request=request)

    provider = OpenAICompatibleAdapter(
        _config(circuit_reset_seconds=60),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(ProviderTimeoutError):
        provider.optimize(ModelRequest(prompt="打开熔断", request_id="rc151-open"))
    with pytest.raises(ProviderCircuitOpenError):
        provider.optimize(ModelRequest(prompt="被熔断", request_id="rc151-blocked"))

    assert calls == 1
    assert provider.circuit_state == "open"


def test_cancelled_request_does_not_call_http_or_open_circuit() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={})

    cancel_event = Event()
    cancel_event.set()
    provider = OpenAICompatibleAdapter(
        _config(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(Exception, match="已取消"):
        provider.optimize(ModelRequest(prompt="取消任务", cancel_event=cancel_event))

    assert calls == 0
    assert provider.circuit_state == "closed"


def test_environment_cloud_provider_requires_explicit_authorization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for suffix, value in {
        "BASE_URL": "https://example.test/chat",
        "API_KEY": "test-key",
        "MODEL": "demo",
    }.items():
        monkeypatch.setenv(f"RABBIT_CODE_OPENAI_{suffix}", value)
    monkeypatch.delenv("RABBIT_CODE_OPENAI_AUTHORIZED", raising=False)
    monkeypatch.delenv("PROMPT_OPTIMIZER_OPENAI_AUTHORIZED", raising=False)

    provider = ProviderRegistry().get("openai")

    assert provider.config.authorized is False  # type: ignore[attr-defined]
    assert ProviderRegistry.is_available(provider) is False
