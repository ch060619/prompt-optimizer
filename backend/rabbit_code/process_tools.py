from __future__ import annotations

import ctypes
import os
import shutil
import signal
import socket
import subprocess
import threading
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from .permissions import CapabilityDomain, PermissionPolicy
from .sandbox import SandboxController
from .security import sanitize_environment, validate_argv
from .shell_tools import Shell

# RC ID: RC-094. Manage bounded background processes and cursor-based logs.


class ProcessToolError(RuntimeError):
    pass


class ProcessNotFound(ProcessToolError, KeyError):
    pass


class PtyUnavailable(ProcessToolError):
    pass


class ProcessStatus(StrEnum):
    STARTING = "starting"
    RUNNING = "running"
    EXITED = "exited"
    STOPPED = "stopped"
    TIMED_OUT = "timed_out"
    FAILED = "failed"


@dataclass(frozen=True)
class ProcessRecord:
    process_id: str
    pid: int
    command: tuple[str, ...]
    cwd: Path
    pty: bool
    status: ProcessStatus
    timeout_seconds: float | None
    log_path: Path
    started_at: float
    ended_at: float | None = None
    returncode: int | None = None
    termination_signal: int | None = None
    error: str | None = None
    log_bytes: int = 0
    log_truncated: bool = False
    binary_output: bool = False

    @property
    def args(self) -> tuple[str, ...]:
        return self.command

    @property
    def state(self) -> ProcessStatus:
        return self.status


@dataclass(frozen=True)
class LogChunk:
    process_id: str
    cursor: int
    next_cursor: int
    text: str
    complete: bool
    truncated: bool = False
    binary: bool = False


@dataclass(frozen=True)
class PortStatus:
    host: str
    port: int
    occupied: bool
    error: str | None = None


class _ManagedProcess:
    def __init__(
        self,
        record: ProcessRecord,
        process: subprocess.Popen[bytes],
        log_handle: Any,
        reader_fd: int | None,
    ) -> None:
        self.record = record
        self.process = process
        self.log_handle = log_handle
        self.reader_fd = reader_fd
        self.lock = threading.RLock()
        self.done = threading.Event()
        self.reader_done = threading.Event()
        self.log_bytes = 0
        self.log_truncated = False
        self.binary_output = False
        self.stop_requested = False
        self.timeout_requested = False
        self.reader_thread: threading.Thread | None = None
        self.watcher_thread: threading.Thread | None = None


class ProcessRegistry:
    """Thread-safe in-memory registry retaining terminal process states."""

    def __init__(self) -> None:
        self._items: dict[str, _ManagedProcess] = {}
        self._lock = threading.RLock()

    def add(self, item: _ManagedProcess) -> None:
        with self._lock:
            self._items[item.record.process_id] = item

    def get(self, process_id: str) -> _ManagedProcess:
        with self._lock:
            try:
                return self._items[process_id]
            except KeyError as exc:
                raise ProcessNotFound(process_id) from exc

    def values(self) -> tuple[_ManagedProcess, ...]:
        with self._lock:
            return tuple(self._items.values())


