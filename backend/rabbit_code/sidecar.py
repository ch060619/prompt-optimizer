from __future__ import annotations

import os
import secrets
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# RC ID: RC-067. Own the local App Server process lifecycle at the desktop boundary.

HOST = "127.0.0.1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class SidecarError(RuntimeError):
    pass


class SidecarStartupError(SidecarError):
    pass


def generate_startup_token() -> str:
    return secrets.token_urlsafe(32)


class SidecarVersionMismatch(SidecarError):
    def __init__(self, expected: str, actual: object) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(f"sidecar protocol mismatch: expected {expected!r}, got {actual!r}")


@dataclass(frozen=True)
class SidecarConfig:
    python_executable: str = sys.executable
    repository_root: Path = REPOSITORY_ROOT
    server_module: str = "backend.rabbit_code.sidecar_server"
    host: str = HOST
    protocol_version: str = "v1"
    data_dir: Path | None = None
    startup_timeout_seconds: float = 10.0
    shutdown_timeout_seconds: float = 5.0
    max_restarts: int = 2
    poll_interval_seconds: float = 0.05

    def __post_init__(self) -> None:
        if self.host not in {"127.0.0.1", "::1"}:
            raise ValueError("sidecar host must be Loopback")
        if self.max_restarts < 0:
            raise ValueError("max_restarts must be non-negative")
        if self.startup_timeout_seconds <= 0 or self.shutdown_timeout_seconds <= 0:
            raise ValueError("sidecar timeouts must be positive")
        if self.poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be positive")


@dataclass(frozen=True)
class SidecarConnection:
    host: str
    port: int
    startup_token: str
    protocol_version: str

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def headers(self) -> dict[str, str]:
        return {
            "X-Rabbit-Code-Startup-Token": self.startup_token,
            "X-Rabbit-Code-Protocol": self.protocol_version,
        }


def reserve_loopback_port(host: str = HOST) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind((host, 0))
        return int(listener.getsockname()[1])


