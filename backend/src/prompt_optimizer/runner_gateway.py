from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, replace
from threading import Event, Lock, Semaphore
from time import monotonic, perf_counter
from typing import Literal
from uuid import uuid4

from prompt_optimizer.hardware import HardwareReport
from prompt_optimizer.metrics import LocalMetricsAggregator
from prompt_optimizer.providers.base import ModelRequest
from prompt_optimizer.providers.local import LocalModelFailure, LocalRunnerHealth
from prompt_optimizer.providers.runners import (
    LocalRunnerAdapter,
    RunnerModel,
    RunnerOperation,
    RunnerRegistry,
)
from prompt_optimizer.runner_resources import RunnerResourceConfig, safe_runner_config

# RC ID: RC-198. Keep FastAPI local runner operations behind one cancellable gateway.

RunnerEventType = Literal["started", "delta", "completed", "cancelled", "error"]


@dataclass(frozen=True)
class RunnerCapabilities:
    runner: str
    generate: bool = True
    streaming: bool = True
    cancellation: bool = True
    model_listing: bool = True
    load: bool = True
    unload: bool = True

    def to_dict(self) -> dict[str, object]:
        return {
            "runner": self.runner,
            "generate": self.generate,
            "streaming": self.streaming,
            "cancellation": self.cancellation,
            "model_listing": self.model_listing,
            "load": self.load,
            "unload": self.unload,
        }


@dataclass(frozen=True)
class RunnerGeneration:
    request_id: str
    text: str

    def to_dict(self) -> dict[str, object]:
        return {"request_id": self.request_id, "text": self.text}


@dataclass(frozen=True)
class RunnerEvent:
    event: RunnerEventType
    request_id: str
    text: str | None = None
    error: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "event": self.event,
            "request_id": self.request_id,
        }
        if self.text is not None:
            payload["text"] = self.text
        if self.error is not None:
            payload["error"] = self.error
        return payload


@dataclass(frozen=True)
class RunnerQueueStatus:
    active: int
    pending: int
    capacity: int

    @property
    def available(self) -> int:
        return max(0, self.capacity - self.active)

    def to_dict(self) -> dict[str, int]:
        return {
            "active": self.active,
            "pending": self.pending,
            "capacity": self.capacity,
            "available": self.available,
        }


class RunnerGatewayError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        code: str,
        retryable: bool,
        recovery_action: str,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.recovery_action = recovery_action

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "message": str(self),
            "retryable": self.retryable,
            "recovery_action": self.recovery_action,
        }


class RunnerBusyError(RunnerGatewayError):
    def __init__(self) -> None:
        super().__init__(
            "local runner concurrency limit reached",
            code="runner_busy",
            retryable=True,
            recovery_action="wait_and_retry",
        )


class RunnerCancelledError(RunnerGatewayError):
    def __init__(self) -> None:
        super().__init__(
            "local runner request cancelled",
            code="cancelled",
            retryable=False,
            recovery_action="retry",
        )


