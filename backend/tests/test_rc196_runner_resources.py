from __future__ import annotations

from collections.abc import Iterator

import pytest

from prompt_optimizer.hardware import HardwareField, HardwareReport
from prompt_optimizer.providers import (
    InMemoryRunnerAdapter,
    LocalModelOutOfMemory,
    LocalModelProvider,
    LocalRunnerHealth,
    ModelRequest,
    RunnerResourceConfig,
    safe_runner_config,
)

# RC ID: RC-196. Verify safe resource defaults, OOM recovery, and idle unload.


def hardware_report(*, cores: int, ram_bytes: int, gpu_memory_mb: int = 0) -> HardwareReport:
    return HardwareReport(
        fields={
            "cpu": HardwareField({"logical_cores": cores}, "test", "user"),
            "ram": HardwareField({"total_bytes": ram_bytes}, "test", "user"),
            "gpu": HardwareField(
                {"devices": [{"memory_mb": gpu_memory_mb}] if gpu_memory_mb else []},
                "test",
                "user",
            ),
        }
    )


def test_safe_defaults_cover_cpu_only_and_gpu_capacity() -> None:
    cpu = safe_runner_config(hardware_report(cores=2, ram_bytes=4 * 1024**3), context_length=8192)
    gpu = safe_runner_config(
        hardware_report(cores=16, ram_bytes=16 * 1024**3, gpu_memory_mb=8192),
        context_length=32768,
    )

    assert cpu.threads == 1
    assert cpu.gpu_layers == 0
    assert cpu.context_length == 2048
    assert gpu.threads == 8
    assert gpu.gpu_layers == 16
    assert gpu.context_length == 32768
    assert gpu.concurrency == 1


def test_runner_can_lower_resources_after_oom_and_release_idle_model() -> None:
    runner = InMemoryRunnerAdapter("ollama")
    runner.configure(
        RunnerResourceConfig(
            threads=4,
            gpu_layers=8,
            context_length=8192,
            concurrency=2,
            idle_timeout_seconds=10,
        )
    )
    runner.pull("gemma-3-1b-it")
    runner.load("gemma-3-1b-it")
    reduced = runner.recover_from_oom()

    assert reduced.threads == 3
    assert reduced.gpu_layers == 4
    assert reduced.context_length == 6144
    assert reduced.concurrency == 1
    assert runner.health().status == "not_ready"

    runner.load("gemma-3-1b-it")
    assert runner.release_if_idle(now=10**9) is True
    assert runner.health().status == "not_ready"
    assert runner.release_if_idle(now=10**9) is False


class OOMRunner:
    def __init__(self) -> None:
        self.recoveries = 0

    def health(self) -> LocalRunnerHealth:
        return LocalRunnerHealth(True, model_id="gemma-3-1b-it", status="ready")

    def generate(self, request: ModelRequest) -> str:
        raise MemoryError("test oom")

    def stream(self, request: ModelRequest) -> Iterator[str]:
        raise MemoryError("test oom")
        yield ""

    def recover_from_oom(self) -> RunnerResourceConfig:
        self.recoveries += 1
        return RunnerResourceConfig(threads=1, gpu_layers=0, context_length=2048)


def test_provider_reports_oom_after_one_recovery_without_retry_loop() -> None:
    runner = OOMRunner()
    provider = LocalModelProvider(runner)

    with pytest.raises(LocalModelOutOfMemory):
        provider.optimize(ModelRequest(prompt="resource test"))

    assert runner.recoveries == 1
