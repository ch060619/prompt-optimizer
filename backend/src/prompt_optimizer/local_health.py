from __future__ import annotations

import ctypes
import json
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from threading import Event
from typing import Literal, Protocol

from prompt_optimizer.providers.base import ModelRequest
from prompt_optimizer.providers.runners import LocalRunnerAdapter

# RC ID: RC-193. Run a private, repeatable local-model health probe without storing user prompts.

HealthCheckStatus = Literal["passed", "failed"]
ResourceProbe = Callable[[], int | None]


class HealthReportRecorder(Protocol):
    def record_health_report(
        self,
        *,
        report_path: Path,
        passed: bool,
        error: str | None = None,
    ) -> dict[str, object]:
        ...


@dataclass(frozen=True)
class HealthCheckResult:
    name: str
    status: HealthCheckStatus
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status, "detail": self.detail}


@dataclass(frozen=True)
class HealthReport:
    model_id: str
    runner: str
    checked_at: str
    ready: bool
    checks: tuple[HealthCheckResult, ...]
    resource_peak_bytes: int | None

    def to_dict(self) -> dict[str, object]:
        return {
            "model_id": self.model_id,
            "runner": self.runner,
            "checked_at": self.checked_at,
            "ready": self.ready,
            "checks": [check.to_dict() for check in self.checks],
            "resource_peak_bytes": self.resource_peak_bytes,
        }


def run_health_check(
    runner: LocalRunnerAdapter,
    *,
    model_id: str,
    context_length: int,
    report_path: Path,
    resource_probe: ResourceProbe | None = None,
    state_recorder: HealthReportRecorder | None = None,
) -> HealthReport:
    if context_length <= 0:
        raise ValueError("context_length must be positive")
    probe = resource_probe or _process_peak_memory_bytes
    checks: list[HealthCheckResult] = []
    samples: list[int] = []

    def sample_resource() -> None:
        sample = probe()
        if sample is not None and sample >= 0:
            samples.append(sample)

    def run_check(name: str, action: Callable[[], None]) -> None:
        sample_resource()
        try:
            action()
        except Exception as exc:  # noqa: BLE001 - health probes must report and roll back.
            checks.append(HealthCheckResult(name, "failed", type(exc).__name__))
        else:
            checks.append(HealthCheckResult(name, "passed", "ok"))
        sample_resource()

    version = ""

    def check_version() -> None:
        nonlocal version
        version = runner.version().strip()
        if not version:
            raise RuntimeError("runner version is empty")

    def check_load() -> None:
        operation = runner.load(model_id)
        if operation.status != "ok":
            raise RuntimeError("model load failed")

    def check_minimal_generation() -> None:
        result = runner.generate(ModelRequest(prompt="Rabbit Code health probe"))
        if not result.strip():
            raise RuntimeError("empty generation")

    def check_streaming() -> None:
        chunks = tuple(runner.stream(ModelRequest(prompt="Rabbit Code stream probe")))
        if len(chunks) < 2 or not all(chunk.strip() for chunk in chunks):
            raise RuntimeError("stream did not produce incremental output")

    def check_cancellation() -> None:
        cancel_event = Event()
        cancel_event.set()
        chunks = tuple(
            runner.stream(
                ModelRequest(
                    prompt="Rabbit Code cancellation probe",
                    cancel_event=cancel_event,
                )
            )
        )
        if chunks:
            raise RuntimeError("runner emitted output after cancellation")

    def check_context() -> None:
        prompt = "x " * context_length
        result = runner.generate(ModelRequest(prompt=prompt))
        if not result.strip():
            raise RuntimeError("context probe returned empty output")

    def check_stop_and_reload() -> None:
        stopped = runner.stop(model_id)
        if stopped.status != "ok":
            raise RuntimeError("model stop failed")
        reloaded = runner.load(model_id)
        if reloaded.status != "ok":
            raise RuntimeError("model reload failed")

    run_check("runner_version", check_version)
    run_check("model_load", check_load)
    run_check("minimal_generation", check_minimal_generation)
    run_check("streaming_increment", check_streaming)
    run_check("cancellation", check_cancellation)
    run_check("context_length", check_context)
    run_check("stop_and_reload", check_stop_and_reload)
    resource_peak = max(samples) if samples else None
    checks.append(
        HealthCheckResult(
            "resource_peak",
            "passed" if resource_peak is not None else "failed",
            "ok" if resource_peak is not None else "resource probe unavailable",
        )
    )
    report = HealthReport(
        model_id=model_id,
        runner=version or runner.name,
        checked_at=datetime.now(UTC).isoformat(),
        ready=all(check.status == "passed" for check in checks),
        checks=tuple(checks),
        resource_peak_bytes=resource_peak,
    )
    _save_report(report_path, report)
    if state_recorder is not None:
        state_recorder.record_health_report(
            report_path=report_path,
            passed=report.ready,
            error=None if report.ready else "one or more health checks failed",
        )
    return report


def _save_report(path: Path, report: HealthReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _process_peak_memory_bytes() -> int | None:
    if os.name == "nt":
        return _windows_peak_working_set()
    try:
        import resource
    except ImportError:
        return None
    getrusage = getattr(resource, "getrusage", None)
    usage_self = getattr(resource, "RUSAGE_SELF", None)
    if getrusage is None or usage_self is None:
        return None
    peak = getrusage(usage_self).ru_maxrss
    return int(peak if sys.platform == "darwin" else peak * 1024)


def _windows_peak_working_set() -> int | None:
    class MemoryCounters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("PageFaultCount", ctypes.c_ulong),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
        ]

    counters = MemoryCounters()
    counters.cb = ctypes.sizeof(MemoryCounters)
    process = ctypes.windll.kernel32.GetCurrentProcess()
    if not ctypes.windll.psapi.GetProcessMemoryInfo(
        process,
        ctypes.byref(counters),
        counters.cb,
    ):
        return None
    return int(counters.PeakWorkingSetSize)
