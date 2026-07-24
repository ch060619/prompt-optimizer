from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from time import perf_counter
from typing import Literal, Protocol

from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.providers.base import (
    ModelProviderError,
    ModelRequest,
    ModelResponse,
    ProviderCapabilities,
    ProviderEvent,
    ProviderEventType,
    ProviderTimeoutError,
)

# RC ID: RC-149. Keep local model generation behind a runner adapter with no network client.


LocalRunnerStatus = Literal["ready", "not_installed", "not_ready", "out_of_memory", "timeout"]
LocalFallbackReason = Literal["not_installed", "not_ready", "out_of_memory", "timeout"]
LocalRecoveryAction = Literal["install", "repair", "free_memory", "retry"]


@dataclass(frozen=True)
class LocalRunnerHealth:
    ready: bool
    model_id: str | None = None
    detail: str = ""
    status: LocalRunnerStatus | None = None
    temperature_celsius: float | None = None


class LocalModelRunner(Protocol):
    def health(self) -> LocalRunnerHealth:
        pass

    def generate(self, request: ModelRequest) -> str:
        pass

    def stream(self, request: ModelRequest) -> Iterator[str]:
        pass


class LocalModelFailure(ModelProviderError):
    fallback_reason: LocalFallbackReason
    recovery_action: LocalRecoveryAction

    def __init__(
        self,
        message: str,
        *,
        fallback_reason: LocalFallbackReason,
        recovery_action: LocalRecoveryAction,
    ) -> None:
        super().__init__(message)
        self.fallback_reason = fallback_reason
        self.recovery_action = recovery_action


class LocalModelNotInstalled(LocalModelFailure):
    def __init__(self, message: str = "本地模型尚未安装。") -> None:
        super().__init__(message, fallback_reason="not_installed", recovery_action="install")


class LocalModelUnavailable(LocalModelFailure):
    def __init__(self, message: str = "本地模型运行器尚未就绪。") -> None:
        super().__init__(message, fallback_reason="not_ready", recovery_action="repair")


class LocalModelOutOfMemory(LocalModelFailure):
    def __init__(self, message: str = "本地模型运行器资源不足。") -> None:
        super().__init__(message, fallback_reason="out_of_memory", recovery_action="free_memory")


class LocalModelTimeout(LocalModelFailure):
    def __init__(self, message: str = "本地模型运行器响应超时。") -> None:
        super().__init__(message, fallback_reason="timeout", recovery_action="retry")


class UnavailableLocalRunner:
    def health(self) -> LocalRunnerHealth:
        return LocalRunnerHealth(
            False,
            detail="local runner is not configured",
            status="not_installed",
        )

    def generate(self, request: ModelRequest) -> str:
        raise LocalModelNotInstalled()

    def stream(self, request: ModelRequest) -> Iterator[str]:
        raise LocalModelNotInstalled()
        yield ""


class LocalModelProvider:
    name = "local"
    display_name = "Local Model"
    execution_location = "local"
    network_access = False
    credential_ref = None
    capabilities = ProviderCapabilities(streaming=True)

    def __init__(
        self,
        runner: LocalModelRunner | None = None,
        analyzer: Analyzer | None = None,
    ) -> None:
        self.runner = runner or UnavailableLocalRunner()
        self.analyzer = analyzer or Analyzer()

    @property
    def model(self) -> str | None:
        return self.runner.health().model_id

    def health(self) -> LocalRunnerHealth:
        return self.runner.health()

    def optimize(self, request: ModelRequest) -> ModelResponse:
        self._require_ready()
        started = perf_counter()
        try:
            content = self.runner.generate(request)
        except LocalModelFailure:
            raise
        except (MemoryError, ProviderTimeoutError, TimeoutError) as exc:
            if isinstance(exc, MemoryError):
                self._recover_after_oom()
            raise _translate_runner_error(exc) from exc
        if not content.strip():
            raise LocalModelUnavailable("本地模型未返回有效结果。")
        analysis = self.analyzer.analyze(content)
        analysis.optimized_prompt = content
        return ModelResponse(
            analysis=analysis,
            provider_used=self.name,
            latency_ms=int((perf_counter() - started) * 1000),
        )

    def stream(self, request: ModelRequest) -> Iterator[ProviderEvent]:
        self._require_ready()
        yield ProviderEvent(ProviderEventType.STARTED)
        try:
            for chunk in self.runner.stream(request):
                if chunk:
                    yield ProviderEvent(ProviderEventType.DELTA, text=chunk)
        except LocalModelFailure:
            raise
        except (MemoryError, ProviderTimeoutError, TimeoutError) as exc:
            if isinstance(exc, MemoryError):
                self._recover_after_oom()
            raise _translate_runner_error(exc) from exc
        yield ProviderEvent(ProviderEventType.COMPLETED)

    def _require_ready(self) -> None:
        health = self.health()
        if not health.ready:
            detail = health.detail or "本地模型运行器尚未就绪。"
            status = health.status or "not_ready"
            if status == "not_installed":
                raise LocalModelNotInstalled(detail)
            if status == "out_of_memory":
                self._recover_after_oom()
                raise LocalModelOutOfMemory(detail)
            if status == "timeout":
                raise LocalModelTimeout(detail)
            raise LocalModelUnavailable(detail)

    def _recover_after_oom(self) -> None:
        recover = getattr(self.runner, "recover_from_oom", None)
        if callable(recover):
            recover()


def _translate_runner_error(error: BaseException) -> LocalModelFailure:
    if isinstance(error, MemoryError):
        return LocalModelOutOfMemory()
    if isinstance(error, (ProviderTimeoutError, TimeoutError)):
        return LocalModelTimeout()
    raise TypeError(f"unsupported local runner error: {type(error).__name__}")
