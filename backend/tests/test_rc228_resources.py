from __future__ import annotations

from threading import Event, Thread

import pytest
from fastapi.testclient import TestClient

from prompt_optimizer.api.app import create_app
from prompt_optimizer.hardware import HardwareField, HardwareReport
from prompt_optimizer.providers import (
    InMemoryRunnerAdapter,
    LocalRunnerHealth,
    RunnerResourceConfig,
)
from prompt_optimizer.providers.runners import RunnerRegistry
from prompt_optimizer.runner_gateway import LocalRunnerGateway, RunnerGatewayError


class _CapturingRegistry(RunnerRegistry):
    def __init__(self) -> None:
        super().__init__()
        self.configs: list[RunnerResourceConfig | None] = []

    def create(self, name="ollama", *, config=None):
        self.configs.append(config)
        return InMemoryRunnerAdapter(name)


def test_gateway_applies_resource_config_to_runner_and_reports_queue_capacity() -> None:
    config = RunnerResourceConfig(
        threads=4,
        gpu_layers=8,
        context_length=8192,
        concurrency=2,
        idle_timeout_seconds=30,
    )
    registry = _CapturingRegistry()
    gateway = LocalRunnerGateway(registry=registry, resource_config=config)

    gateway.pull("ollama", "demo")

    assert registry.configs == [config]
    assert gateway.resource_config == config
    status = gateway.queue_status()
    assert status.active == 0
    assert status.pending == 0
    assert status.capacity == 2
    assert status.available == 2


def test_gateway_derives_conservative_resources_from_hardware_report() -> None:
    report = HardwareReport(
        fields={
            "cpu": HardwareField({"logical_cores": 16}, "test", "user"),
            "ram": HardwareField({"total_bytes": 16 * 1024**3}, "test", "user"),
            "gpu": HardwareField(
                {"devices": [{"memory_mb": 8192}]},
                "test",
                "user",
            ),
        }
    )

    gateway = LocalRunnerGateway(hardware_report=report, context_length=32768)

    assert gateway.resource_config.threads == 8
    assert gateway.resource_config.gpu_layers == 16
    assert gateway.resource_config.context_length == 32768
    assert gateway.resource_config.concurrency == 1


def test_user_can_lower_resources_when_runner_is_idle() -> None:
    gateway = LocalRunnerGateway(
        resource_config=RunnerResourceConfig(
            threads=8,
            gpu_layers=16,
            context_length=16384,
            concurrency=2,
            idle_timeout_seconds=900,
        )
    )
    lowered = RunnerResourceConfig(
        threads=2,
        gpu_layers=0,
        context_length=4096,
        concurrency=1,
        idle_timeout_seconds=60,
    )

    assert gateway.configure_resources(lowered) == lowered
    assert gateway.resource_config == lowered
    assert gateway.queue_status().capacity == 1


def test_api_exposes_queue_signal_and_resource_lowering() -> None:
    gateway = LocalRunnerGateway()
    client = TestClient(create_app(runner_gateway=gateway))

    lowered = client.post(
        "/api/v1/local-runners/ollama/resources",
        json={"threads": 1, "context_length": 2048},
    )
    assert lowered.status_code == 200
    assert lowered.json()["config"]["threads"] == 1
    assert lowered.json()["config"]["context_length"] == 2048

    queue = client.get("/api/v1/local-runners/ollama/queue")
    assert queue.status_code == 200
    assert queue.json()["capacity"] == 1


def test_resource_signal_reports_temperature_and_oom_without_fabricating_values() -> None:
    class SignalRunner(InMemoryRunnerAdapter):
        def health(self) -> LocalRunnerHealth:
            return LocalRunnerHealth(
                True,
                model_id="demo",
                status="ready",
                temperature_celsius=92.0,
            )

    class SignalRegistry(RunnerRegistry):
        def create(self, name="ollama", *, config=None):
            return SignalRunner(name)

    gateway = LocalRunnerGateway(
        registry=SignalRegistry(),
        resource_config=RunnerResourceConfig(temperature_limit_celsius=90.0),
    )

    gateway.pull("ollama", "demo")
    signal = gateway.resource_signal("ollama")

    assert signal == {
        "runner": "ollama",
        "out_of_memory": False,
        "temperature_celsius": 92.0,
        "temperature_limit_celsius": 90.0,
        "should_throttle": True,
    }


def test_queue_status_exposes_waiting_work_and_busy_error_has_recovery_action() -> None:
    started = Event()
    release = Event()

    class BlockingRunner(InMemoryRunnerAdapter):
        def generate(self, request):
            started.set()
            assert release.wait(timeout=2)
            return super().generate(request)

    class BlockingRegistry(RunnerRegistry):
        def create(self, name="ollama", *, config=None):
            return BlockingRunner(name)

    gateway = LocalRunnerGateway(
        registry=BlockingRegistry(),
        resource_config=RunnerResourceConfig(concurrency=1),
        max_queue=1,
        queue_timeout_seconds=0.05,
    )
    gateway.pull("ollama", "demo")
    gateway.load("ollama", "demo")
    first = Thread(target=lambda: gateway.generate("ollama", request("first")), daemon=True)
    first.start()
    assert started.wait(timeout=2)

    second = Thread(target=lambda: gateway.generate("ollama", request("second")), daemon=True)
    second.start()
    assert wait_for_pending(gateway)
    assert gateway.queue_status().pending == 1

    with pytest.raises(RunnerGatewayError) as raised:
        gateway.configure_resources(RunnerResourceConfig(concurrency=1))
    assert raised.value.code == "runner_busy"
    assert raised.value.recovery_action == "wait_and_retry"

    release.set()
    first.join(timeout=2)
    second.join(timeout=2)
    assert not first.is_alive()
    assert not second.is_alive()


def request(prompt: str):
    from prompt_optimizer.providers import ModelRequest

    return ModelRequest(prompt=prompt)


def wait_for_pending(gateway: LocalRunnerGateway) -> bool:
    for _ in range(100):
        if gateway.queue_status().pending:
            return True
    return False