class LocalRunnerGateway:
    def __init__(
        self,
        *,
        registry: RunnerRegistry | None = None,
        max_concurrency: int | None = None,
        max_queue: int = 8,
        queue_timeout_seconds: float = 5.0,
        health_ttl_seconds: float = 5.0,
        clock: Callable[[], float] = monotonic,
        metrics: LocalMetricsAggregator | None = None,
        resource_config: RunnerResourceConfig | None = None,
        hardware_report: HardwareReport | None = None,
        context_length: int = 4096,
    ) -> None:
        if resource_config is not None:
            configured = resource_config
        elif hardware_report is not None:
            configured = safe_runner_config(hardware_report, context_length=context_length)
        else:
            configured = RunnerResourceConfig(
                concurrency=max_concurrency if max_concurrency is not None else 1,
            )
        concurrency = configured.concurrency if max_concurrency is None else max_concurrency
        if concurrency <= 0 or max_queue < 0:
            raise ValueError("runner concurrency limits are invalid")
        if queue_timeout_seconds < 0 or health_ttl_seconds < 0:
            raise ValueError("runner cache and queue timeouts must not be negative")
        self.registry = registry or RunnerRegistry()
        self.resource_config = replace(configured, concurrency=concurrency)
        self.max_concurrency = concurrency
        self.max_queue = max_queue
        self.queue_timeout_seconds = queue_timeout_seconds
        self.health_ttl_seconds = health_ttl_seconds
        self._clock = clock
        self.metrics = metrics
        self._runners: dict[str, LocalRunnerAdapter] = {}
        self._health_cache: dict[str, tuple[float, LocalRunnerHealth]] = {}
        self._requests: dict[tuple[str, str], Event] = {}
        self._lock = Lock()
        self._slots = Semaphore(concurrency)
        self._active = 0
        self._pending = 0

    def list(self, runner_name: str) -> tuple[RunnerModel, ...]:
        return self._runner(runner_name).list()

    def capabilities(self, runner_name: str) -> RunnerCapabilities:
        self._runner(runner_name)
        return RunnerCapabilities(runner=runner_name)

    def queue_status(self) -> RunnerQueueStatus:
        with self._lock:
            return RunnerQueueStatus(
                active=self._active,
                pending=self._pending,
                capacity=self.max_concurrency,
            )

    def configure_resources(self, config: RunnerResourceConfig) -> RunnerResourceConfig:
        with self._lock:
            if self._active or self._pending:
                raise RunnerBusyError()
            self.resource_config = config
            self.max_concurrency = config.concurrency
            self._slots = Semaphore(config.concurrency)
            runners = tuple(self._runners.values())
        for runner in runners:
            runner.configure(config)
        return config

    def resource_signal(self, runner_name: str) -> dict[str, object]:
        health = self.health(runner_name, force=True)
        temperature = health.temperature_celsius
        return {
            "runner": runner_name,
            "out_of_memory": health.status == "out_of_memory",
            "temperature_celsius": temperature,
            "temperature_limit_celsius": self.resource_config.temperature_limit_celsius,
            "should_throttle": health.status == "out_of_memory"
            or (
                temperature is not None
                and temperature >= self.resource_config.temperature_limit_celsius
            ),
        }

    def health(self, runner_name: str, *, force: bool = False) -> LocalRunnerHealth:
        now = self._clock()
        with self._lock:
            cached = self._health_cache.get(runner_name)
        if not force and cached is not None and now - cached[0] < self.health_ttl_seconds:
            return cached[1]
        health = self._runner(runner_name).health()
        with self._lock:
            self._health_cache[runner_name] = (now, health)
        return health

    def pull(self, runner_name: str, model_id: str) -> RunnerOperation:
        operation = self._runner(runner_name).pull(model_id)
        self._invalidate_health(runner_name)
        return operation

    def load(self, runner_name: str, model_id: str) -> RunnerOperation:
        started = perf_counter()
        try:
            operation = self._runner(runner_name).load(model_id)
        except Exception:
            if self.metrics is not None:
                self.metrics.record_model_load(
                    model=model_id,
                    latency_ms=int((perf_counter() - started) * 1000),
                    success=False,
                )
            raise
        if self.metrics is not None:
            self.metrics.record_model_load(
                model=model_id,
                latency_ms=int((perf_counter() - started) * 1000),
                success=operation.status == "ok",
            )
        self._invalidate_health(runner_name)
        return operation

    def unload(self, runner_name: str, model_id: str) -> RunnerOperation:
        operation = self._runner(runner_name).stop(model_id)
        self._invalidate_health(runner_name)
        return operation

    def generate(
        self,
        runner_name: str,
        request: ModelRequest,
        *,
        model_id: str | None = None,
    ) -> RunnerGeneration:
        request_id = request.request_id or uuid4().hex
        cancel_event = self._register_request(runner_name, request_id)
        begun = False
        try:
            self._begin_request()
            begun = True
            self._require_model(runner_name, model_id)
            if cancel_event.is_set():
                raise RunnerCancelledError()
            result = self._runner(runner_name).generate(
                replace(request, request_id=request_id, cancel_event=cancel_event)
            )
            if cancel_event.is_set():
                raise RunnerCancelledError()
            return RunnerGeneration(request_id=request_id, text=result)
        except RunnerGatewayError:
            raise
        except Exception as exc:
            raise _translate_runner_error(exc) from exc
        finally:
            if begun:
                self._end_request()
            self._finish_request(runner_name, request_id)

    def stream(
        self,
        runner_name: str,
        request: ModelRequest,
        *,
        model_id: str | None = None,
    ) -> Iterator[RunnerEvent]:
        request_id = request.request_id or uuid4().hex
        cancel_event = self._register_request(runner_name, request_id)
        begun = False
        try:
            self._begin_request()
            begun = True
            self._require_model(runner_name, model_id)
            yield RunnerEvent("started", request_id)
            for chunk in self._runner(runner_name).stream(
                replace(request, request_id=request_id, cancel_event=cancel_event)
            ):
                if cancel_event.is_set():
                    yield RunnerEvent("cancelled", request_id)
                    return
                if chunk:
                    yield RunnerEvent("delta", request_id, text=chunk)
            if cancel_event.is_set():
                yield RunnerEvent("cancelled", request_id)
            else:
                yield RunnerEvent("completed", request_id)
        except GeneratorExit:
            cancel_event.set()
            raise
        except Exception as exc:
            error = _translate_runner_error(exc)
            yield RunnerEvent("error", request_id, error=error.to_dict())
        finally:
            if begun:
                self._end_request()
            self._finish_request(runner_name, request_id)

    def cancel(self, runner_name: str, request_id: str) -> bool:
        with self._lock:
            event = self._requests.get((runner_name, request_id))
        if event is None:
            return False
        event.set()
        return True

    def _runner(self, runner_name: str) -> LocalRunnerAdapter:
        with self._lock:
            runner = self._runners.get(runner_name)
            if runner is not None:
                return runner
            try:
                runner = self.registry.create(runner_name, config=self.resource_config)
            except ValueError as exc:
                raise RunnerGatewayError(
                    str(exc),
                    code="unsupported_runner",
                    retryable=False,
                    recovery_action="choose_runner",
                ) from exc
            self._runners[runner_name] = runner
            return runner

    def _invalidate_health(self, runner_name: str) -> None:
        with self._lock:
            self._health_cache.pop(runner_name, None)

    def _require_model(self, runner_name: str, model_id: str | None) -> None:
        if model_id is None:
            return
        health = self.health(runner_name, force=True)
        if health.model_id == model_id and health.ready:
            return
        raise RunnerGatewayError(
            "requested local model is not loaded",
            code="model_not_ready",
            retryable=False,
            recovery_action="load",
        )

    def _register_request(self, runner_name: str, request_id: str) -> Event:
        with self._lock:
            key = (runner_name, request_id)
            if key in self._requests:
                raise RunnerGatewayError(
                    "request ID is already running",
                    code="duplicate_request",
                    retryable=False,
                    recovery_action="retry",
                )
            event = Event()
            self._requests[key] = event
            return event

    def _finish_request(self, runner_name: str, request_id: str) -> None:
        with self._lock:
            self._requests.pop((runner_name, request_id), None)

    def _begin_request(self) -> None:
        with self._lock:
            if self._active + self._pending >= self.max_concurrency + self.max_queue:
                raise RunnerBusyError()
            self._pending += 1
        acquired = self._slots.acquire(timeout=self.queue_timeout_seconds)
        with self._lock:
            self._pending -= 1
            if acquired:
                self._active += 1
        if not acquired:
            raise RunnerBusyError()

    def _end_request(self) -> None:
        with self._lock:
            self._active -= 1
        self._slots.release()


def _translate_runner_error(error: BaseException) -> RunnerGatewayError:
    if isinstance(error, RunnerGatewayError):
        return error
    if isinstance(error, LocalModelFailure):
        return RunnerGatewayError(
            str(error),
            code=f"local_{error.fallback_reason}",
            retryable=error.fallback_reason in {"timeout", "out_of_memory"},
            recovery_action=error.recovery_action,
        )
    if isinstance(error, MemoryError):
        return RunnerGatewayError(
            "local runner ran out of memory",
            code="out_of_memory",
            retryable=True,
            recovery_action="free_memory",
        )
    if isinstance(error, (TimeoutError,)):
        return RunnerGatewayError(
            "local runner timed out",
            code="timeout",
            retryable=True,
            recovery_action="retry",
        )
    return RunnerGatewayError(
        "local runner request failed",
        code="runner_error",
        retryable=False,
        recovery_action="repair",
    )
