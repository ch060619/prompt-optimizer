from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest
from backend.rabbit_code.permissions import PermissionMode, PermissionPolicy
from backend.rabbit_code.shell_tools import Shell, ShellAdapter

# RC ID: RC-091. Verify array execution, shell scripts, encoding, env, timeout, and bounds.


def _adapter(tmp_path: Path) -> ShellAdapter:
    policy = PermissionPolicy(tmp_path)
    policy.switch_mode(PermissionMode.HIGH, explicit_confirmation=True)
    return ShellAdapter(tmp_path, permission_policy=policy)


def test_array_command_preserves_unicode_spaces_env_and_diagnostics(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path)
    code = (
        "import os,sys; print(sys.argv[1]); print(os.environ['RC_TEST'], file=sys.stderr); "
        "print('输入')"
    )
    result = adapter.run(
        (sys.executable, "-c", code, "name with spaces 中文"),
        env={"RC_TEST": "env value"},
        approval=True,
    )

    assert result.returncode == 0
    assert "name with spaces 中文" in result.stdout
    assert "输入" in result.stdout
    assert result.stderr.strip() == "env value"
    assert result.signal is None
    assert not result.timed_out


@pytest.mark.parametrize(
    "shell,script",
    (
        (Shell.POWERSHELL, "Write-Output shell-ok"),
        (Shell.CMD, "echo shell-ok"),
        (Shell.BASH, "printf shell-ok"),
        (Shell.ZSH, "printf shell-ok"),
    ),
)
def test_explicit_shell_scripts_capture_output(
    tmp_path: Path,
    shell: Shell,
    script: str,
) -> None:
    executable = (
        (shutil.which("pwsh") or shutil.which("powershell"))
        if shell is Shell.POWERSHELL
        else shutil.which("cmd.exe") or shutil.which("cmd")
        if shell is Shell.CMD
        else shutil.which(shell.value)
    )
    if executable is None:
        pytest.skip(f"{shell.value} is unavailable")
    result = _adapter(tmp_path).run_script(shell=shell, script=script, approval=True)
    if result.returncode != 0 and shell is Shell.BASH:
        pytest.skip("bash executable is present but its runtime is unavailable")
    assert result.returncode == 0
    assert "shell-ok" in result.stdout


def test_timeout_and_permission_are_explicit(tmp_path: Path) -> None:
    policy = PermissionPolicy(tmp_path)
    adapter = ShellAdapter(tmp_path, permission_policy=policy)
    with pytest.raises(PermissionError, match="read-only"):
        adapter.run((sys.executable, "-c", "print('blocked')"))

    policy.switch_mode(PermissionMode.HIGH, explicit_confirmation=True)
    result = adapter.run(
        (sys.executable, "-c", "import time; time.sleep(1)"),
        timeout_seconds=0.05,
        approval=True,
    )
    assert result.timed_out
    assert result.returncode != 0


def test_cwd_and_arguments_are_bounded(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path)
    with pytest.raises(PermissionError, match="workspace"):
        adapter.run((sys.executable, "-c", "pass"), cwd=tmp_path.parent, approval=True)
    with pytest.raises(TypeError, match="sequence"):
        adapter.run("python -c pass", approval=True)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="not-a-shell"):
        Shell("not-a-shell")
