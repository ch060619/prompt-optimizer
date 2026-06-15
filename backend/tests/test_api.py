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
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService


@fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    services = AppServices()
    services.versions = VersionService(StorageService(tmp_path / "api.sqlite3"))
    services.export = ExportService()
    with TestClient(create_app(services)) as test_client:
        yield test_client


def test_api_analyze(client: TestClient) -> None:
    response = client.post(
        "/api/analyze",
        json={"prompt": "你是一名老师，请解释机器学习，输出格式为列表。"},
    )
    assert response.status_code == 200
    assert response.json()["score"]["total_score"] >= 0


def test_api_templates(client: TestClient) -> None:
    response = client.get("/api/templates?category=business")
    assert response.status_code == 200
    assert response.json()


def test_api_optimize_and_export(client: TestClient) -> None:
    response = client.post("/api/optimize", json={"prompt": "帮我写销售话术"})
    assert response.status_code == 200
    payload = response.json()
    version_id = payload["version_id"]
    assert payload["metadata"]["provider_used"] == "offline"
    assert payload["metadata"]["fallback_used"] is False

    export_response = client.post("/api/export", json={"version_id": version_id, "format": "md"})
    assert export_response.status_code == 200
    assert "提示词优化结果" in export_response.text


def test_api_auth_register_login_and_me(client: TestClient) -> None:
    register_response = client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "secret123"},
    )
    assert register_response.status_code == 200
    token = register_response.json()["access_token"]

    me_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "alice"

    login_response = client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "secret123"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["user"]["username"] == "alice"


def test_api_history_is_scoped_to_current_user(client: TestClient) -> None:
    alice_token = client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "secret123"},
    ).json()["access_token"]
    bob_token = client.post(
        "/api/auth/register",
        json={"username": "bob", "password": "secret123"},
    ).json()["access_token"]

    response = client.post(
        "/api/optimize",
        json={"prompt": "帮我写销售话术"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert response.status_code == 200
    version_id = response.json()["version_id"]

    alice_history = client.get("/api/history", headers={"Authorization": f"Bearer {alice_token}"})
    bob_history = client.get("/api/history", headers={"Authorization": f"Bearer {bob_token}"})
    bob_version = client.get(
        f"/api/history/{version_id}",
        headers={"Authorization": f"Bearer {bob_token}"},
    )

    assert len(alice_history.json()) == 1
    assert bob_history.json() == []
    assert bob_version.status_code == 404


def test_api_projects_returns_default_space(client: TestClient) -> None:
    token = client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "secret123"},
    ).json()["access_token"]

    response = client.get("/api/projects", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()[0]["name"] == "默认项目"


def test_api_rejects_invalid_auth_header(client: TestClient) -> None:
    response = client.get("/api/auth/me", headers={"Authorization": "bad-token"})

    assert response.status_code == 401


def test_api_optimize_task_succeeds(client: TestClient) -> None:
    token = client.post(
        "/api/auth/register",
        json={"username": "worker", "password": "secret123"},
    ).json()["access_token"]
    response = client.post(
        "/api/tasks/optimize",
        json={"prompt": "帮我写销售话术"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    task_id = response.json()["task_id"]

    task_response = client.get(
        f"/api/tasks/{task_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    result_response = client.get(
        f"/api/tasks/{task_id}/result",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert task_response.json()["status"] == "succeeded"
    assert result_response.json()["version_id"] >= 1


def test_api_export_task_requires_finished_task(client: TestClient) -> None:
    response = client.post("/api/tasks/export", json={"version_id": 999, "format": "md"})
    assert response.status_code == 200
    task_id = response.json()["task_id"]

    result_response = client.get(f"/api/tasks/{task_id}/result")

    assert result_response.status_code == 409


def test_api_evaluate_task_is_user_scoped(client: TestClient) -> None:
    alice_token = client.post(
        "/api/auth/register",
        json={"username": "alice2", "password": "secret123"},
    ).json()["access_token"]
    bob_token = client.post(
        "/api/auth/register",
        json={"username": "bob2", "password": "secret123"},
    ).json()["access_token"]
    response = client.post(
        "/api/tasks/evaluate",
        json={"prompts": ["帮我写销售话术"], "provider": "offline"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    task_id = response.json()["task_id"]

    alice_task = client.get(
        f"/api/tasks/{task_id}",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    bob_task = client.get(f"/api/tasks/{task_id}", headers={"Authorization": f"Bearer {bob_token}"})

    assert alice_task.json()["status"] == "succeeded"
    assert bob_task.status_code == 404


def test_api_optimize_falls_back_to_offline_provider(tmp_path: Path) -> None:
    services = AppServices()
    services.versions = VersionService(StorageService(tmp_path / "fallback.sqlite3"))
    services.providers = ProviderRegistry(
        services.optimizer,
        providers={
            "offline": services.providers.get("offline"),
            "openai": FailingProvider(),
        },
    )
    with TestClient(create_app(services)) as test_client:
        response = test_client.post(
            "/api/optimize",
            json={"prompt": "帮我写销售话术", "provider": "openai"},
        )

    assert response.status_code == 200
    metadata = response.json()["metadata"]
    assert metadata["provider_requested"] == "openai"
    assert metadata["provider_used"] == "offline"
    assert metadata["fallback_used"] is True
    assert "boom" in metadata["error_summary"]


def test_api_optimize_stream_emits_sse_events(client: TestClient) -> None:
    with client.stream(
        "POST",
        "/api/optimize/stream",
        json={"prompt": "帮我写销售话术", "provider": "offline"},
    ) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    assert "event: started" in body
    assert "event: analysis" in body
    assert "event: chunk" in body
    assert "event: saved" in body
    assert "event: completed" in body


class FailingProvider:
    name = "openai"

    def optimize(self, request: ModelRequest) -> ModelResponse:
        raise ModelProviderError("boom")
