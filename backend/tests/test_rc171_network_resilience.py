from __future__ import annotations

import ssl
from threading import Event

import httpx
import pytest

from prompt_optimizer.providers import (
    ModelRequest,
    ProviderCancelledError,
    ProviderConfig,
)
from prompt_optimizer.providers.openai import OpenAICompatibleAdapter
from prompt_optimizer.providers.registry import ProviderRegistry


def _config(**overrides: object) -> ProviderConfig:
    values: dict[str, object] = {
        "name": "openai",
        "base_url": "https://provider.test/v1",
        "api_key": "owned-key",
        "model": "demo",
        "max_retries": 2,
        "circuit_failure_threshold": 3,
    }
    values.update(overrides)
    return ProviderConfig(**values)  # type: ignore[arg-type]


def _success() -> httpx.Response:
    return httpx.Response(
        200,
        json={"choices": [{"message": {"content": "目标：完成。输出格式：列表。"}}]},
    )


def test_retry_after_overrides_exponential_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0
    waits: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                429,
                json={"error": {"code": "rate_limit", "message": "slow down"}},
                headers={"Retry-After": "2"},
            )
        return _success()

    provider = OpenAICompatibleAdapter(
        _config(max_retries=1),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    monkeypatch.setattr("prompt_optimizer.providers.openai.random.uniform", lambda _a, _b: 0.0)
    provider._sleep_before_retry = lambda _request, seconds: waits.append(seconds)  # type: ignore[method-assign]

    provider.optimize(ModelRequest(prompt="限流重试"))

    assert calls == 2
    assert waits == [2.0]


def test_network_retries_use_exponential_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0
    waits: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise httpx.ConnectError("offline", request=request)
        return _success()

    provider = OpenAICompatibleAdapter(
        _config(max_retries=2),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    monkeypatch.setattr("prompt_optimizer.providers.openai.random.uniform", lambda _a, _b: 0.0)
    provider._sleep_before_retry = lambda _request, seconds: waits.append(seconds)  # type: ignore[method-assign]

    provider.optimize(ModelRequest(prompt="断网重试"))

    assert calls == 3
    assert waits == [0.2, 0.4]


def test_cancel_interrupts_retry_wait_before_second_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    cancel_event = Event()

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.TimeoutException("slow", request=request)

    provider = OpenAICompatibleAdapter(
        _config(max_retries=1),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    def interrupting_sleep(_seconds: float) -> None:
        cancel_event.set()

    monkeypatch.setattr("prompt_optimizer.providers.openai.time.sleep", interrupting_sleep)
    with pytest.raises(ProviderCancelledError):
        provider.optimize(ModelRequest(prompt="可取消重试", cancel_event=cancel_event))

    assert calls == 1


def test_proxy_ca_ip_family_and_no_proxy_are_configurable() -> None:
    provider = OpenAICompatibleAdapter(
        _config(
            proxy_url="http://proxy.test:8080",
            no_proxy=("localhost", ".internal.test"),
            ca_bundle=ssl.get_default_verify_paths().cafile,
            ip_version="ipv6",
        )
    )

    assert provider._matches_no_proxy("https://localhost/v1") is True
    assert provider._matches_no_proxy("https://api.internal.test/v1") is True
    assert provider._matches_no_proxy("https://api.public.test/v1") is False


def test_proxy_credentials_require_opaque_reference_and_runtime_resolver() -> None:
    with pytest.raises(ValueError, match="不得包含明文凭据"):
        OpenAICompatibleAdapter(_config(proxy_url="http://user:password@proxy.test:8080"))

    seen: list[str] = []

    def resolve(reference: str) -> tuple[str, str]:
        seen.append(reference)
        return "proxy-user", "proxy-password"

    OpenAICompatibleAdapter(
        _config(
            proxy_url="http://proxy.test:8080",
            proxy_credential_ref="secret://proxy/enterprise",
        ),
        proxy_credential_resolver=resolve,
    )

    assert seen == ["secret://proxy/enterprise"]


def test_provider_registry_reads_enterprise_network_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RABBIT_CODE_OPENAI_PROXY_URL", "http://proxy.test:8080")
    monkeypatch.setenv("RABBIT_CODE_OPENAI_NO_PROXY", "localhost,.internal.test")
    monkeypatch.setenv("RABBIT_CODE_OPENAI_CA_BUNDLE", "C:/certs/enterprise.pem")
    monkeypatch.setenv("RABBIT_CODE_OPENAI_IP_VERSION", "ipv4")
    monkeypatch.setenv(
        "RABBIT_CODE_OPENAI_PROXY_CREDENTIAL_REF",
        "secret://proxy/enterprise",
    )

    config = ProviderRegistry._config_from_env("openai")

    assert config.proxy_url == "http://proxy.test:8080"
    assert config.no_proxy == ("localhost", ".internal.test")
    assert config.ca_bundle == "C:/certs/enterprise.pem"
    assert config.ip_version == "ipv4"
    assert config.proxy_credential_ref == "secret://proxy/enterprise"
