from __future__ import annotations

import argparse
import ctypes
import json
import math
import os
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from time import perf_counter, sleep
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [
    str(REPOSITORY_ROOT),
    str(REPOSITORY_ROOT / "backend" / "src"),
    str(REPOSITORY_ROOT / "backend"),
    str(REPOSITORY_ROOT / "packages" / "protocol"),
]

from prompt_optimizer.core.analyzer import Analyzer  # noqa: E402
from prompt_optimizer.core.diff import DiffService  # noqa: E402
from prompt_optimizer.core.models import PromptVersion  # noqa: E402
from prompt_optimizer.core.optimizer import Optimizer  # noqa: E402
from prompt_optimizer.providers.base import ModelRequest, ProviderEventType  # noqa: E402
from prompt_optimizer.providers.offline import OfflineRuleProvider  # noqa: E402
from rabbit_code.search_index import SafeSearchIndexer  # noqa: E402

# RC ID: RC-222. Keep performance budgets reproducible and explicit about blocked probes.


def _timed(callback: Callable[[], object], iterations: int) -> dict[str, float | int | str]:
    samples: list[float] = []
    for _ in range(2):
        callback()
    for _ in range(iterations):
        started = perf_counter()
        callback()
        samples.append((perf_counter() - started) * 1000)
    ordered = sorted(samples)
    p95_index = min(len(ordered) - 1, max(0, math.ceil(len(ordered) * 0.95) - 1))
    return {
        "status": "measured",
        "iterations": iterations,
        "p50_ms": round(median(ordered), 3),
        "p95_ms": round(ordered[p95_index], 3),
        "min_ms": round(ordered[0], 3),
        "max_ms": round(ordered[-1], 3),
    }


def _blocked(reason: str) -> dict[str, int | str]:
    return {"status": "blocked", "reason": reason}


def _prompt_versions() -> tuple[PromptVersion, PromptVersion]:
    analyzer = Analyzer()
    old_text = "Write a concise API summary."
    new_text = "Write a concise API summary with risks and next actions."
    old_analysis = analyzer.analyze(old_text)
    new_analysis = analyzer.analyze(new_text)
    return (
        PromptVersion(
            id=1,
            original_prompt=old_text,
            optimized_prompt=old_text,
            analysis=old_analysis,
            created_at=datetime.now(UTC),
        ),
        PromptVersion(
            id=2,
            original_prompt=new_text,
            optimized_prompt=new_text,
            analysis=new_analysis,
            created_at=datetime.now(UTC),
        ),
    )


def _frontend_dist_bytes() -> dict[str, int | str]:
    dist = REPOSITORY_ROOT / "frontend" / "dist"
    if not dist.is_dir():
        return _blocked("frontend/dist does not exist; build the frontend first")
    return {
        "status": "measured",
        "bytes": sum(path.stat().st_size for path in dist.rglob("*") if path.is_file()),
    }


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            check=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"
    return result.stdout.strip() or "unavailable"


def _memory_probe() -> dict[str, int | str]:
    if sys.platform == "win32":
        class _ProcessMemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong),
                ("page_fault_count", ctypes.c_ulong),
                ("peak_working_set_size", ctypes.c_size_t),
                ("working_set_size", ctypes.c_size_t),
                ("quota_peak_paged_pool_usage", ctypes.c_size_t),
                ("quota_paged_pool_usage", ctypes.c_size_t),
                ("quota_peak_non_paged_pool_usage", ctypes.c_size_t),
                ("quota_non_paged_pool_usage", ctypes.c_size_t),
                ("pagefile_usage", ctypes.c_size_t),
                ("peak_pagefile_usage", ctypes.c_size_t),
            ]

        counters = _ProcessMemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        psapi = ctypes.WinDLL("psapi")  # type: ignore[attr-defined, unused-ignore]
        kernel32 = ctypes.WinDLL("kernel32")  # type: ignore[attr-defined, unused-ignore]
        get_process_memory_info = psapi.GetProcessMemoryInfo
        get_process_memory_info.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(_ProcessMemoryCounters),
            ctypes.c_ulong,
        ]
        get_process_memory_info.restype = ctypes.c_bool
        if get_process_memory_info(
            kernel32.GetCurrentProcess(),
            ctypes.byref(counters),
            counters.cb,
        ):
            return {"status": "measured", "rss_bytes": counters.working_set_size}
        return _blocked("Windows GetProcessMemoryInfo failed")

    try:
        import resource
    except ImportError:
        return _blocked("resource RSS probe is unavailable in this environment")
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {
        "status": "measured",
        "rss_bytes": int(rss * (1024 if sys.platform == "darwin" else 1)),
    }