class ProcessManager:
    def __init__(
        self,
        workspace_root: Path,
        *,
        log_dir: Path | None = None,
        permission_policy: PermissionPolicy | None = None,
        max_log_bytes: int = 10_000_000,
        sandbox: SandboxController | None = None,
    ) -> None:
        self.workspace_root = workspace_root.expanduser().resolve()
        if not self.workspace_root.is_dir():
            raise ValueError("workspace root must be a directory")
        self.permission_policy = permission_policy or PermissionPolicy(self.workspace_root)
        self.sandbox = sandbox
        if max_log_bytes <= 0:
            raise ValueError("max_log_bytes must be positive")
        self.max_log_bytes = max_log_bytes
        self.log_dir = (
            log_dir or self.workspace_root / ".rabbit-code" / "process-logs"
        ).expanduser()
        self.log_dir = self.log_dir.resolve()
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.registry = ProcessRegistry()
        self._job = _WindowsJob()
        self._closed = False

    @property
    def processes(self) -> tuple[ProcessRecord, ...]:
        return tuple(self.track(item.record.process_id) for item in self.registry.values())

    def start(
        self,
        args: Sequence[str],
        *,
        cwd: str | Path = ".",
        env: Mapping[str, str] | None = None,
        pty: bool = False,
        timeout_seconds: float | None = None,
        encoding: str = "utf-8",
        approval: bool = False,
    ) -> ProcessRecord:
        command = _args(args)
        if timeout_seconds is not None and timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if pty and not _pty_available():
            raise PtyUnavailable("PTY mode is unavailable on this platform")
        working_directory = self._cwd(cwd)
        self._authorize(working_directory, approval=approval)
        launch_command = command
        launch_env = env
        if self.sandbox is not None:
            launch = self.sandbox.prepare(
                launch_command,
                cwd=working_directory,
                env=env,
                approval=approval,
            )
            launch_command = launch.command
            working_directory = launch.cwd
            launch_env = launch.env
        process_id = f"proc-{uuid4().hex}"
        log_path = self.log_dir / f"{process_id}.log"
        log_handle = log_path.open("ab")
        try:
            process, reader_fd = self._spawn(
                launch_command,
                working_directory,
                launch_env,
                pty=pty,
                encoding=encoding,
            )
            self._job.assign(process)
        except Exception:
            log_handle.close()
            log_path.unlink(missing_ok=True)
            raise
        record = ProcessRecord(
            process_id=process_id,
            pid=process.pid,
            command=command,
            cwd=working_directory,
            pty=pty,
            status=ProcessStatus.RUNNING,
            timeout_seconds=timeout_seconds,
            log_path=log_path,
            started_at=time.time(),
        )
        item = _ManagedProcess(record, process, log_handle, reader_fd)
        self.registry.add(item)
        item.reader_thread = threading.Thread(
            target=self._read_output,
            args=(item, encoding),
            name=f"rabbit-process-reader-{process_id}",
            daemon=True,
        )
        item.watcher_thread = threading.Thread(
            target=self._watch_process,
            args=(item,),
            name=f"rabbit-process-watcher-{process_id}",
            daemon=True,
        )
        item.reader_thread.start()
        item.watcher_thread.start()
        return record

    def start_script(
        self,
        script: str,
        shell: Shell,
        *,
        cwd: str | Path = ".",
        env: Mapping[str, str] | None = None,
        pty: bool = False,
        timeout_seconds: float | None = None,
        encoding: str = "utf-8",
        approval: bool = False,
    ) -> ProcessRecord:
        if not isinstance(script, str) or not script:
            raise ValueError("script must be non-empty")
        return self.start(
            self._shell_command(shell, script),
            cwd=cwd,
            env=env,
            pty=pty,
            timeout_seconds=timeout_seconds,
            encoding=encoding,
            approval=approval,
        )

    def track(self, process_id: str) -> ProcessRecord:
        item = self.registry.get(process_id)
        with item.lock:
            return item.record

    def wait(self, process_id: str, timeout_seconds: float | None = None) -> ProcessRecord:
        if timeout_seconds is not None and timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        item = self.registry.get(process_id)
        if not item.done.wait(timeout_seconds):
            self._terminate(item, timed_out=True)
            item.done.wait()
        return self.track(process_id)

    def read_log(
        self,
        process_id: str,
        *,
        cursor: int = 0,
        max_bytes: int = 64 * 1024,
        encoding: str = "utf-8",
    ) -> LogChunk:
        if cursor < 0:
            raise ValueError("cursor must not be negative")
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        item = self.registry.get(process_id)
        with item.lock:
            size = item.record.log_path.stat().st_size
            if cursor > size:
                raise ValueError("cursor is beyond the end of the log")
            with item.record.log_path.open("rb") as handle:
                handle.seek(cursor)
                data = handle.read(max_bytes)
            next_cursor = cursor + len(data)
            complete = item.done.is_set() and next_cursor >= size
            truncated = item.log_truncated
            binary = item.binary_output
        return LogChunk(
            process_id=process_id,
            cursor=cursor,
            next_cursor=next_cursor,
            text=data.decode(encoding, errors="replace"),
            complete=complete,
            truncated=truncated,
            binary=binary,
        )

    def stop(self, process_id: str, *, force: bool = True) -> ProcessRecord:
        item = self.registry.get(process_id)
        if item.done.is_set():
            return self.track(process_id)
        self._terminate(item, force=force)
        item.done.wait()
        return self.track(process_id)

    def probe_port(
        self,
        port: int,
        *,
        host: str = "127.0.0.1",
        timeout_seconds: float = 0.2,
    ) -> PortStatus:
        if not 1 <= port <= 65535:
            raise ValueError("port must be between 1 and 65535")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        try:
            addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except OSError as exc:
            return PortStatus(host, port, False, str(exc))
        for family, socket_type, protocol, _, address in addresses:
            try:
                with socket.socket(family, socket_type, protocol) as connection:
                    connection.settimeout(timeout_seconds)
                    if connection.connect_ex(address) == 0:
                        return PortStatus(host, port, True)
            except OSError:
                continue
        return PortStatus(host, port, False)

    def cleanup(self) -> tuple[ProcessRecord, ...]:
        results: list[ProcessRecord] = []
        for item in self.registry.values():
            if not item.done.is_set():
                self._terminate(item)
            item.done.wait()
            results.append(self.track(item.record.process_id))
        return tuple(results)

    def close(self) -> None:
        if self._closed:
            return
        self.cleanup()
        self._job.close()
        self._closed = True

    def __enter__(self) -> ProcessManager:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def _spawn(
        self,
        command: tuple[str, ...],
        cwd: Path,
        env: Mapping[str, str] | None,
        *,
        pty: bool,
        encoding: str,
    ) -> tuple[subprocess.Popen[bytes], int | None]:
        process_env = sanitize_environment(os.environ, reject_unknown=False)
        process_env.setdefault("PYTHONUTF8", "1")
        process_env.setdefault("PYTHONIOENCODING", encoding)
        if env is not None:
            process_env.update(sanitize_environment(env))
        options: dict[str, Any] = {
            "cwd": cwd,
            "env": process_env,
            "shell": False,
            "stdin": subprocess.DEVNULL,
        }
        reader_fd: int | None = None
        if pty:
            import pty as pty_module

            master_fd, slave_fd = pty_module.openpty()  # type: ignore[attr-defined]
            options.update(
                {
                    "stdin": slave_fd,
                    "stdout": slave_fd,
                    "stderr": subprocess.STDOUT,
                    "close_fds": True,
                    "start_new_session": True,
                }
            )
            try:
                process = subprocess.Popen(command, **options)
            except Exception:
                os.close(master_fd)
                os.close(slave_fd)
                raise
            os.close(slave_fd)
            reader_fd = master_fd
            return process, reader_fd
        options.update(
            {
                "stdout": subprocess.PIPE,
                "stderr": subprocess.STDOUT,
                "start_new_session": os.name != "nt",
            }
        )
        if os.name == "nt":
            options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        return subprocess.Popen(command, **options), None

    def _read_output(self, item: _ManagedProcess, encoding: str) -> None:
        try:
            while True:
                if item.reader_fd is not None:
                    try:
                        data = os.read(item.reader_fd, 8192)
                    except OSError:
                        break
                else:
                    stream = item.process.stdout
                    if stream is None:
                        break
                    data = stream.read(8192)
                if not data:
                    break
                with item.lock:
                    item.log_bytes += len(data)
                    item.binary_output = item.binary_output or b"\x00" in data
                    remaining = self.max_log_bytes - item.log_handle.tell()
                    if remaining > 0:
                        item.log_handle.write(data[:remaining])
                    if len(data) > max(remaining, 0):
                        item.log_truncated = True
                    item.log_handle.flush()
        finally:
            if item.reader_fd is not None:
                try:
                    os.close(item.reader_fd)
                except OSError:
                    pass
                item.reader_fd = None
            if item.process.stdout is not None:
                item.process.stdout.close()
            item.reader_done.set()

    def _watch_process(self, item: _ManagedProcess) -> None:
        try:
            if item.record.timeout_seconds is None:
                item.process.wait()
            else:
                try:
                    item.process.wait(timeout=item.record.timeout_seconds)
                except subprocess.TimeoutExpired:
                    self._terminate(item, timed_out=True)
                    item.process.wait()
            item.reader_done.wait()
            with item.lock:
                self._finish(item)
        finally:
            item.done.set()

    def _terminate(
        self,
        item: _ManagedProcess,
        *,
        force: bool = True,
        timed_out: bool = False,
    ) -> None:
        with item.lock:
            if item.done.is_set() or item.process.poll() is not None:
                return
            item.stop_requested = True
            item.timeout_requested = item.timeout_requested or timed_out
            pid = item.process.pid
        _terminate_process_tree(pid, force=force)

    def _finish(self, item: _ManagedProcess) -> None:
        if item.done.is_set():
            return
        returncode = item.process.returncode
        if returncode is None:
            return
        status = (
            ProcessStatus.TIMED_OUT
            if item.timeout_requested
            else ProcessStatus.STOPPED
            if item.stop_requested
            else ProcessStatus.EXITED
        )
        item.record = replace(
            item.record,
            status=status,
            ended_at=time.time(),
            returncode=returncode,
            termination_signal=-returncode if returncode < 0 else None,
            log_bytes=item.log_bytes,
            log_truncated=item.log_truncated,
            binary_output=item.binary_output,
        )
        item.log_handle.flush()
        item.log_handle.close()

    def _cwd(self, cwd: str | Path) -> Path:
        raw = Path(cwd).expanduser()
        candidate = raw if raw.is_absolute() else self.workspace_root / raw
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError as exc:
            raise PermissionError("process cwd must remain within the workspace") from exc
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

    def _shell_command(self, shell: Shell, script: str) -> tuple[str, ...]:
        if shell is Shell.POWERSHELL:
            executable = shutil.which("pwsh") or shutil.which("powershell")
            if executable is None:
                raise PtyUnavailable("PowerShell is unavailable")
            return executable, "-NoProfile", "-NonInteractive", "-Command", script
        if shell is Shell.CMD:
            executable = shutil.which("cmd.exe") or shutil.which("cmd")
            if executable is None:
                raise PtyUnavailable("cmd is unavailable")
            return executable, "/d", "/s", "/c", script
        executable = shutil.which(shell.value)
        if executable is None:
            raise PtyUnavailable(f"{shell.value} is unavailable")
        return executable, "-c", script


