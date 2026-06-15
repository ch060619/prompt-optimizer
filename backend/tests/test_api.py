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
