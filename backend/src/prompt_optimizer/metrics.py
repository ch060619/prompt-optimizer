from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock

from prompt_optimizer.core.models import PerformanceMetricsSnapshot

# RC ID: RC-219. Aggregate anonymous technical metrics locally without content.

_SAFE_LABEL = re.compile(r"^[A-Za-z0-9._:/-]{1,128}$")
_SENSITIVE_LABEL = re.compile(r"(?i)(api[_ -]?key|token|secret|password|cookie|bearer)")


@dataclass
class _Counter:
    requests_total: int = 0
    requests_succeeded: int = 0
    requests_failed: int = 0
    latency_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class LocalMetricsAggregator:
    _started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)
    _requests: _Counter = field(default_factory=_Counter, init=False, repr=False)
    _providers: dict[str, _Counter] = field(default_factory=dict, init=False, repr=False)
    _first_token_count: int = field(default=0, init=False)
    _first_token_latency_ms: int = field(default=0, init=False)
    _tool_calls: int = field(default=0, init=False)
    _tool_successes: int = field(default=0, init=False)
    _model_loads: int = field(default=0, init=False)
    _model_load_failures: int = field(default=0, init=False)
    _model_load_latency_ms: int = field(default=0, init=False)
    _resource_samples: int = field(default=0, init=False)
    _max_cpu_percent: float | None = field(default=None, init=False)
    _max_ram_bytes: int | None = field(default=None, init=False)
    _max_gpu_memory_bytes: int | None = field(default=None, init=False)

    def record_request(
        self,
        *,
        provider: str,
        latency_ms: int,
        success: bool,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
    ) -> None:
        name = _safe_label(provider, "provider")
        _nonnegative(latency_ms, "latency_ms")
        input_value = _optional_nonnegative(input_tokens, "input_tokens")
        output_value = _optional_nonnegative(output_tokens, "output_tokens")
        with self._lock:
            counter = self._providers.setdefault(name, _Counter())
            _record_request(counter, latency_ms, success, input_value, output_value)
            _record_request(self._requests, latency_ms, success, input_value, output_value)

    def record_first_token(self, latency_ms: int) -> None:
        _nonnegative(latency_ms, "first_token_latency_ms")
        with self._lock:
            self._first_token_count += 1
            self._first_token_latency_ms += latency_ms

    def record_tool(self, *, success: bool) -> None:
        with self._lock:
            self._tool_calls += 1
            self._tool_successes += int(success)

    def record_model_load(self, *, model: str, latency_ms: int, success: bool) -> None:
        _safe_label(model, "model")
        _nonnegative(latency_ms, "model_load_latency_ms")
        with self._lock:
            self._model_loads += 1
            self._model_load_failures += int(not success)
            self._model_load_latency_ms += latency_ms

    def record_resources(
        self,
        *,
        cpu_percent: float | None = None,
        ram_bytes: int | None = None,
        gpu_memory_bytes: int | None = None,
    ) -> None:
        if cpu_percent is not None and not 0 <= cpu_percent <= 100:
            raise ValueError("cpu_percent must be between 0 and 100")
        ram_value = _optional_nonnegative(ram_bytes, "ram_bytes")
        gpu_value = _optional_nonnegative(gpu_memory_bytes, "gpu_memory_bytes")
        if cpu_percent is None and ram_value is None and gpu_value is None:
            return
        with self._lock:
            self._resource_samples += 1
            if cpu_percent is not None:
                self._max_cpu_percent = max(self._max_cpu_percent or 0, cpu_percent)
            if ram_value is not None:
                self._max_ram_bytes = max(self._max_ram_bytes or 0, ram_value)
            if gpu_value is not None:
                self._max_gpu_memory_bytes = max(self._max_gpu_memory_bytes or 0, gpu_value)

    def snapshot(self) -> PerformanceMetricsSnapshot:
        with self._lock:
            requests = self._requests
            return PerformanceMetricsSnapshot(
                schema_version="rc219-v1",
                window_started_at=self._started_at,
                requests_total=requests.requests_total,
                requests_succeeded=requests.requests_succeeded,
                requests_failed=requests.requests_failed,
                failure_rate=_rate(requests.requests_failed, requests.requests_total),
                total_latency_ms=requests.latency_ms,
                average_latency_ms=_average(requests.latency_ms, requests.requests_total),
                first_token_count=self._first_token_count,
                first_token_total_ms=self._first_token_latency_ms,
                average_first_token_ms=_average(
                    self._first_token_latency_ms,
                    self._first_token_count,
                ),
                input_tokens=requests.input_tokens,
                output_tokens=requests.output_tokens,
                tool_calls=self._tool_calls,
                tool_successes=self._tool_successes,
                tool_success_rate=_rate(self._tool_successes, self._tool_calls),
                model_loads=self._model_loads,
                model_load_failures=self._model_load_failures,
                total_model_load_ms=self._model_load_latency_ms,
                average_model_load_ms=_average(
                    self._model_load_latency_ms,
                    self._model_loads,
                ),
                resource_samples=self._resource_samples,
                max_cpu_percent=self._max_cpu_percent,
                max_ram_bytes=self._max_ram_bytes,
                max_gpu_memory_bytes=self._max_gpu_memory_bytes,
                provider_metrics={
                    name: _counter_display(counter) for name, counter in self._providers.items()
                },
            )


def _record_request(
    counter: _Counter,
    latency_ms: int,
    success: bool,
    input_tokens: int | None,
    output_tokens: int | None,
) -> None:
    counter.requests_total += 1
    counter.requests_succeeded += int(success)
    counter.requests_failed += int(not success)
    counter.latency_ms += latency_ms
    counter.input_tokens += input_tokens or 0
    counter.output_tokens += output_tokens or 0


def _counter_display(counter: _Counter) -> dict[str, float | int]:
    return {
        "requests_total": counter.requests_total,
        "requests_succeeded": counter.requests_succeeded,
        "requests_failed": counter.requests_failed,
        "failure_rate": _rate(counter.requests_failed, counter.requests_total),
        "total_latency_ms": counter.latency_ms,
        "input_tokens": counter.input_tokens,
        "output_tokens": counter.output_tokens,
    }


def _safe_label(value: str, name: str) -> str:
    if (
        not isinstance(value, str)
        or not _SAFE_LABEL.fullmatch(value)
        or _SENSITIVE_LABEL.search(value)
    ):
        raise ValueError(f"{name} must be a non-sensitive technical label")
    return value


def _nonnegative(value: int, name: str) -> None:
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _optional_nonnegative(value: int | None, name: str) -> int | None:
    if value is not None:
        _nonnegative(value, name)
    return value


def _average(total: int, count: int) -> float:
    return round(total / count, 2) if count else 0.0


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0
