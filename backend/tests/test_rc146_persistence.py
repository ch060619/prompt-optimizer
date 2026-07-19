from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from fastapi.testclient import TestClient
from pytest import fixture

from prompt_optimizer.api.app import create_app
from prompt_optimizer.core.optimizer import Optimizer
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService
from prompt_optimizer.tasks import TaskService

# RC ID: RC-146. Verify opt-in history persistence, accepted state, metadata, and owner isolation.


@fixture
def app_context(tmp_path: Path) -> Iterator[tuple[TestClient, VersionService]]:
    storage = StorageService(tmp_path / "rc146.sqlite3")
    versions = VersionService(storage)
    services = AppServices(versions=versions, tasks=TaskService(storage))
    with TestClient(create_app(services)) as client:
        yield client, versions


def register(client: TestClient, username: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": "secret123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_history_toggle_keeps_results_in_memory_without_writing(app_context) -> None:  # type: ignore[no-untyped-def]
    client, _versions = app_context
    headers = register(client, "toggle-user")

    saved = client.post(
        "/api/v1/optimize",
        json={"prompt": "写一个发布说明", "save_prompt_history": True},
        headers=headers,
    )
    assert saved.status_code == 200
    assert isinstance(saved.json()["version_id"], int)

    unsaved = client.post(
        "/api/v1/optimize",
        json={"prompt": "写一个不落盘的发布说明", "save_prompt_history": False},
        headers=headers,
    )
    assert unsaved.status_code == 200
    assert unsaved.json()["version_id"] is None
    assert unsaved.json()["analysis"]["optimized_prompt"]

    history = client.get("/api/v1/history", headers=headers)
    assert history.status_code == 200
    assert len(history.json()) == 1


def test_stream_and_background_toggle_propagate_without_history_rows(app_context) -> None:  # type: ignore[no-untyped-def]
    client, _versions = app_context
    headers = register(client, "memory-user")

    with client.stream(
        "POST",
        "/api/v1/optimize/stream",
        json={"prompt": "流式但不保存", "save_prompt_history": False},
        headers=headers,
    ) as response:
        stream_body = "".join(response.iter_text())
    assert response.status_code == 200
    assert '"version_id": null' in stream_body

    task_response = client.post(
        "/api/v1/tasks/optimize",
        json={"prompt": "后台但不保存", "save_prompt_history": False},
        headers=headers,
    )
    assert task_response.status_code == 200
    task_id = task_response.json()["task_id"]
    task_result = client.get(f"/api/v1/tasks/{task_id}/result", headers=headers)
    assert task_result.status_code == 200
    assert task_result.json()["version_id"] is None
    assert client.get("/api/v1/history", headers=headers).json() == []


def test_version_metadata_acceptance_and_delete_are_persistent_and_scoped(app_context) -> None:  # type: ignore[no-untyped-def]
    client, versions = app_context
    alice_headers = register(client, "alice146")
    bob_headers = register(client, "bob146")

    optimized = client.post(
        "/api/v1/optimize",
        json={"prompt": "保存元数据", "save_prompt_history": True},
        headers=alice_headers,
    )
    version_id = optimized.json()["version_id"]
    summary = client.get("/api/v1/history", headers=alice_headers).json()[0]
    assert summary["accepted"] is False
    assert summary["provider_used"] == "offline"
    assert summary["model"] is None
    assert summary["created_at"]
    alice_id = summary["owner_id"]

    accepted = client.post(f"/api/v1/history/{version_id}/accept", headers=alice_headers)
    assert accepted.status_code == 200
    assert accepted.json()["accepted"] is True
    assert accepted.json()["accepted_at"]
    assert client.get("/api/v1/history", headers=alice_headers).json()[0]["accepted"] is True

    bob_delete = client.delete(f"/api/v1/history/{version_id}", headers=bob_headers)
    assert bob_delete.status_code == 404
    assert versions.get(version_id, alice_id).provider_used == "offline"

    assert client.delete(f"/api/v1/history/{version_id}", headers=alice_headers).status_code == 204
    assert client.get("/api/v1/history", headers=alice_headers).json() == []


def test_provider_model_and_timestamps_survive_storage_round_trip(app_context) -> None:  # type: ignore[no-untyped-def]
    _client, versions = app_context
    analysis = Optimizer().optimize("记录 provider 和模型")
    version_id = versions.create(
        "记录 provider 和模型",
        analysis.optimized_prompt or "",
        analysis,
        owner_id=1,
        provider_used="openai",
        model="gpt-test",
    )

    version = versions.get(version_id, 1)
    summary = versions.list(1)[0]
    assert version.provider_used == "openai"
    assert version.model == "gpt-test"
    assert version.created_at.tzinfo is not None
    assert summary.provider_used == "openai"
    assert summary.model == "gpt-test"
    assert summary.created_at == version.created_at
