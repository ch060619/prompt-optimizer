from __future__ import annotations

import socket
import sys
import time
from pathlib import Path

import pytest
from backend.rabbit_code.permissions import PermissionMode, PermissionPolicy
from backend.rabbit_code.process_tools import (
    ProcessManager,
    ProcessStatus,
    PtyUnavailable,
)

# RC ID: RC-094. Verify registration, background logs, ports, timeout, and tree cleanup.


def _manager(tmp_path: Path) -> ProcessManager:
    policy = PermissionPolicy(tmp_path)
    policy.switch_mode(PermissionMode.HIGH, explicit_confirmation=True)
    return ProcessManager(tmp_path, permission_policy=policy)


def _python(code: str) -> tuple[str, ...]:
    return (sys.executable, "-u", "-c", code)


def test_concurrent_processes_are_registered_and_logs_are_cursor_readable(
    tmp_path: Path,
) -> None:
    manager = _manager(tmp_path)
    try:
        first = manager.start(
            _python("import time; print('first'); time.sleep(.15); print('first-done')"),
            timeout_seconds=2,
            approval=True,
        )
        second = manager.start(
            _python("import time; print('second'); time.sleep(.05); print('second-done')"),
            timeout_seconds=2,
            approval=True,
        )
        assert first.process_id != second.process_id
        assert {item.process_id for item in manager.processes} == {
            first.process_id,
            second.process_id,
        }
        completed = manager.wait(first.process_id)
        assert completed.status is ProcessStatus.EXITED
        chunk = manager.read_log(first.process_id, max_bytes=7)
        assert chunk.text.replace("\r\n", "\n") == "first\n"
        tail = manager.read_log(first.process_id, cursor=chunk.next_cursor)
        assert "first-done" in tail.text
        assert tail.complete
        assert manager.wait(second.process_id).status is ProcessStatus.EXITED
    finally:
        manager.close()


def test_timeout_and_stop_terminate_the_process_tree(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    try:
        timed_out = manager.start(
            _python("import time; print('before-timeout'); time.sleep(5)"),
            timeout_seconds=.1,
            approval=True,
        )
        assert manager.wait(timed_out.process_id).status is ProcessStatus.TIMED_OUT

        stopped = manager.start(_python("import time; time.sleep(5)"), approval=True)
        result = manager.stop(stopped.process_id)
        assert result.status is ProcessStatus.STOPPED
        assert result.returncode is not None
        assert manager.track(stopped.process_id).ended_at is not None
    finally:
        manager.close()


def test_port_probe_is_independent_from_process_registry(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen()
    try:
        port = server.getsockname()[1]
        occupied = manager.probe_port(port)
        free = manager.probe_port(port + 1)
        assert occupied.occupied
        assert not free.occupied
        assert not manager.processes
    finally:
        server.close()
        manager.close()


def test_pty_unavailability_is_explicit_on_windows(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    try:
        if sys.platform == "win32":
            with pytest.raises(PtyUnavailable, match="unavailable"):
                manager.start(_python("print('no fake pty')"), pty=True, approval=True)
        else:
            record = manager.start(_python("print('pty-ok')"), pty=True, approval=True)
            assert manager.wait(record.process_id).status is ProcessStatus.EXITED
    finally:
        manager.close()


def test_wait_timeout_stops_without_leaving_a_running_record(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    try:
        record = manager.start(_python("import time; time.sleep(5)"), approval=True)
        finished = manager.wait(record.process_id, timeout_seconds=.05)
        assert finished.status is ProcessStatus.TIMED_OUT
        time.sleep(.05)
        assert manager.track(record.process_id).status is ProcessStatus.TIMED_OUT
    finally:
        manager.close()
