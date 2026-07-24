from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from prompt_optimizer.api.app import create_app
from prompt_optimizer.core.models import ExecutionDestination
from prompt_optimizer.providers import (
    OpenAICompatibleAdapter,
    ProviderConfig,
    ProviderRegistry,
)
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService

# RC ID: RC-216. Verify local/cloud destination disclosure before provider calls.


def _services(tmp_path: Path) -> AppServices:
    services = AppServices()
    services.versions = VersionService(StorageService(tmp_path / "destination.sqlite3"))
    offline = services.providers.get("offline")
    cloud = OpenAICompatibleAdapter(
        ProviderConfig(
            name="openai",
            base_url="https://api.example.test/v1",
            api_key="runtime-key",
            model="gpt-test",
            authorized=True,
        )
    )
    services.providers = ProviderRegistry(
        services.optimizer,
        providers={"offline": offline, "openai": cloud},
    )
    return services


def test_destination_endpoint_discloses_local_and_cloud_targets(tmp_path: Path) -> None:
    with TestClient(create_app(_services(tmp_path))) as client:
        local_response = client.post(
            "/api/v1/execution-destination",
            json={"provider": "offline"},
        )
        cloud_response = client.post(
            "/api/v1/execution-destination",
            json={"provider": "openai", "model": "gpt-test"},
        )

    assert local_response.status_code == 200
    assert cloud_response.status_code == 200
    local = ExecutionDestination.model_validate(local_response.json())
    cloud = ExecutionDestination.model_validate(cloud_response.json())
    assert local.execution_location == "local"
    assert local.network_access is False
    assert local.target_service == "本机"
    assert cloud.execution_location == "cloud"
    assert cloud.network_access is True
    assert cloud.target_service == "OpenAI Compatible"
    assert cloud.target_host == "api.example.test"


def test_optimize_response_keeps_destination_metadata(tmp_path: Path) -> None:
    with TestClient(create_app(_services(tmp_path))) as client:
        response = client.post("/api/v1/optimize", json={"prompt": "写一个摘要"})

    assert response.status_code == 200
    destination = response.json()["metadata"]["destination"]
    assert destination["execution_location"] == "local"
    assert destination["network_access"] is False
    assert destination["target_service"] == "本机"
