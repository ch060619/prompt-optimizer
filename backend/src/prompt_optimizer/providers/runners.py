from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal, Protocol

from prompt_optimizer.providers.base import ModelRequest
from prompt_optimizer.providers.local import (
    LocalModelNotInstalled,
    LocalModelUnavailable,
    LocalRunnerHealth,
)
from prompt_optimizer.runner_resources import RunnerResourceConfig

# RC ID: RC-187. Keep runner lifecycle commands behind one provider boundary.

RunnerOperationStatus = Literal["ok", "not_found", "not_ready"]


@dataclass(frozen=True)
class RunnerModel:
    model_id: str
    loaded: bool = False


@dataclass(frozen=True)
class RunnerOperation:
    status: RunnerOperationStatus
    model_id: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {
            "status": self.status,
            "model_id": self.model_id,
            "detail": self.detail,
        }


class LocalRunnerAdapter(Protocol):
    name: str

    def pull(self, model_id: str) -> RunnerOperation:
        ...

    def load(self, model_id: str) -> RunnerOperation:
        ...

    def generate(self, request: ModelRequest) -> str:
        ...

    def stream(self, request: ModelRequest) -> Iterator[str]:
        ...

    def stop(self, model_id: str) -> RunnerOperation:
        ...

    def list(self) -> tuple[RunnerModel, ...]:
        ...

    def remove(self, model_id: str) -> RunnerOperation:
        ...

    def health(self) -> LocalRunnerHealth:
        ...

    def version(self) -> str:
        ...

    def configure(self, config: RunnerResourceConfig) -> RunnerResourceConfig:
        ...

    def recover_from_oom(self) -> RunnerResourceConfig:
        ...

    def release_if_idle(self, now: float | None = None) -> bool:
        ...


class InMemoryRunnerAdapter:
    """Deterministic runner fixture used until real process adapters are enabled."""

    name: str

    def __init__(self, name: Literal["ollama", "llama-cpp"]) -> None:
        self.name = name
        self._models: dict[str, bool] = {}
        self._active_model: str | None = None
        self._config = RunnerResourceConfig()
        self._last_activity = 0.0

    @property
    def config(self) -> RunnerResourceConfig:
        return self._config

    def configure(self, config: RunnerResourceConfig) -> RunnerResourceConfig:
        self._config = config
        return config

    def pull(self, model_id: str) -> RunnerOperation:
        self._models.setdefault(model_id, False)
        return RunnerOperation("ok", model_id, "model is available")

    def load(self, model_id: str) -> RunnerOperation:
        if model_id not in self._models:
            return RunnerOperation("not_found", model_id, "model is not installed")
        self._models[model_id] = True
        self._active_model = model_id
        self._last_activity = _monotonic()
        return RunnerOperation("ok", model_id, "model loaded")

    def generate(self, request: ModelRequest) -> str:
        self._require_loaded()
        self._last_activity = _monotonic()
        return f"[{self.name}] {request.prompt}"

    def version(self) -> str:
        return f"{self.name}-in-memory-1"

    def stream(self, request: ModelRequest) -> Iterator[str]:
        content = self.generate(request)
        for chunk in content.split(" "):
            if request.cancel_event is not None and request.cancel_event.is_set():
                return
            yield chunk

    def stop(self, model_id: str) -> RunnerOperation:
        if model_id not in self._models:
            return RunnerOperation("not_found", model_id, "model is not installed")
        self._models[model_id] = False
        if self._active_model == model_id:
            self._active_model = None
        return RunnerOperation("ok", model_id, "model stopped")

    def recover_from_oom(self) -> RunnerResourceConfig:
        if self._active_model is not None:
            self.stop(self._active_model)
        self._config = self._config.reduced_for_oom()
        return self._config

    def release_if_idle(self, now: float | None = None) -> bool:
        if self._active_model is None:
            return False
        current = _monotonic() if now is None else now
        if current - self._last_activity < self._config.idle_timeout_seconds:
            return False
        self.stop(self._active_model)
        return True

    def list(self) -> tuple[RunnerModel, ...]:
        return tuple(
            RunnerModel(model_id=model_id, loaded=loaded)
            for model_id, loaded in sorted(self._models.items())
        )

    def remove(self, model_id: str) -> RunnerOperation:
        if model_id not in self._models:
            return RunnerOperation("not_found", model_id, "model is not installed")
        del self._models[model_id]
        if self._active_model == model_id:
            self._active_model = None
        return RunnerOperation("ok", model_id, "model removed")

    def health(self) -> LocalRunnerHealth:
        if not self._models:
            return LocalRunnerHealth(
                False,
                detail="runner has no installed models",
                status="not_installed",
            )
        if self._active_model is None:
            return LocalRunnerHealth(
                False,
                detail="runner has no loaded model",
                status="not_ready",
            )
        return LocalRunnerHealth(
            True,
            model_id=self._active_model,
            detail="runner ready",
            status="ready",
        )

    def _require_loaded(self) -> None:
        health = self.health()
        if health.ready:
            return
        if health.status == "not_installed":
            raise LocalModelNotInstalled(health.detail)
        raise LocalModelUnavailable(health.detail)


class RunnerRegistry:
    def __init__(self) -> None:
        self._factories = {
            "ollama": lambda: InMemoryRunnerAdapter("ollama"),
            "llama-cpp": lambda: InMemoryRunnerAdapter("llama-cpp"),
        }

    def create(
        self,
        name: str = "ollama",
        *,
        config: RunnerResourceConfig | None = None,
    ) -> LocalRunnerAdapter:
        try:
            runner = self._factories[name]()
        except KeyError as exc:
            raise ValueError(f"unsupported local runner: {name}") from exc
        if config is not None:
            runner.configure(config)
        return runner


DEFAULT_RUNNER = "ollama"
RUNNER_COMPARISON: tuple[dict[str, str], ...] = (
    {
        "id": "ollama",
        "license": "MIT",
        "api": "local HTTP API",
        "gpu": "CUDA/Metal/ROCm through runtime",
        "install": "managed runtime",
        "maintenance": "runtime project",
    },
    {
        "id": "llama-cpp",
        "license": "MIT",
        "api": "llama-server HTTP API or CLI",
        "gpu": "CUDA/Metal/Vulkan/CPU build dependent",
        "install": "user-managed binary",
        "maintenance": "build and binary lifecycle",
    },
)


def _monotonic() -> float:
    from time import monotonic

    return monotonic()