def _backend_package_bytes() -> dict[str, int | str]:
    """Build a temporary wheel so package size is measured from a real artifact."""
    with tempfile.TemporaryDirectory(prefix="rabbit-code-wheel-") as directory:
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "wheel",
                    "--no-deps",
                    "--no-build-isolation",
                    "--wheel-dir",
                    directory,
                    str(REPOSITORY_ROOT / "backend"),
                ],
                cwd=REPOSITORY_ROOT,
                capture_output=True,
                check=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            return _blocked(f"backend wheel build failed: {exc}")
        wheels = sorted(Path(directory).glob("*.whl"))
        if not wheels:
            return _blocked("backend wheel build produced no wheel")
        return {
            "status": "measured",
            "bytes": sum(path.stat().st_size for path in wheels),
            "artifact": wheels[0].name,
        }


def _gui_startup(iterations: int) -> tuple[dict[str, Any], dict[str, Any]]:
    dist = REPOSITORY_ROOT / "frontend" / "dist"
    if not (dist / "index.html").is_file():
        blocked = _blocked("frontend/dist is unavailable; build the GUI first")
        return blocked, blocked.copy()

    def start_server() -> tuple[subprocess.Popen[bytes], str]:
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = int(reservation.getsockname()[1])
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "http.server",
                str(port),
                "--bind",
                "127.0.0.1",
                "--directory",
                str(dist),
            ],
            cwd=REPOSITORY_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return process, f"http://127.0.0.1:{port}/index.html"

    def fetch(url: str) -> None:
        with urlopen(url, timeout=1) as response:
            if response.status != 200 or not response.read(32):
                raise RuntimeError("GUI startup probe returned an invalid response")

    def wait_until_ready(process: subprocess.Popen[bytes], url: str) -> None:
        deadline = perf_counter() + 5
        while perf_counter() < deadline:
            if process.poll() is not None:
                raise RuntimeError("GUI startup probe exited before becoming ready")
            try:
                fetch(url)
                return
            except (OSError, URLError):
                sleep(0.01)
        raise TimeoutError("GUI startup probe did not become ready within 5 seconds")

    def stop_server(process: subprocess.Popen[bytes]) -> None:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)

    def cold_start() -> None:
        process, url = start_server()
        try:
            wait_until_ready(process, url)
        finally:
            stop_server(process)

    cold = _timed(cold_start, iterations)
    process, url = start_server()
    try:
        wait_until_ready(process, url)
        hot = _timed(lambda: fetch(url), iterations)
    finally:
        stop_server(process)
    cold["surface"] = "frontend-dist-http"
    hot["surface"] = "frontend-dist-http"
    return cold, hot


