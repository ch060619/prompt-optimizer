from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from prompt_optimizer.api.app import create_app, create_app_server
from prompt_optimizer.export.service import ExportService
from prompt_optimizer.providers import (
    ModelProviderError,
    ModelRequest,
    ModelResponse,
    ProviderCapabilities,
    ProviderEvent,
    ProviderRegistry,
)
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService

# RC ID: RC-232. Keep FastAPI security and transport tests offline and repeatable.

STARTUP_TOKEN = "rc232-startup-token"
ALLOWED_ORIGIN = "http://127.0.0.1:5173"


def _services(tmp_path: Path) -> AppServices:
    services = AppServices()
    services.versions = VersionService(StorageService(tmp_path / "rc232.sqlite3"))
    services.export = ExportService()
    return services


def _strict_client(tmp_path: Path, *, max_body_bytes: int = 512) -> TestClient:
    return TestClient(
        create_app_server(
            _services(tmp_path),
            startup_token=STARTUP_TOKEN,
            strict_boundary=True,
            max_body_bytes=max_body_bytes,
        ),
        base_url="http://127.0.0.1",
        client=("127.0.0.1", 51000),
    )


def _strict_headers(*, origin: str | None = ALLOWED_ORIGIN) -> dict[str, str]:
    headers = {
        "X-Rabbit-Code-Startup-Token": STARTUP_TOKEN,
        "X-Rabbit-Code-Protocol": "v1",
    }
    if origin is not None:
        headers["Origin"] = origin
    return headers


def _event_names(body: str) -> list[str]:
    return [
        line[7:]
        for line in body.splitlines()
        if line.startswith("event: ")
    ]


def test_strict_api_requires_token_origin_and_body_limit(tmp_path: Path) -> None:
    with _strict_client(tmp_path, max_body_bytes=128) as client:
        assert client.get("/api/v1/config").status_code == 401
        assert (
            client.get("/api/v1/config", headers=_strict_headers(origin="https://evil.test"))
            .status_code
            == 403
        )
        assert (
            client.post(
                "/api/v1/analyze",
                json={"prompt": "x" * 200},
                headers=_strict_headers(),
            ).status_code
            == 413
        )
        health = client.get("/api/v1/health")

    assert health.status_code == 200
    assert health.json()["startup_token_required"] is True


def test_websocket_requires_startup_token_and_allowlisted_origin(tmp_path: Path) -> None:
    with _strict_client(tmp_path) as client:
        with pytest.raises(WebSocketDisconnect) as missing:
            with client.websocket_connect("/api/v1/optimize/ws"):
                pass
        assert missing.value.code == 4401

        with pytest.raises(WebSocketDisconnect) as bad_origin:
            with client.websocket_connect(
                "/api/v1/optimize/ws",
                headers={
                    "X-Rabbit-Code-Startup-Token": STARTUP_TOKEN,
                    "Origin": "https://evil.test",
                },
            ):
                pass
        assert bad_origin.value.code == 4403


def test_websocket_emits_shared_optimization_events_and_closes(tmp_path: Path) -> None:
    with _strict_client(tmp_path) as client:
        with client.websocket_connect(
            "/api/v1/optimize/ws",
            headers={
                "X-Rabbit-Code-Startup-Token": STARTUP_TOKEN,
                "Origin": ALLOWED_ORIGIN,
                "X-Request-ID": "rc232-ws",
            },
        ) as websocket:
            websocket.send_json({"prompt": "输出一个列表"})
            messages = []
            while True:
                message = websocket.receive_json()
                messages.append(message)
                if message["event"] == "completed":
                    break

    names = [message["event"] for message in messages]
    assert names[0:2] == ["started", "analysis"]
    assert names[-1] == "completed"
    assert set(names[2:-1]) == {"chunk"}
    assert len(names[2:-1]) >= 1
    assert messages[-1]["data"]["analysis"]["optimized_prompt"] or messages[-1]["data"][
        "analysis"
    ]["prompt"]


def test_websocket_invalid_payload_returns_structured_error(tmp_path: Path) -> None:
    with _strict_client(tmp_path) as client:
        with client.websocket_connect(
            "/api/v1/optimize/ws",
            headers={"X-Rabbit-Code-Startup-Token": STARTUP_TOKEN},
        ) as websocket:
            websocket.send_json({"prompt": None})
            error = websocket.receive_json()

    assert error["event"] == "error"
    assert error["data"]["code"]
    assert error["data"]["detail"]


def test_sse_replay_does_not_repeat_provider_work(tmp_path: Path) -> None:
    with _strict_client(tmp_path) as client:
        first = client.post(
            "/api/v1/optimize/stream",
            json={"prompt": "流式结果"},
            headers={**_strict_headers(), "X-Request-ID": "rc232-sse"},
        )
        replay = client.post(
            "/api/v1/optimize/stream",
            json={"prompt": "流式结果"},
            headers={
                **_strict_headers(),
                "X-Request-ID": "rc232-sse",
                "Last-Event-ID": "1",
            },
        )

    assert first.status_code == 200
    first_events = _event_names(first.text)
    replay_events = _event_names(replay.text)
    assert first_events[0:2] == ["started", "analysis"]
    assert first_events[-1] == "completed"
    assert set(first_events[2:-1]) == {"delta"}
    assert replay_events[0] == "delta"
    assert replay_events[-1] == "completed"


def test_failing_provider_uses_offline_fallback_and_preserves_request(tmp_path: Path) -> None:
    services = _services(tmp_path)
    services.providers = ProviderRegistry(
        services.optimizer,
        providers={"offline": services.providers.get("offline"), "openai": FailingProvider()},
    )
    with TestClient(create_app(services)) as client:
        response = client.post(
            "/api/v1/optimize",
            json={"prompt": "保留原始输入", "provider": "openai"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"]["provider_requested"] == "openai"
    assert payload["metadata"]["provider_used"] == "offline"
    assert payload["metadata"]["fallback_used"] is True
    assert "保留原始输入" in payload["analysis"]["prompt"]


def test_tasks_are_authenticated_and_complete_offline(tmp_path: Path) -> None:
    with TestClient(create_app(_services(tmp_path))) as client:
        unauthorized = client.post("/api/v1/tasks/optimize", json={"prompt": "task"})
        assert unauthorized.status_code == 401

        token = client.post(
            "/api/v1/auth/register",
            json={"username": "rc232-user", "password": "secret123"},
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        created = client.post(
            "/api/v1/tasks/optimize",
            json={"prompt": "task"},
            headers=headers,
        )
        task_id = created.json()["task_id"]
        task = client.get(f"/api/v1/tasks/{task_id}", headers=headers)
        result = client.get(f"/api/v1/tasks/{task_id}/result", headers=headers)

    assert task.status_code == 200
    assert task.json()["status"] == "succeeded"
    assert result.status_code == 200
    assert "task" in result.json()["analysis"]["prompt"]


def test_local_runner_routes_share_token_boundary(tmp_path: Path) -> None:
    with _strict_client(tmp_path) as client:
        assert client.get("/api/v1/local-runners/ollama/health").status_code == 401
        health = client.get(
            "/api/v1/local-runners/ollama/health",
            headers=_strict_headers(origin=None),
        )

    assert health.status_code == 200
    assert health.json()["runner"] == "ollama"


class FailingProvider:
    name = "openai"
    capabilities = ProviderCapabilities()

    def optimize(self, request: ModelRequest) -> ModelResponse:
        raise ModelProviderError("injected provider failure")

    def stream(self, request: ModelRequest) -> Iterator[ProviderEvent]:
        raise ModelProviderError("injected provider failure")
        yield  # pragma: no cover
