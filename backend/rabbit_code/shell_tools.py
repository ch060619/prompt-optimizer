from __future__ import annotations

import os
import shutil
import signal
import subprocess
import threading
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path

from .permissions import CapabilityDomain, PermissionPolicy
from .security import sanitize_environment, validate_argv
from .tool_results import BoundedOutput, ToolOutcome

# RC ID: RC-091. Run array commands and explicit shell scripts with bounded diagnostics.


class Shell(StrEnum):
    POWERSHELL = "powershell"
    CMD = "cmd"
    BASH = "bash"
    ZSH = "zsh"


class ShellUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class CommandResult:
    args: tuple[str, ...]
    cwd: Path
    stdout: str
    stderr: str
    returncode: int
    signal: int | None
    timed_out: bool
    stdout_bytes: int = 0
    stderr_bytes: int = 0
    stdout_sha256: str = ""
    stderr_sha256: str = ""
    stdout_truncated: bool = False
    stderr_truncated: bool = False
    stdout_binary: bool = False
    stderr_binary: bool = False
    cancelled: bool = False
    retries: int = 0

    @property
    def outcome(self) -> ToolOutcome:
        if self.cancelled:
            return ToolOutcome.CANCELLED
        if self.timed_out:
            return ToolOutcome.TIMED_OUT
        if self.returncode != 0:
            return ToolOutcome.FAILED
        if self.stdout_truncated or self.stderr_truncated:
            return ToolOutcome.PARTIAL_SUCCESS
        return ToolOutcome.SUCCESS


