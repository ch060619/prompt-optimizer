from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

from backend.rabbit_code.permissions import PermissionMode, PermissionPolicy
from backend.rabbit_code.process_tools import ProcessManager
from backend.rabbit_code.shell_tools import ShellAdapter
from backend.rabbit_code.tool_results import ToolOutcome

# RC ID: RC-096. Verify bounded output, binary metadata, retry, timeout, cancel, and partial logs.


def _adapter(tmp_path: Path) -> ShellAdapter:
    policy = PermissionPolicy(tmp_path)
    policy.switch_mode(PermissionMode.HIGH, explicit_confirmation=True)
    return ShellAdapter(tmp_path, permission_policy=policy)


def _python(code: str) -> tuple[str, ...]:
    return (sys.executable, "-u", "-c", code)


def test_large_output_is_bounded_and_marked_partial_success(tmp_path: Path) -> None:
    result = _adapter(tmp_path).run(
        _python("import sys; sys.stdout.write('x' * 100000); sys.stdout.flush()"),
        max_output_bytes=32,
        approval=True,
    )

    assert result.returncode == 0
    assert result.outcome is ToolOutcome.PARTIAL_SUCCESS
    assert result.stdout_truncated
    assert len(result.stdout) == 32
    assert result.stdout_bytes == 100000
    assert result.stdout_sha256


def test_binary_output_is_returned_as_metadata_without_decoding_failure(tmp_path: Path) -> None:
    result = _adapter(tmp_path).run(
        _python("import sys; sys.stdout.buffer.write(b'\\x00\\xffbinary'); sys.stdout.flush()"),
        approval=True,
    )

    assert result.returncode == 0
    assert result.outcome is ToolOutcome.SUCCESS
    assert result.stdout_binary
    assert result.stdout_bytes == 8
    assert "binary" in result.stdout


def test_nonzero_exit_is_a_failed_result_and_retry_is_explicit(tmp_path: Path) -> None:
    marker = tmp_path / "attempt.marker"
    code = f"""
from pathlib import Path
import sys
marker = Path({str(marker)!r})
if marker.exists():
    print('ok')
else:
    marker.write_text('1')
    sys.exit(1)
"""
    result = _adapter(tmp_path).run(
        _python(code),
        retries=1,
        retry_on=(ToolOutcome.FAILED,),
        approval=True,
    )

    assert result.returncode == 0
    assert result.outcome is ToolOutcome.SUCCESS
    assert result.retries == 1


def test_timeout_and_user_cancel_are_distinct(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path)
    timed_out = adapter.run(
        _python("import time; time.sleep(5)"),
        timeout_seconds=.05,
        approval=True,
    )
    assert timed_out.outcome is ToolOutcome.TIMED_OUT

    cancel = threading.Event()
    result_holder: list[object] = []

    def run() -> None:
        result_holder.append(
            adapter.run(
                _python("import time; time.sleep(5)"),
                timeout_seconds=2,
                cancel_event=cancel,
                approval=True,
            )
        )

    worker = threading.Thread(target=run)
    worker.start()
    time.sleep(.05)
    cancel.set()
    worker.join(timeout=2)
    result = result_holder[0]
    assert result.outcome is ToolOutcome.CANCELLED  # type: ignore[union-attr]


def test_background_log_limit_drains_output_and_keeps_cursor_readable(tmp_path: Path) -> None:
    policy = PermissionPolicy(tmp_path)
    policy.switch_mode(PermissionMode.HIGH, explicit_confirmation=True)
    manager = ProcessManager(tmp_path, permission_policy=policy, max_log_bytes=16)
    try:
        record = manager.start(
            _python("import sys; sys.stdout.write('y' * 100); sys.stdout.flush()"),
            approval=True,
        )
        finished = manager.wait(record.process_id)
        chunk = manager.read_log(record.process_id)
        assert finished.log_bytes == 100
        assert finished.log_truncated
        assert chunk.next_cursor == 16
        assert chunk.complete
        assert chunk.truncated
    finally:
        manager.close()
