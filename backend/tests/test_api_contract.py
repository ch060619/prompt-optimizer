from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pytest import fixture

from prompt_optimizer.api.app import create_app
from prompt_optimizer.export.service import ExportService
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService

# RC ID: RC-048. Contract tests cover legacy and versioned FastAPI clients.

ROOT = Path(__file__).parents[2]
API_PREFIXES = ("/api", "/api/v1")
API_PATHS = (
    "/analyze",
    "/auth/register",
    "/auth/login",
    "/auth/me",
    "/projects",
    "/optimize",
    "/optimize/stream",
    "/tasks/optimize",
    "/tasks/export",
    "/tasks/evaluate",
    "/tasks/{task_id}",
    "/tasks/{task_id}/result",
    "/templates",
    "/templates/{template_id}",
    "/history",
    "/history/{version_id}",
    "/history/{version_id}/diff/{other_id}",
    "/export",
)


@fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    services = AppServices()
    services.versions = VersionService(StorageService(tmp_path / "api-contract.sqlite3"))
    services.export = ExportService()
    with TestClient(create_app(services)) as test_client:
        yield test_client


def _register(client: TestClient, username: str = "contract-user") -> dict[str, Any]:
    response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": "secret123"},
    )
    assert response.status_code == 200
    return response.json()


def test_openapi_contains_legacy_and_versioned_paths(client: TestClient) -> None:
    document = client.get("/openapi.json").json()

    assert document["openapi"].startswith("3.")
    assert document["info"]["version"] == "2.0.0"
    assert document["x-api-version"] == "v1"
    assert set(document["components"]["schemas"]) >= {
        "AnalyzeRequest",
        "AuthRequest",
        "AuthResponse",
        "DiffResult",
        "EvaluateTaskRequest",
        "ExportRequest",
        "OptimizeRequest",
        "OptimizeResponse",
        "ProjectSpace",
        "PromptAnalysis",
        "PromptTemplate",
        "PromptVersion",
        "TaskCreateResponse",
        "TaskRecord",
        "UserPublic",
        "VersionSummary",
    }
    for prefix in API_PREFIXES:
        assert {f"{prefix}{path}" for path in API_PATHS} <= set(document["paths"])


def test_exported_openapi_is_generated_from_the_app(client: TestClient) -> None:
    exported = json.loads((ROOT / "docs/api/openapi-v1.json").read_text(encoding="utf-8"))

    assert exported == client.get("/openapi.json").json()


@pytest.mark.parametrize("prefix", API_PREFIXES)
def test_analyze_contract_is_available_during_compatibility_window(
    client: TestClient,
    prefix: str,
) -> None:
    response = client.post(
        f"{prefix}/analyze",
        json={"prompt": "请用列表解释机器学习。"},
    )

    assert response.status_code == 200
    assert response.json()["score"]["total_score"] >= 0


def test_versioned_optimize_stream_task_auth_project_and_version_contracts(
    client: TestClient,
) -> None:
    auth = _register(client)
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    me = client.get("/api/v1/auth/me", headers=headers)
    projects = client.get("/api/v1/projects", headers=headers)
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "contract-user", "password": "secret123"},
    )
    optimized = client.post(
        "/api/v1/optimize",
        json={"prompt": "请写一段销售话术。"},
        headers=headers,
    )
    task = client.post(
        "/api/v1/tasks/optimize",
        json={"prompt": "请写一段任务话术。"},
        headers=headers,
    )
    history = client.get("/api/v1/history", headers=headers)

    assert me.status_code == 200
    assert me.json()["username"] == "contract-user"
    assert projects.status_code == 200
    assert projects.json()[0]["owner_id"] == me.json()["id"]
    assert login.status_code == 200
    assert login.json()["user"]["username"] == "contract-user"
    assert optimized.status_code == 200
    version_id = optimized.json()["version_id"]
    assert isinstance(version_id, int)
    assert task.status_code == 200
    task_id = task.json()["task_id"]
    assert client.get(f"/api/v1/tasks/{task_id}", headers=headers).json()["status"] == "succeeded"
    assert client.get(f"/api/v1/tasks/{task_id}/result", headers=headers).status_code == 200
    assert history.status_code == 200
    assert version_id in {item["id"] for item in history.json()}
    assert client.get(f"/api/v1/history/{version_id}", headers=headers).status_code == 200

    with client.stream(
        "POST",
        "/api/v1/optimize/stream",
        json={"prompt": "请流式优化这段话。"},
        headers=headers,
    ) as stream_response:
        body = "".join(stream_response.iter_text())
    assert stream_response.status_code == 200
    assert "event: started" in body
    assert "event: completed" in body


def test_legacy_auth_and_versioned_validation_errors_remain_compatible(
    client: TestClient,
) -> None:
    assert client.get("/api/history").status_code == 401
    assert client.get("/api/v1/history").status_code == 401

    for prefix in API_PREFIXES:
        response = client.post(f"{prefix}/analyze", json={})
        assert response.status_code == 422
