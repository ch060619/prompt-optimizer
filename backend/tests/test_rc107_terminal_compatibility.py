from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest
from backend.rabbit_code.permissions import PermissionMode, PermissionPolicy
from backend.rabbit_code.shell_tools import Shell, ShellAdapter, ShellUnavailable
from backend.rabbit_code.terminal_compatibility import (
    TerminalKind,
    clipboard_status,
    detect_terminal_matrix,
)
from backend.rabbit_code.tui import TuiRenderer, TuiState

# RC ID: RC-107. Verify mainstream terminal shells, dimensions, signals, paths, and limits.


def _adapter(tmp_path: Path) -> ShellAdapter:
    policy = PermissionPolicy(tmp_path)
    policy.switch_mode(PermissionMode.HIGH, explicit_confirmation=True)
    return ShellAdapter(tmp_path, permission_policy=policy)


def test_terminal_matrix_reports_available_and_unavailable_surfaces_explicitly() -> None:
    matrix = {item.kind: item for item in detect_terminal_matrix()}

    assert set(matrix) == set(TerminalKind)
    for kind in (TerminalKind.POWERSHELL, TerminalKind.CMD, TerminalKind.WSL):
        if not matrix[kind].available:
            pytest.skip(matrix[kind].reason)
    if not matrix[TerminalKind.WINDOWS_TERMINAL].interactive:
        assert "WT_SESSION" in matrix[TerminalKind.WINDOWS_TERMINAL].reason
    if not matrix[TerminalKind.LINUX].available:
        assert "Windows host" in matrix[TerminalKind.LINUX].reason


@pytest.mark.parametrize(
    ("shell", "script"),
    (
        (Shell.POWERSHELL, "Write-Output 'input with spaces 中文'"),
        (Shell.CMD, "echo input with spaces 中文"),
    ),
)
def test_native_windows_shells_preserve_input_and_ansi_output(
    tmp_path: Path,
    shell: Shell,
    script: str,
) -> None:
    try:
        input_result = _adapter(tmp_path).run_script(script, shell, approval=True)
    except ShellUnavailable as exc:
        pytest.skip(str(exc))
    assert input_result.returncode == 0
    assert "input with spaces 中文" in input_result.stdout

    color_result = _adapter(tmp_path).run(
        (
            sys.executable,
            "-c",
            "print('\\x1b[31mcolor\\x1b[0m')",
        ),
        approval=True,
    )
    assert color_result.returncode == 0
    assert "\x1b[31mcolor\x1b[0m" in color_result.stdout


def test_tui_width_height_and_unicode_path_are_stable(tmp_path: Path) -> None:
    state = TuiState(prompt="输入 with spaces", output=["输出"], status="running")
    rendered = TuiRenderer.render(state, width=36, height=10)
    assert all(len(line) <= 36 for line in rendered.splitlines())

    working_directory = tmp_path / "中文 terminal path"
    working_directory.mkdir()
    result = _adapter(tmp_path).run(
        (sys.executable, "-c", "import os; print(os.getcwd())"),
        cwd=working_directory,
        approval=True,
    )
    assert result.returncode == 0
    assert str(working_directory.resolve()) in result.stdout


def test_cancel_signal_is_reported_without_waiting_for_child_exit(tmp_path: Path) -> None:
    cancel = threading.Event()
    timer = threading.Timer(0.05, cancel.set)
    timer.start()
    try:
        result = _adapter(tmp_path).run(
            (sys.executable, "-c", "import time; time.sleep(5)"),
            cancel_event=cancel,
            timeout_seconds=2,
            approval=True,
        )
    finally:
        timer.cancel()
    assert result.cancelled
    assert result.returncode != 0


def test_wsl_linux_shell_probe_when_available() -> None:
    matrix = {item.kind: item for item in detect_terminal_matrix()}
    if not matrix[TerminalKind.WSL].available:
        pytest.skip(matrix[TerminalKind.WSL].reason)
    result = subprocess.run(
        ("wsl", "-e", "sh", "-lc", "printf 'linux-input:%s\\n' '中文 path'"),
        capture_output=True,
        encoding="utf-8",
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0
    assert "linux-input:中文 path" in result.stdout


def test_clipboard_limit_is_explicit_when_no_interactive_session_exists() -> None:
    available, reason = clipboard_status()
    if not available:
        pytest.skip(reason)
    assert os.environ.get("WT_SESSION") or sys.platform == "linux"