class SidecarManager:
    def __init__(self, config: SidecarConfig | None = None) -> None:
        self.config = config or SidecarConfig()
        self._lock = threading.RLock()
        self._process: subprocess.Popen[str] | None = None
        self._connection: SidecarConnection | None = None
        self._monitor_thread: threading.Thread | None = None
        self._stop_requested = False
        self._restart_count = 0
        self._last_error: str | None = None

    @property
    def connection(self) -> SidecarConnection | None:
        with self._lock:
            return self._connection

    @property
    def restart_count(self) -> int:
        with self._lock:
            return self._restart_count

    @property
    def last_error(self) -> str | None:
        with self._lock:
            return self._last_error

    def is_running(self) -> bool:
        with self._lock:
            return self._process is not None and self._process.poll() is None

    def start(self) -> SidecarConnection:
        with self._lock:
            if self.is_running():
                raise SidecarError("sidecar is already running")
            self._stop_requested = False
            self._restart_count = 0
            self._last_error = None
            connection = self._start_with_retries()
            self._monitor_thread = threading.Thread(
                target=self._monitor,
                name="rabbit-code-sidecar-monitor",
                daemon=True,
            )
            self._monitor_thread.start()
            return connection

    def ensure_running(self) -> SidecarConnection:
        with self._lock:
            if self._stop_requested:
                raise SidecarError("sidecar manager is stopped")
            if self.is_running() and self._connection is not None:
                return self._connection
            if self._restart_count >= self.config.max_restarts:
                detail = self._last_error or "sidecar exited unexpectedly"
                raise SidecarStartupError(
                    f"sidecar restart limit reached ({self.config.max_restarts}): {detail}"
                )
            self._restart_count += 1
            try:
                connection = self._start_once()
            except SidecarError as exc:
                self._last_error = str(exc)
                raise
            self._connection = connection
            return connection

    def stop(self) -> None:
        with self._lock:
            self._stop_requested = True
            process = self._process
            self._process = None
            self._connection = None
            monitor = self._monitor_thread
            self._monitor_thread = None
        if process is not None:
            self._terminate(process)
        if monitor is not None and monitor is not threading.current_thread():
            monitor.join(timeout=self.config.shutdown_timeout_seconds)

    def _start_with_retries(self) -> SidecarConnection:
        errors: list[str] = []
        for attempt in range(self.config.max_restarts + 1):
            try:
                connection = self._start_once()
            except SidecarVersionMismatch:
                raise
            except SidecarStartupError as exc:
                errors.append(str(exc))
                if attempt >= self.config.max_restarts:
                    raise SidecarStartupError(
                        f"sidecar failed after {attempt + 1} attempt(s): {'; '.join(errors)}"
                    ) from exc
                self._restart_count += 1
            else:
                self._connection = connection
                return connection
        raise AssertionError("sidecar startup loop must return or raise")

    def _start_once(self) -> SidecarConnection:
        previous_process = self._process
        if previous_process is not None and previous_process.poll() is not None:
            self._process_output(previous_process)
        port = reserve_loopback_port(self.config.host)
        token = generate_startup_token()
        environment = os.environ.copy()
        environment["RABBIT_CODE_STARTUP_TOKEN"] = token
        environment["RABBIT_CODE_PROTOCOL_VERSION"] = self.config.protocol_version
        if self.config.data_dir is not None:
            self.config.data_dir.mkdir(parents=True, exist_ok=True)
            environment["RABBIT_CODE_HOME"] = str(self.config.data_dir)
        command = [
            self.config.python_executable,
            "-m",
            "uvicorn",
            f"{self.config.server_module}:app",
            "--host",
            self.config.host,
            "--port",
            str(port),
            "--log-level",
            "warning",
        ]
        try:
            process = subprocess.Popen(
                command,
                cwd=self.config.repository_root,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as exc:
            raise SidecarStartupError(f"unable to start sidecar on port {port}: {exc}") from exc
        self._process = process
        try:
            self._wait_until_ready(process, port)
        except SidecarVersionMismatch:
            self._terminate(process)
            self._process = None
            self._connection = None
            raise
        except SidecarStartupError as exc:
            self._terminate(process)
            self._process = None
            self._connection = None
            raise SidecarStartupError(f"{exc} (port {port})") from exc
        return SidecarConnection(
            host=self.config.host,
            port=port,
            startup_token=token,
            protocol_version=self.config.protocol_version,
        )

    def _wait_until_ready(self, process: subprocess.Popen[str], port: int) -> None:
        deadline = time.perf_counter() + self.config.startup_timeout_seconds
        last_error = "no response"
        url = f"http://{self.config.host}:{port}/api/v1/health"
        while time.perf_counter() < deadline:
            if process.poll() is not None:
                details = self._process_output(process)
                raise SidecarStartupError(
                    f"sidecar exited before readiness: {details or 'no process output'}"
                )
            request = urllib.request.Request(
                url,
                headers={"X-Rabbit-Code-Protocol": self.config.protocol_version},
            )
            try:
                with urllib.request.urlopen(request, timeout=0.25) as response:
                    if response.status != 200:
                        last_error = f"HTTP {response.status}"
                    else:
                        payload = response.read()
                        self._validate_health(payload)
                        return
            except SidecarVersionMismatch:
                raise
            except (OSError, urllib.error.URLError, ValueError) as exc:
                last_error = type(exc).__name__
            time.sleep(self.config.poll_interval_seconds)
        raise SidecarStartupError(
            "sidecar readiness timed out after "
            f"{self.config.startup_timeout_seconds:.1f}s: {last_error}"
        )

    def _validate_health(self, body: bytes) -> None:
        import json

        try:
            payload: Any = json.loads(body)
        except json.JSONDecodeError as exc:
            raise SidecarStartupError("sidecar health response is not JSON") from exc
        if not isinstance(payload, dict) or payload.get("status") != "ok":
            raise SidecarStartupError("sidecar health response is not ready")
        actual = payload.get("protocol_version")
        if actual != self.config.protocol_version:
            raise SidecarVersionMismatch(self.config.protocol_version, actual)

    def _monitor(self) -> None:
        while True:
            time.sleep(self.config.poll_interval_seconds)
            with self._lock:
                if self._stop_requested:
                    return
                process = self._process
            if process is None or process.poll() is None:
                continue
            try:
                self.ensure_running()
            except SidecarError as exc:
                with self._lock:
                    self._last_error = str(exc)
                    self._connection = None
                return

    @staticmethod
    def _process_output(process: subprocess.Popen[str]) -> str:
        try:
            stdout, stderr = process.communicate(timeout=0.2)
        except subprocess.TimeoutExpired:
            return ""
        output = "\n".join(part.strip() for part in (stdout, stderr) if part and part.strip())
        return output.splitlines()[-1] if output else ""

    def _terminate(self, process: subprocess.Popen[str]) -> None:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=self.config.shutdown_timeout_seconds)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=self.config.shutdown_timeout_seconds)
        try:
            process.communicate(timeout=self.config.shutdown_timeout_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=self.config.shutdown_timeout_seconds)
