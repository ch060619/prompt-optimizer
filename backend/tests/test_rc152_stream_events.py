from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from fastapi.testclient import TestClient

from prompt_optimizer.api.app import create_app
from prompt_optimizer.core.optimizer import Optimizer
from prompt_optimizer.providers import (
    ModelRequest,
    ModelResponse,
    ProviderCancelledError,
    ProviderCapabilities,
    ProviderEvent,
    ProviderEventType,
    ProviderRegistry,
)
from prompt_optimizer.providers.offline import OfflineRuleProvider
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService

# RC ID: RC-152. Verify ordered resumable optimization events and terminal-state replay.


class CountingStreamProvider:
    name = "openai"
    capabilities = ProviderCapabilities(streaming=True)

    def __init__(self, *, fail: bool = False) -> None:
        self.calls = 0
        self.fail = fail

    def optimize(self, request: ModelRequest) -> ModelResponse:
        raise AssertionError("streaming path should not call optimize")

    def stream(self, request: ModelRequest) -> Iterator[ProviderEvent]:
        self.calls += 1
        if self.fail:
            raise ProviderCancelledError("stream cancelled")
        yield ProviderEvent(ProviderEventType.STARTED)
        yield ProviderEvent(ProviderEventType.DELTA, text="流式结果")
        yield ProviderEvent(ProviderEventType.COMPLETED)


def _events(body: str) -> list[tuple[int, str, dict[str, object]]]:
    parsed: list[tuple[int, str, dict[str, object]]] = []
    for raw in body.strip().split("\n\n"):
        lines = raw.splitlines()
        if not lines or not any(line.startswith("id: ") for line in lines):
            continue
        sequence = int(next(line[4:] for line in lines if line.startswith("id: ")))
        event = next(line[7:] for line in lines if line.startswith("event: "))
        data = next(line[6:] for line in lines if line.startswith("data: "))
        import json

        parsed.append((sequence, event, json.loads(data)))
    return parsed


def _client(tmp_path: Path, provider: CountingStreamProvider) -> tuple[TestClient, AppServices]:
    services = AppServices()
    services.versions = VersionService(StorageService(tmp_path / "rc152.sqlite3"))
    services.providers = ProviderRegistry(
        Optimizer(),
        providers={"offline": OfflineRuleProvider(), "openai": provider},
    )
    return TestClient(create_app(services)), services


def test_v1_stream_events_are_ordered_and_numbered(tmp_path: Path) -> None:
    provider = CountingStreamProvider()
    with _client(tmp_path, provider)[0] as client:
        response = client.post(
            "/api/v1/optimize/stream",
            json={"prompt": "生成流式结果", "provider": "openai"},
            headers={"X-Request-ID": "rc152-order"},
        )

    events = _events(response.text)
    assert [event for _seq, event, _payload in events] == [
        "started",
        "analysis",
        "delta",
        "completed",
    ]
    assert [seq for seq, _event, _payload in events] == [0, 1, 2, 3]
    assert provider.calls == 1


def test_reconnect_replays_after_cursor_without_repeating_provider(tmp_path: Path) -> None:
    provider = CountingStreamProvider()
    with _client(tmp_path, provider)[0] as client:
        first = client.post(
            "/api/v1/optimize/stream",
            json={"prompt": "可重连结果", "provider": "openai"},
            headers={"X-Request-ID": "rc152-reconnect"},
        )
        replay = client.post(
            "/api/v1/optimize/stream",
            json={"prompt": "可重连结果", "provider": "openai"},
            headers={"X-Request-ID": "rc152-reconnect", "Last-Event-ID": "1"},
        )

    assert [event for _seq, event, _payload in _events(first.text)] == [
        "started",
        "analysis",
        "delta",
        "completed",
    ]
    replayed = _events(replay.text)
    assert [seq for seq, _event, _payload in replayed] == [2, 3]
    assert [event for _seq, event, _payload in replayed] == ["delta", "completed"]
    assert provider.calls == 1


def test_saved_event_is_replayed_without_duplicate_version(tmp_path: Path) -> None:
    provider = CountingStreamProvider()
    client, services = _client(tmp_path, provider)
    with client:
        registered = client.post(
            "/api/v1/auth/register",
            json={"username": "rc152-user", "password": "secret123"},
        ).json()
        headers = {
            "Authorization": f"Bearer {registered['access_token']}",
            "X-Request-ID": "rc152-saved",
        }
        first = client.post(
            "/api/v1/optimize/stream",
            json={"prompt": "需要保存", "provider": "openai"},
            headers=headers,
        )
        replay = client.post(
            "/api/v1/optimize/stream",
            json={"prompt": "需要保存", "provider": "openai"},
            headers={**headers, "Last-Event-ID": "1"},
        )

    assert [event for _seq, event, _payload in _events(first.text)] == [
        "started",
        "analysis",
        "delta",
        "saved",
        "completed",
    ]
    assert [event for _seq, event, _payload in _events(replay.text)] == [
        "delta",
        "saved",
        "completed",
    ]
    assert provider.calls == 1
    assert len(services.versions.list(registered["user"]["id"])) == 1


def test_cancel_event_is_idempotent_and_replayable(tmp_path: Path) -> None:
    provider = CountingStreamProvider()
    with _client(tmp_path, provider)[0] as client:
        cancelled = client.post("/api/v1/optimize/stream/rc152-cancel/cancel")
        replay = client.post(
            "/api/v1/optimize/stream",
            json={"prompt": "不会执行", "provider": "openai"},
            headers={"X-Request-ID": "rc152-cancel", "Last-Event-ID": "-1"},
        )

    assert cancelled.json()["cancelled"] is False
    assert [event for _seq, event, _payload in _events(replay.text)] == ["cancelled"]
    assert provider.calls == 0


def test_provider_error_emits_error_terminal_event(tmp_path: Path) -> None:
    provider = CountingStreamProvider(fail=True)
    with _client(tmp_path, provider)[0] as client:
        response = client.post(
            "/api/v1/optimize/stream",
            json={"prompt": "失败结果", "provider": "openai"},
            headers={"X-Request-ID": "rc152-error"},
        )

    events = _events(response.text)
    assert [event for _seq, event, _payload in events] == ["started", "analysis", "error"]
    assert events[-1][2]["code"] == "REQUEST_CANCELLED"