def _args(args: Sequence[str]) -> tuple[str, ...]:
    return validate_argv(args)


def _pty_available() -> bool:
    if os.name == "nt":
        return False
    try:
        import pty  # noqa: F401
    except (ImportError, OSError):
        return False
    return True


def _terminate_process_tree(pid: int, *, force: bool = True) -> None:
    if os.name == "nt":
        result = subprocess.run(
            ("taskkill", "/PID", str(pid), "/T", "/F"),
            capture_output=True,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if result.returncode != 0:
            try:
                os.kill(pid, signal.SIGTERM)
            except (PermissionError, ProcessLookupError):
                pass
        return
    try:
        os.killpg(  # type: ignore[attr-defined]
            pid,
            signal.SIGKILL if force else signal.SIGTERM,  # type: ignore[attr-defined]
        )
    except ProcessLookupError:
        try:
            os.kill(
                pid,
                signal.SIGKILL if force else signal.SIGTERM,  # type: ignore[attr-defined]
            )
        except ProcessLookupError:
            pass
    if force:
        return
    deadline = time.monotonic() + 1.0
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.02)
    try:
        os.killpg(pid, signal.SIGKILL)  # type: ignore[attr-defined]
    except ProcessLookupError:
        pass


class _WindowsJob:
    def __init__(self) -> None:
        self._handle: Any = None
        if os.name != "nt":
            return
        try:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.CreateJobObjectW(None, None)
            if not handle:
                return
            info = _JobObjectExtendedLimitInformation()
            info.BasicLimitInformation.LimitFlags = 0x2000
            if not kernel32.SetInformationJobObject(
                handle,
                9,
                ctypes.byref(info),
                ctypes.sizeof(info),
            ):
                kernel32.CloseHandle(handle)
                return
            self._handle = handle
        except (AttributeError, OSError):
            self._handle = None

    def assign(self, process: subprocess.Popen[bytes]) -> None:
        if self._handle is None or os.name != "nt":
            return
        try:
            process_handle = getattr(process, "_handle", None)
            if process_handle is None:
                return
            if not ctypes.windll.kernel32.AssignProcessToJobObject(self._handle, process_handle):
                return
        except (AttributeError, OSError):
            return

    def close(self) -> None:
        if self._handle is not None:
            ctypes.windll.kernel32.CloseHandle(self._handle)
            self._handle = None


class _JobObjectBasicLimitInformation(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", ctypes.c_uint32),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", ctypes.c_uint32),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", ctypes.c_uint32),
        ("SchedulingClass", ctypes.c_uint32),
    ]


class _IoCounters(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_uint64),
        ("WriteOperationCount", ctypes.c_uint64),
        ("OtherOperationCount", ctypes.c_uint64),
        ("ReadTransferCount", ctypes.c_uint64),
        ("WriteTransferCount", ctypes.c_uint64),
        ("OtherTransferCount", ctypes.c_uint64),
    ]


class _JobObjectExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _JobObjectBasicLimitInformation),
        ("IoInfo", _IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]