def _cli_first_response(prompt: str) -> None:
    environment = os.environ.copy()
    python_paths = [
        str(REPOSITORY_ROOT),
        str(REPOSITORY_ROOT / "backend" / "src"),
        str(REPOSITORY_ROOT / "backend"),
        str(REPOSITORY_ROOT / "packages" / "protocol"),
    ]
    existing_path = environment.get("PYTHONPATH")
    if existing_path:
        python_paths.append(existing_path)
    environment["PYTHONPATH"] = os.pathsep.join(python_paths)
    subprocess.run(
        [sys.executable, "-m", "prompt_optimizer.cli.__main__", "analyze", prompt],
        cwd=REPOSITORY_ROOT,
        env=environment,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def collect(iterations: int) -> dict[str, Any]:
    optimizer = Optimizer()
    prompt = "Write a concise API summary with explicit constraints and acceptance criteria."
    provider = OfflineRuleProvider(optimizer)
    request = ModelRequest(prompt=prompt)
    old_version, new_version = _prompt_versions()
    diff_service = DiffService()
    gui_cold_start, gui_hot_start = _gui_startup(iterations)

    with tempfile.TemporaryDirectory(prefix="rabbit-code-performance-") as directory:
        workspace = Path(directory)
        for index in range(100):
            (workspace / f"module_{index:03d}.py").write_text(
                f"# benchmark file {index}\nneedle = {index}\n",
                encoding="utf-8",
            )
        indexer = SafeSearchIndexer(workspace)
        indexer.scan()

        measurements: dict[str, Any] = {
            "cli_first_response": _timed(lambda: _cli_first_response(prompt), iterations),
            "offline_first_token": _timed(
                lambda: next(
                    event
                    for event in provider.stream(request)
                    if event.type is ProviderEventType.DELTA
                ),
                iterations,
            ),
            "search_query": _timed(lambda: indexer.search("needle"), iterations),
            "diff": _timed(lambda: diff_service.compare(old_version, new_version), iterations),
            "frontend_dist": _frontend_dist_bytes(),
            "memory": _memory_probe(),
            "gui_cold_start": gui_cold_start,
            "gui_hot_start": gui_hot_start,
            "backend_package": _backend_package_bytes(),
        }

    return {
        "schema_version": "rc222-v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "environment": {
            "commit": _git_commit(),
            "machine": platform.node() or "unavailable",
            "os": platform.platform(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "python": platform.python_version(),
            "node": shutil.which("node") or "unavailable",
            "hardware_probe": "Windows WMI values recorded in docs/performance/baseline.md",
        },
        "thresholds": {
            "cli_first_response_p95_ms": 1000,
            "offline_first_token_p95_ms": 1500,
            "search_query_p95_ms": 50,
            "diff_p95_ms": 50,
            "frontend_dist_bytes": 2_000_000,
            "gui_cold_start_p95_ms": 3_000,
            "gui_hot_start_p95_ms": 500,
            "memory_rss_bytes": 512_000_000,
            "backend_package_bytes": 5_000_000,
        },
        "measurements": measurements,
    }


def _failed_measurements(report: dict[str, Any]) -> list[str]:
    thresholds = report["thresholds"]
    measurements = report["measurements"]
    failures: list[str] = []
    for key, threshold_key in (
        ("cli_first_response", "cli_first_response_p95_ms"),
        ("offline_first_token", "offline_first_token_p95_ms"),
        ("search_query", "search_query_p95_ms"),
        ("diff", "diff_p95_ms"),
        ("gui_cold_start", "gui_cold_start_p95_ms"),
        ("gui_hot_start", "gui_hot_start_p95_ms"),
    ):
        item = measurements[key]
        if item.get("status") != "measured" or item["p95_ms"] > thresholds[threshold_key]:
            failures.append(key)
    package = measurements["frontend_dist"]
    if package.get("status") != "measured" or package["bytes"] > thresholds["frontend_dist_bytes"]:
        failures.append("frontend_dist")
    memory = measurements["memory"]
    if memory.get("status") != "measured" or memory["rss_bytes"] > thresholds["memory_rss_bytes"]:
        failures.append("memory")
    backend_package = measurements["backend_package"]
    if (
        backend_package.get("status") != "measured"
        or backend_package["bytes"] > thresholds["backend_package_bytes"]
    ):
        failures.append("backend_package")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the offline Rabbit Code performance baseline.")
    parser.add_argument("--iterations", type=int, default=25)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true", help="fail when a budget is unmet or blocked")
    args = parser.parse_args()
    if args.iterations < 5:
        parser.error("--iterations must be at least 5")
    report = collect(args.iterations)
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized, end="")
    return 1 if args.check and _failed_measurements(report) else 0


if __name__ == "__main__":
    raise SystemExit(main())
