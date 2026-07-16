#!/usr/bin/env python3
"""RC ID: RC-046. Probe the existing FastAPI app as a desktop sidecar process."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import TypedDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
HOST = "127.0.0.1"


class ProbeResult(TypedDict):
    protocol: str
    host: str
    port: int
    ready: bool
    startup_ms: int
    shutdown_ms: int
    exit_code: int
    alive_after_shutdown: bool


def _reserve_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind((HOST, 0))
        return int(listener.getsockname()[1])


def _wait_until_ready(
    process: subprocess.Popen[str],
    url: str,
    timeout_seconds: float,
) -> None:
    deadline = time.perf_counter() + timeout_seconds
    last_error = "no response"
    while time.perf_counter() < deadline:
        if process.poll() is not None:
            _, stderr = process.communicate()
            summary = stderr.strip().splitlines()[-1] if stderr.strip() else "no stderr"
            raise RuntimeError(f"sidecar exited before readiness: {summary}")
        try:
            with urllib.request.urlopen(url, timeout=0.25) as response:
                if response.status == 200:
                    return
                last_error = f"HTTP {response.status}"
        except (OSError, urllib.error.URLError) as exc:
            last_error = type(exc).__name__
        time.sleep(0.05)
    raise TimeoutError(f"sidecar readiness timed out: {last_error}")


def run_probe(
    *,
    python_executable: str,
    data_dir: Path,
    timeout_seconds: float = 10.0,
) -> ProbeResult:
    """Start, probe, and stop one isolated App Server process."""
    port = _reserve_loopback_port()
    environment = os.environ.copy()
    environment["PROMPT_OPTIMIZER_HOME"] = str(data_dir)
    command = [
        python_executable,
        "-m",
        "uvicorn",
        "prompt_optimizer.api.app:app",
        "--host",
        HOST,
        "--port",
        str(port),
        "--log-level",
        "warning",
    ]
    started = time.perf_counter()
    process = subprocess.Popen(
        command,
        cwd=REPOSITORY_ROOT,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    ready = False
    startup_ms = 0
    shutdown_started = started
    try:
        _wait_until_ready(process, f"http://{HOST}:{port}/openapi.json", timeout_seconds)
        ready = True
        startup_ms = int((time.perf_counter() - started) * 1000)
    finally:
        shutdown_started = time.perf_counter()
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        process.communicate()

    return {
        "protocol": "rc-046-sidecar-prototype-v1",
        "host": HOST,
        "port": port,
        "ready": ready,
        "startup_ms": startup_ms,
        "shutdown_ms": int((time.perf_counter() - shutdown_started) * 1000),
        "exit_code": int(process.returncode),
        "alive_after_shutdown": process.poll() is None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", default=sys.executable, help="Python executable for the sidecar")
    parser.add_argument("--data-dir", type=Path, help="isolated sidecar data directory")
    parser.add_argument("--timeout", type=float, default=10.0, help="readiness timeout in seconds")
    args = parser.parse_args(argv)

    if args.data_dir:
        args.data_dir.mkdir(parents=True, exist_ok=True)
        result = run_probe(
            python_executable=args.python,
            data_dir=args.data_dir,
            timeout_seconds=args.timeout,
        )
    else:
        with tempfile.TemporaryDirectory(prefix="rabbit-sidecar-") as directory:
            result = run_probe(
                python_executable=args.python,
                data_dir=Path(directory),
                timeout_seconds=args.timeout,
            )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
