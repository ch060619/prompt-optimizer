#!/usr/bin/env python3
"""RC ID: RC-057. Probe the candidate Agent Core App Server lifecycle."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import TypedDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
HOST = "127.0.0.1"


class ProbeResult(TypedDict):
    protocol: str
    platform: str
    ready: bool
    stream_events: list[str]
    startup_ms: int
    alive_after_shutdown: bool
    exit_code: int


def _reserve_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind((HOST, 0))
        return int(listener.getsockname()[1])


def _wait_ready(process: subprocess.Popen[str], url: str) -> None:
    deadline = time.perf_counter() + 10
    while time.perf_counter() < deadline:
        if process.poll() is not None:
            raise RuntimeError("prototype App Server exited before readiness")
        try:
            with urllib.request.urlopen(url, timeout=0.25) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.05)
    raise TimeoutError("prototype App Server readiness timed out")


def run_probe() -> ProbeResult:
    port = _reserve_port()
    environment = os.environ.copy()
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.rabbit_code.prototype_app:app",
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
    try:
        _wait_ready(process, f"http://{HOST}:{port}/health")
        startup_ms = int((time.perf_counter() - started) * 1000)
        request = urllib.request.Request(
            f"http://{HOST}:{port}/agent/stream",
            data=json.dumps({"prompt": "写一个测试计划"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
        stream_events = [
            line.removeprefix("event: ")
            for line in body.splitlines()
            if line.startswith("event: ")
        ]
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        process.communicate()

    return {
        "protocol": "rc-057-agent-prototype-v1",
        "platform": sys.platform,
        "ready": True,
        "stream_events": stream_events,
        "startup_ms": startup_ms,
        "alive_after_shutdown": process.poll() is None,
        "exit_code": int(process.returncode),
    }


if __name__ == "__main__":
    print(json.dumps(run_probe(), ensure_ascii=False, indent=2, sort_keys=True))
