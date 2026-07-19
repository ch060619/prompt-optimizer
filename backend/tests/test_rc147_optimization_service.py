from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

from fastapi.testclient import TestClient

from prompt_optimizer.api.app import create_app
from prompt_optimizer.services import AppServices, PromptOptimizationService
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService
from prompt_optimizer.tasks import TaskService

# RC ID: RC-147. Verify one optimization service backs direct, stream, API, and task paths.


def build_services(tmp_path: Path) -> AppServices:
    storage = StorageService(tmp_path / "rc147.sqlite3")
    return AppServices(
        versions=VersionService(storage),
        tasks=TaskService(storage),
    )


def completed_payload(body: str) -> dict[str, object]:
    lines = body.splitlines()
    for index, line in enumerate(lines):
        if line == "event: completed" and index + 1 < len(lines):
            return json.loads(lines[index + 1].removeprefix("data: "))
    raise AssertionError("stream did not emit a completed event")


def test_prompt_optimization_service_has_consistent_optimize_and_stream_contract(
    tmp_path: Path,
) -> None:
    services = build_services(tmp_path)
    service = services.optimization
    assert isinstance(service, PromptOptimizationService)

    direct = service.optimize(
        original_prompt="请写一个上线检查清单",
        prompt="请写一个上线检查清单",
        template=None,
        owner_id=None,
    )
    events = list(
        service.stream(
            original_prompt="请写一个上线检查清单",
            prompt="请写一个上线检查清单",
            template=None,
            owner_id=None,
            request_id="rc147-stream",
        )
    )

    assert events[0].event == "analysis"
    assert events[-1].event == "completed"
    assert all(event.event == "chunk" for event in events[1:-1])
    streamed = events[-1].data
    assert direct.analysis.optimized_prompt == streamed.analysis.optimized_prompt
    assert direct.metadata.provider_used == streamed.metadata.provider_used


def test_prompt_optimization_service_cancel_stops_before_completed(tmp_path: Path) -> None:
    service = build_services(tmp_path).optimization
    stream: Iterator[object] = service.stream(
        original_prompt="取消这个优化",
        prompt="取消这个优化",
        template=None,
        owner_id=None,
        request_id="rc147-cancel",
    )

    first = next(stream)
    assert first.event == "analysis"
    assert service.cancel("rc147-cancel") is True
    assert list(stream) == []
    assert service.cancel("rc147-cancel") is False


def test_api_and_background_task_use_the_same_optimization_contract(tmp_path: Path) -> None:
    services = build_services(tmp_path)
    prompt = "请写一个上线检查清单"
    with TestClient(create_app(services)) as client:
        api_result = client.post(
            "/api/v1/optimize",
            json={"prompt": prompt, "save_prompt_history": False},
        )
        assert api_result.status_code == 200

        with client.stream(
            "POST",
            "/api/v1/optimize/stream",
            json={"prompt": prompt, "save_prompt_history": False},
        ) as response:
            stream_result = completed_payload("".join(response.iter_text()))

        token = client.post(
            "/api/v1/auth/register",
            json={"username": "rc147-user", "password": "secret123"},
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        task = client.post(
            "/api/v1/tasks/optimize",
            json={"prompt": prompt, "save_prompt_history": False},
            headers=headers,
        )
        task_result = client.get(
            f"/api/v1/tasks/{task.json()['task_id']}/result",
            headers=headers,
        ).json()

    expected = api_result.json()["analysis"]["optimized_prompt"]
    assert stream_result["analysis"]["optimized_prompt"] == expected
    assert task_result["analysis"]["optimized_prompt"] == expected
