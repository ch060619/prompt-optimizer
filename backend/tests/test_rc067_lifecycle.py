from __future__ import annotations

import json
import socket
import sys
import time
import urllib.request
from pathlib import Path

import pytest
from backend.rabbit_code import sidecar

# RC ID: RC-067. Verify startup, token handoff, health/version checks, recovery, and cleanup.


def _health(connection: sidecar.SidecarConnection) -> dict[str, object]:
    request = urllib.request.Request(
        f"{connection.base_url}/api/v1/health",
        headers=connection.headers,
    )
    with urllib.request.urlopen(request, timeout=2) as response:
        return json.loads(response.read())


def _config(tmp_path: Path, **overrides: object) -> sidecar.SidecarConfig:
    values: dict[str, object] = {
        "python_executable": sys.executable,
        "data_dir": tmp_path,
        "startup_timeout_seconds": 10.0,
        "shutdown_timeout_seconds": 2.0,
        "poll_interval_seconds": 0.05,
    }
    values.update(overrides)
    return sidecar.SidecarConfig(**values)  # type: ignore[arg-type]


def test_sidecar_starts_with_one_time_token_and_stops_cleanly(tmp_path: Path) -> None:
    manager = sidecar.SidecarManager(_config(tmp_path))
    connection = manager.start()
    try:
        assert len(connection.startup_token) >= 32
        assert _health(connection) == {
            "status": "ok",
            "protocol_version": "v1",
            "startup_token_required": True,
        }
        assert manager.is_running()
    finally:
        manager.stop()

    assert not manager.is_running()
    assert manager.connection is None


def test_sidecar_restarts_after_a_crash_with_a_new_port_and_token(tmp_path: Path) -> None:
    manager = sidecar.SidecarManager(_config(tmp_path, max_restarts=1))
    first = manager.start()
    process = manager._process
    assert process is not None
    process.kill()
    process.wait(timeout=2)

    try:
        deadline = time.perf_counter() + 5
        while time.perf_counter() < deadline and manager.restart_count == 0:
            time.sleep(0.05)
        second = manager.ensure_running()
        assert second.port != first.port
        assert second.startup_token != first.startup_token
        assert _health(second)["status"] == "ok"
        assert manager.restart_count == 1
    finally:
        manager.stop()


def test_startup_failure_reports_retry_cap_and_actionable_error(tmp_path: Path) -> None:
    manager = sidecar.SidecarManager(
        _config(
            tmp_path,
            server_module="backend.rabbit_code.module_that_does_not_exist",
            max_restarts=1,
            startup_timeout_seconds=1.0,
        )
    )

    with pytest.raises(sidecar.SidecarStartupError, match="failed after 2 attempt"):
        manager.start()

    assert not manager.is_running()
    assert manager.restart_count == 1


def test_forced_kill_without_restart_budget_reports_actionable_error(tmp_path: Path) -> None:
    manager = sidecar.SidecarManager(_config(tmp_path, max_restarts=0))
    manager.start()
    child = manager._process
    assert child is not None
    child.kill()
    child.wait(timeout=2)

    try:
        with pytest.raises(sidecar.SidecarStartupError, match="restart limit reached"):
            manager.ensure_running()
        assert manager.last_error is None
    finally:
        manager.stop()


def test_port_occupied_is_reported_without_leaving_a_sidecar(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind((sidecar.HOST, 0))
        listener.listen()
        occupied_port = int(listener.getsockname()[1])
        monkeypatch.setattr(sidecar, "reserve_loopback_port", lambda host: occupied_port)
        manager = sidecar.SidecarManager(
            _config(tmp_path, max_restarts=0, startup_timeout_seconds=1.0)
        )

        with pytest.raises(sidecar.SidecarStartupError, match="port"):
            manager.start()

    assert not manager.is_running()


def test_protocol_mismatch_is_actionable() -> None:
    manager = sidecar.SidecarManager(sidecar.SidecarConfig(protocol_version="v2"))

    with pytest.raises(sidecar.SidecarVersionMismatch, match="expected 'v2'"):
        manager._validate_health(json.dumps({"status": "ok", "protocol_version": "v1"}).encode())
