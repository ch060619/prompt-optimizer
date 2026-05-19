from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from fastapi.testclient import TestClient
from pytest import fixture

from prompt_optimizer.api.app import create_app
from prompt_optimizer.export.service import ExportService
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
    version_id = response.json()["version_id"]

    export_response = client.post("/api/export", json={"version_id": version_id, "format": "md"})
    assert export_response.status_code == 200
    assert "提示词优化结果" in export_response.text