class ShellAdapter:
    def __init__(
        self,
        workspace_root: Path,
        *,
        permission_policy: PermissionPolicy | None = None,
    ) -> None:
        self.workspace_root = workspace_root.expanduser().resolve()
        if not self.workspace_root.is_dir():
            raise ValueError("workspace root must be a directory")
        self.permission_policy = permission_policy or PermissionPolicy(self.workspace_root)

    def run(
        self,
        args: Sequence[str],
        *,
        cwd: str | Path = ".",
        env: Mapping[str, str] | None = None,
        input_text: str | None = None,
        timeout_seconds: float = 30.0,
        encoding: str = "utf-8",
        max_output_bytes: int = 1_000_000,
        cancel_event: threading.Event | None = None,
        retries: int = 0,
        retry_delay_seconds: float = 0.0,
        retry_on: Sequence[ToolOutcome] = (ToolOutcome.TIMED_OUT,),
        approval: bool = False,
    ) -> CommandResult:
        command = _args(args)
        working_directory = self._cwd(cwd)
        self._authorize(working_directory, approval=approval)
        return self._run_with_retry(
            command,
            working_directory,
            env,
            input_text,
            timeout_seconds,
            encoding,
            max_output_bytes,
            cancel_event,
            retries,
            retry_delay_seconds,
            retry_on,
        )

    def run_script(
        self,
        script: str,
        shell: Shell,
        *,
        cwd: str | Path = ".",
        env: Mapping[str, str] | None = None,
        input_text: str | None = None,
        timeout_seconds: float = 30.0,
        encoding: str = "utf-8",
        max_output_bytes: int = 1_000_000,
        cancel_event: threading.Event | None = None,
        retries: int = 0,
        retry_delay_seconds: float = 0.0,
        retry_on: Sequence[ToolOutcome] = (ToolOutcome.TIMED_OUT,),
        approval: bool = False,
    ) -> CommandResult:
        if not isinstance(script, str) or not script:
            raise ValueError("script must be non-empty")
        working_directory = self._cwd(cwd)
        self._authorize(working_directory, approval=approval)
        command = self._shell_command(shell, script)
        return self._run_with_retry(
            command,
            working_directory,
            env,
            input_text,
            timeout_seconds,
            encoding,
            max_output_bytes,
            cancel_event,
            retries,
            retry_delay_seconds,
            retry_on,
        )

    def _run_with_retry(
        self,
        command: tuple[str, ...],
        cwd: Path,
        env: Mapping[str, str] | None,
        input_text: str | None,
        timeout_seconds: float,
        encoding: str,
        max_output_bytes: int,
        cancel_event: threading.Event | None,
        retries: int,
        retry_delay_seconds: float,
        retry_on: Sequence[ToolOutcome],
    ) -> CommandResult:
        if max_output_bytes <= 0:
            raise ValueError("max_output_bytes must be positive")
        if retries < 0:
            raise ValueError("retries must not be negative")
        if retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must not be negative")
        retryable = frozenset(retry_on)
        attempt = 0
        while True:
            result = self._execute(
                command,
                cwd,
                env,
                input_text,
                timeout_seconds,
                encoding,
                max_output_bytes,
                cancel_event,
            )
            if result.outcome not in retryable or attempt >= retries:
                return _with_retries(result, attempt)
            attempt += 1
            if retry_delay_seconds:
                time.sleep(retry_delay_seconds)

    def _execute(
        self,
        command: tuple[str, ...],
        cwd: Path,
        env: Mapping[str, str] | None,
        input_text: str | None,
        timeout_seconds: float,
        encoding: str,
        max_output_bytes: int,
        cancel_event: threading.Event | None,
    ) -> CommandResult:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        process_env = sanitize_environment(os.environ, reject_unknown=False)
        process_env.setdefault("PYTHONUTF8", "1")
        process_env.setdefault("PYTHONIOENCODING", encoding)
        if env is not None:
            process_env.update(sanitize_environment(env))
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=process_env,
                stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                start_new_session=os.name != "nt",
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
                ),
            )
        except FileNotFoundError as exc:
            raise ShellUnavailable(f"executable is unavailable: {command[0]}") from exc
        stdout_capture = BoundedOutput(max_output_bytes)
        stderr_capture = BoundedOutput(max_output_bytes)
        stdout_reader = threading.Thread(
            target=_read_stream,
            args=(process.stdout, stdout_capture),
            daemon=True,
        )
        stderr_reader = threading.Thread(
            target=_read_stream,
            args=(process.stderr, stderr_capture),
            daemon=True,
        )
        stdout_reader.start()
        stderr_reader.start()
        timed_out = False
        cancelled = False
        input_bytes = input_text.encode(encoding) if input_text is not None else None
        if input_bytes is not None and process.stdin is not None:
            try:
                process.stdin.write(input_bytes)
            except (BrokenPipeError, OSError):
                pass
            finally:
                process.stdin.close()
        deadline = time.monotonic() + timeout_seconds
        while process.poll() is None:
            if cancel_event is not None and cancel_event.is_set():
                cancelled = True
                _terminate(process)
                break
            if time.monotonic() >= deadline:
                timed_out = True
                _terminate(process)
                break
            try:
                process.wait(timeout=0.05)
            except subprocess.TimeoutExpired:
                pass
        process.wait()
        stdout_reader.join()
        stderr_reader.join()
        returncode = process.returncode
        stdout_metadata = stdout_capture.metadata()
        stderr_metadata = stderr_capture.metadata()
        return CommandResult(
            args=command,
            cwd=cwd,
            stdout=stdout_capture.text(encoding),
            stderr=stderr_capture.text(encoding),
            returncode=returncode,
            signal=-returncode if returncode < 0 else None,
            timed_out=timed_out,
            stdout_bytes=stdout_metadata.bytes_seen,
            stderr_bytes=stderr_metadata.bytes_seen,
            stdout_sha256=stdout_metadata.sha256,
            stderr_sha256=stderr_metadata.sha256,
            stdout_truncated=stdout_metadata.truncated,
            stderr_truncated=stderr_metadata.truncated,
            stdout_binary=stdout_metadata.binary,
            stderr_binary=stderr_metadata.binary,
            cancelled=cancelled,
        )

    def _shell_command(self, shell: Shell, script: str) -> tuple[str, ...]:
        if shell is Shell.POWERSHELL:
            executable = shutil.which("pwsh") or shutil.which("powershell")
            if executable is None:
                raise ShellUnavailable("PowerShell is unavailable")
            return executable, "-NoProfile", "-NonInteractive", "-Command", script
        if shell is Shell.CMD:
            executable = shutil.which("cmd.exe") or shutil.which("cmd")
            if executable is None:
                raise ShellUnavailable("cmd is unavailable")
            return executable, "/d", "/s", "/c", script
        executable = shutil.which(shell.value)
        if executable is None:
            raise ShellUnavailable(f"{shell.value} is unavailable")
        return executable, "-c", script

    def _cwd(self, cwd: str | Path) -> Path:
        raw = Path(cwd).expanduser()
        candidate = raw if raw.is_absolute() else self.workspace_root / raw
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError as exc:
            raise PermissionError("command cwd must remain within the workspace") from exc
        if not resolved.is_dir():
            raise FileNotFoundError(resolved)
        return resolved

    def _authorize(self, cwd: Path, *, approval: bool) -> None:
        decision = self.permission_policy.authorize_capability(
            CapabilityDomain.TERMINAL,
            "execute",
            {"path": cwd},
            approval=approval,
        )
        if not decision.allowed:
            raise PermissionError(decision.reason)


def _args(args: Sequence[str]) -> tuple[str, ...]:
    return validate_argv(args)


def _read_stream(stream: object, capture: BoundedOutput) -> None:
    if stream is None:
        return
    reader = stream
    while True:
        data = reader.read(8192)  # type: ignore[attr-defined]
        if not data:
            return
        capture.append(data)


def _terminate(process: subprocess.Popen[bytes]) -> None:
    if os.name == "nt":
        result = subprocess.run(
            ("taskkill", "/PID", str(process.pid), "/T", "/F"),
            capture_output=True,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode != 0:
            process.kill()
        return
    try:
        os.killpg(process.pid, signal.SIGKILL)  # type: ignore[attr-defined]
    except ProcessLookupError:
        pass


def _with_retries(result: CommandResult, retries: int) -> CommandResult:
    return replace(result, retries=retries)
