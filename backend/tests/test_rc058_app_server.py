from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from fastapi.testclient import TestClient
from pytest import fixture

from prompt_optimizer.api.app import create_app_server
from prompt_optimizer.export.service import ExportService
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService

# RC ID: RC-058. Verify the strict versioned App Server boundary and startup token.


@fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    services = AppServices()
    services.versions = VersionService(StorageService(tmp_path / "rc058.sqlite3"))
    services.export = ExportService()
    with TestClient(create_app_server(services, startup_token="test-start")) as test_client:
        yield test_client


def test_app_server_health_is_public_and_reports_protocol(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "protocol_version": "v1",
        "startup_token_required": True,
    }
    assert response.headers["X-Rabbit-Code-Protocol"] == "v1"


def test_app_server_requires_startup_token_for_business_routes(client: TestClient) -> None:
    request = {"prompt": "请用列表解释机器学习。"}

    assert client.post("/api/v1/analyze", json=request).status_code == 401
    response = client.post(
        "/api/v1/analyze",
        json=request,
        headers={
            "X-Rabbit-Code-Startup-Token": "test-start",
            "X-Rabbit-Code-Protocol": "v1",
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Rabbit-Code-Protocol"] == "v1"


def test_app_server_rejects_unknown_protocol_and_has_no_legacy_duplicate_paths(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/analyze",
        json={"prompt": "测试协议版本。"},
        headers={
            "X-Rabbit-Code-Startup-Token": "test-start",
            "X-Rabbit-Code-Protocol": "v9",
        },
    )

    assert response.status_code == 426
    paths = set(client.get("/openapi.json").json()["paths"])
    assert "/api/analyze" not in paths
    assert "/api/v1/analyze" in paths
