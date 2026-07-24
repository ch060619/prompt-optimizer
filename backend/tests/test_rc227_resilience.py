from __future__ import annotations

import socket
import sqlite3
from pathlib import Path
from threading import Event

import httpx
import pytest
from backend.rabbit_code.permissions import PermissionMode, PermissionPolicy
from backend.rabbit_code.process_tools import PortConflictError, ProcessManager

from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.model_lifecycle import DiskSpaceError, ModelDirectoryService
from prompt_optimizer.providers import (
    LocalModelOutOfMemory,
    LocalModelProvider,
    LocalRunnerHealth,
    ModelRequest,
    ProviderConfig,
    ProviderNetworkError,
    ProviderProxyError,
    ProviderRateLimitError,
)
from prompt_optimizer.providers.openai import OpenAICompatibleAdapter
from prompt_optimizer.public import error_code_for, provider_error_presentation
from prompt_optimizer.storage.errors import DatabaseLockedError
from prompt_optimizer.storage.service import StorageService


def _provider_config(**overrides: object) -> ProviderConfig:
    values: dict[str, object] = {
        "name": "openai",
        "base_url": "https://provider.test/v1",
        "api_key": "owned-key",
        "model": "demo",
        "max_retries": 0,
        "circuit_failure_threshold": 1,
    }
    values.update(overrides)
    return ProviderConfig(**values)  # type: ignore[arg-type]


def _success() -> httpx.Response:
    return httpx.Response(
        200,
        json={"choices": [{"message": {"content": "目标：完成。输出格式：列表。"}}]},
    )


def test_rate_limit_retry_is_finite_and_preserves_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    waits: list[float] = []
    prompts: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        prompts.append(request.content.decode())
        return httpx.Response(
            429,
            json={"error": {"code": "rate_limit", "message": "slow down"}},
            headers={"Retry-After": "3"},
        )

    provider = OpenAICompatibleAdapter(
        _provider_config(max_retries=2),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    monkeypatch.setattr("prompt_optimizer.providers.openai.random.uniform", lambda _a, _b: 0.0)
    provider._sleep_before_retry = lambda _request, seconds: waits.append(seconds)  # type: ignore[method-assign]

    with pytest.raises(ProviderRateLimitError) as raised:
        provider.optimize(ModelRequest(prompt="keep this input", request_id="rc227-rate"))

    assert calls == 3
    assert waits == [3.0, 3.0]
    assert all("keep this input" in prompt for prompt in prompts)
    assert raised.value.retryable is True
    assert raised.value.retry_after_seconds == 3.0


def test_proxy_failure_has_dedicated_diagnostic_and_finite_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ProxyError("proxy unavailable", request=request)

    provider = OpenAICompatibleAdapter(
        _provider_config(max_retries=1),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    provider._sleep_before_retry = lambda _request, _seconds: None  # type: ignore[method-assign]

    with pytest.raises(ProviderProxyError) as raised:
        provider.optimize(ModelRequest(prompt="proxy input"))

    presentation = provider_error_presentation(raised.value)
    assert calls == 2
    assert error_code_for(raised.value) == "PROVIDER_PROXY"
    assert presentation.category == "network"
    assert presentation.recovery_action == "check_network"
    assert presentation.retryable is True


def test_network_disconnect_retries_once_per_configured_attempt_and_opens_circuit(
) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ConnectError("offline", request=request)

    provider = OpenAICompatibleAdapter(
        _provider_config(max_retries=2),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    provider._sleep_before_retry = lambda _request, _seconds: None  # type: ignore[method-assign]

    with pytest.raises(ProviderNetworkError):
        provider.optimize(ModelRequest(prompt="offline input"))

    assert calls == 3
    assert provider.circuit_state == "open"


class _OutOfMemoryRunner:
    def __init__(self) -> None:
        self.prompts: list[str] = []
        self.recovered = 0

    def health(self) -> LocalRunnerHealth:
        return LocalRunnerHealth(True, model_id="demo", status="ready")

    def generate(self, request: ModelRequest) -> str:
        self.prompts.append(request.prompt)
        raise MemoryError("injected OOM")

    def stream(self, request: ModelRequest):
        raise MemoryError("injected OOM")
        yield ""

    def recover_from_oom(self) -> None:
        self.recovered += 1


def test_local_oom_releases_resources_and_preserves_input() -> None:
    runner = _OutOfMemoryRunner()
    provider = LocalModelProvider(runner=runner, analyzer=Analyzer())

    with pytest.raises(LocalModelOutOfMemory) as raised:
        provider.optimize(ModelRequest(prompt="local input", cancel_event=Event()))

    assert runner.prompts == ["local input"]
    assert runner.recovered == 1
    assert raised.value.recovery_action == "free_memory"
    assert raised.value.retryable is True


def test_disk_full_is_detected_before_model_directory_switch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    service = ModelDirectoryService(tmp_path / "registry.json", tmp_path / "models")
    monkeypatch.setattr(
        "prompt_optimizer.model_lifecycle.shutil.disk_usage",
        lambda _path: shutil_disk_usage(total=100, used=100, free=0),
    )

    with pytest.raises(DiskSpaceError) as raised:
        service.set_directory(tmp_path / "full", required_bytes=1)

    assert raised.value.code == "DISK_FULL"
    assert raised.value.retryable is False
    assert raised.value.recovery_action == "free_disk"
    assert service.root == (tmp_path / "models").resolve()


def shutil_disk_usage(*, total: int, used: int, free: int):
    return type("DiskUsage", (), {"total": total, "used": used, "free": free})()


def test_sqlite_lock_is_classified_without_retry_loop(tmp_path: Path) -> None:
    database = tmp_path / "locked.sqlite3"
    storage = StorageService(database, busy_timeout_seconds=0.0)
    lock = sqlite3.connect(database)
    lock.execute("BEGIN EXCLUSIVE")
    try:
        with pytest.raises(DatabaseLockedError) as raised:
            storage.save_version(
                "original input",
                "optimized output",
                Analyzer().analyze("目标：完成。输出格式：列表。"),
            )
    finally:
        lock.rollback()
        lock.close()

    assert raised.value.code == "DATABASE_LOCKED"
    assert raised.value.retryable is True
    assert raised.value.recovery_action == "wait_and_retry"


def test_port_conflict_requires_another_port(tmp_path: Path) -> None:
    policy = PermissionPolicy(tmp_path)
    policy.switch_mode(PermissionMode.HIGH, explicit_confirmation=True)
    manager = ProcessManager(tmp_path, permission_policy=policy)
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen()
    try:
        port = server.getsockname()[1]
        with pytest.raises(PortConflictError) as raised:
            manager.require_free_port(port)
        assert raised.value.code == "PORT_CONFLICT"
        assert raised.value.retryable is False
        assert raised.value.recovery_action == "choose_port"
    finally:
        server.close()
        manager.close()
