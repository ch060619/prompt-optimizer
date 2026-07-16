from __future__ import annotations

import base64
from collections.abc import Iterator
from datetime import UTC, datetime
from hashlib import pbkdf2_hmac
from pathlib import Path

from fastapi.testclient import TestClient
from pytest import fixture, raises

from prompt_optimizer.api.app import create_app
from prompt_optimizer.auth.service import AuthError, AuthService
from prompt_optimizer.core.models import UserPublic
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
    guest_response = client.post("/api/optimize", json={"prompt": "帮我写销售话术"})
    assert guest_response.status_code == 200
    assert guest_response.json()["version_id"] is None
    assert client.get("/api/history").status_code == 401

    token = client.post(
        "/api/auth/register",
        json={"username": "export-user", "password": "secret123"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/api/optimize",
        json={"prompt": "帮我写销售话术"},
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()
    version_id = payload["version_id"]
    assert isinstance(version_id, int)
    assert payload["metadata"]["provider_used"] == "offline"
    assert payload["metadata"]["fallback_used"] is False

    export_response = client.post(
        "/api/export",
        json={"version_id": version_id, "format": "md"},
        headers=headers,
    )
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


def test_api_rejects_token_for_missing_user(tmp_path: Path) -> None:
    services = AppServices()
    services.versions = VersionService(StorageService(tmp_path / "missing-user.sqlite3"))
    token = services.auth.create_token(
        UserPublic(id=999, username="missing-user", created_at=datetime.now(UTC))
    )
    headers = {"Authorization": f"Bearer {token}"}

    with TestClient(create_app(services)) as test_client:
        me_response = test_client.get("/api/auth/me", headers=headers)
        optimize_response = test_client.post(
            "/api/optimize",
            json={"prompt": "帮我写销售话术"},
            headers=headers,
        )

    assert me_response.status_code == 401
    assert optimize_response.status_code == 401


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
    token = client.post(
        "/api/auth/register",
        json={"username": "export-worker", "password": "secret123"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/api/tasks/export",
        json={"version_id": 999, "format": "md"},
        headers=headers,
    )
    assert response.status_code == 200
    task_id = response.json()["task_id"]

    result_response = client.get(f"/api/tasks/{task_id}/result", headers=headers)

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
        token = test_client.post(
            "/api/auth/register",
            json={"username": "fallback-user", "password": "secret123"},
        ).json()["access_token"]
        response = test_client.post(
            "/api/optimize",
            json={"prompt": "帮我写销售话术", "provider": "openai"},
            headers={"Authorization": f"Bearer {token}"},
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
    assert "event: completed" in body
    assert "\"version_id\": null" in body


def test_api_optimize_stream_can_use_provider_chunks(tmp_path: Path) -> None:
    services = AppServices()
    services.versions = VersionService(StorageService(tmp_path / "stream-provider.sqlite3"))
    services.providers = ProviderRegistry(
        services.optimizer,
        providers={
            "offline": services.providers.get("offline"),
            "openai": StreamingProvider(),
        },
    )
    with TestClient(create_app(services)) as test_client:
        token = test_client.post(
            "/api/auth/register",
            json={"username": "stream-user", "password": "secret123"},
        ).json()["access_token"]
        with test_client.stream(
            "POST",
            "/api/optimize/stream",
            json={"prompt": "帮我写销售话术", "provider": "openai"},
            headers={"Authorization": f"Bearer {token}"},
        ) as response:
            body = "".join(response.iter_text())

    assert response.status_code == 200
    assert 'data: {"text": "流式"}' in body
    assert 'data: {"text": "优化"}' in body
    assert '"provider_used": "openai"' in body


def test_api_rejects_remote_provider_without_login(client: TestClient) -> None:
    response = client.post(
        "/api/optimize",
        json={"prompt": "帮我写销售话术", "provider": "openai"},
    )

    assert response.status_code == 401


def test_production_requires_a_strong_jwt_secret(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("PROMPT_OPTIMIZER_ENV", "production")
    monkeypatch.delenv("PROMPT_OPTIMIZER_JWT_SECRET", raising=False)
    with raises(AuthError, match="PROMPT_OPTIMIZER_JWT_SECRET"):
        AuthService()

    monkeypatch.setenv("PROMPT_OPTIMIZER_JWT_SECRET", "too-short")
    with raises(AuthError, match="至少为 32 字节"):
        AuthService()


def test_login_rehashes_legacy_password(tmp_path: Path) -> None:
    salt = "legacy-salt"
    digest = pbkdf2_hmac("sha256", b"secret123", salt.encode("utf-8"), 120_000)
    legacy_hash = f"{salt}${base64.urlsafe_b64encode(digest).decode('ascii')}"
    services = AppServices()
    storage = StorageService(tmp_path / "legacy.sqlite3")
    services.versions = VersionService(storage)
    storage.create_user("legacy", legacy_hash)

    with TestClient(create_app(services)) as test_client:
        response = test_client.post(
            "/api/auth/login",
            json={"username": "legacy", "password": "secret123"},
        )

    stored_user = storage.get_user_by_username("legacy")
    assert response.status_code == 200
    assert stored_user is not None
    assert stored_user[1].startswith("$argon2id$")

def test_spa_deep_links_return_index_html(tmp_path: Path) -> None:
    static_dir = tmp_path / "dist"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<main>Prompt Optimizer</main>", encoding="utf-8")
    services = AppServices()
    services.versions = VersionService(StorageService(tmp_path / "spa.sqlite3"))

    with TestClient(create_app(services, static_dir)) as test_client:
        workspace_response = test_client.get("/workspace")
        login_response = test_client.get("/login")
        api_response = test_client.get("/api/not-found")
        asset_response = test_client.get("/missing.js")

    assert workspace_response.status_code == 200
    assert login_response.status_code == 200
    assert "Prompt Optimizer" in workspace_response.text
    assert api_response.status_code == 404
    assert asset_response.status_code == 404


class FailingProvider:
    name = "openai"

    def optimize(self, request: ModelRequest) -> ModelResponse:
        raise ModelProviderError("boom")

    def stream(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        raise ModelProviderError("boom")


class StreamingProvider:
    name = "openai"

    def optimize(self, request: ModelRequest) -> ModelResponse:
        raise AssertionError("streaming path should not call optimize")

    def stream(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        yield "流式"
        yield "优化"
