from __future__ import annotations

import json
import sys
from pathlib import Path

from backend.rabbit_code.permissions import PermissionMode, PermissionPolicy
from backend.rabbit_code.process_tools import ProcessManager, ProcessStatus
from fastapi.testclient import TestClient

from prompt_optimizer.api.app import create_app
from prompt_optimizer.local_model_state import LocalModelState, recover_state
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService

# RC ID: RC-225. Verify restart recovery for durable tasks, local models, and terminal processes.


def _python(code: str) -> tuple[str, ...]:
    return (sys.executable, "-u", "-c", code)


def _policy(tmp_path: Path) -> PermissionPolicy:
    policy = PermissionPolicy(tmp_path)
    policy.switch_mode(PermissionMode.HIGH, explicit_confirmation=True)
    return policy


def test_app_startup_marks_unfinished_tasks_failed_and_retryable(tmp_path: Path) -> None:
    storage = StorageService(tmp_path / "tasks.sqlite3")
    services = AppServices(versions=VersionService(storage))
    task = storage.create_task(
        task_id="interrupted-task",
        owner_id=1,
        kind="export",
        input_json={"version_id": 1, "format": "md"},
    )
    storage.update_task(task.id, 1, status="running")

    with TestClient(create_app(services)):
        recovered = services.tasks.get(task.id, 1)

    assert recovered.status == "failed"
    assert recovered.error is not None
    assert "restart" in recovered.error


def test_local_model_recovery_downgrades_transient_busy_state(tmp_path: Path) -> None:
    installed = tmp_path / "demo.gguf"
    installed.write_text("model", encoding="utf-8")
    state = LocalModelState(
        model_id="demo",
        runner="ollama",
        status="busy",
        installed_path=str(installed),
    )

    recovered = recover_state(
        state,
        installed_path=installed,
        runner_status="unknown",
    )

    assert recovered.status == "ready"


def test_process_manager_reconciles_running_record_and_keeps_log(tmp_path: Path) -> None:
    first = ProcessManager(tmp_path, permission_policy=_policy(tmp_path))
    record = first.start(_python("print('before-crash')"), approval=True)
    first.wait(record.process_id)
    first.close()

    registry_path = tmp_path / ".rabbit-code" / "process-logs" / "process-registry.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    payload[0]["status"] = "running"
    payload[0]["ended_at"] = None
    registry_path.write_text(json.dumps(payload), encoding="utf-8")

    second = ProcessManager(tmp_path, permission_policy=_policy(tmp_path))
    try:
        recovered = second.track(record.process_id)

        assert recovered.status is ProcessStatus.FAILED
        assert recovered.error is not None
        assert "restarted" in recovered.error
        assert "before-crash" in second.read_log(record.process_id).text
    finally:
        second.close()
