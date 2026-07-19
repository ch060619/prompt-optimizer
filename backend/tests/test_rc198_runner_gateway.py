from __future__ import annotations

from threading import Event, Thread

import pytest
from fastapi.testclient import TestClient

from prompt_optimizer.api.app import create_app
from prompt_optimizer.providers import ModelRequest
from prompt_optimizer.providers.runners import InMemoryRunnerAdapter, RunnerRegistry
from prompt_optimizer.runner_gateway import (
    LocalRunnerGateway,
    RunnerBusyError,
)

# RC ID: RC-198. Verify one FastAPI-facing contract for local runner lifecycle and events.


def test_gateway_exposes_runner_capabilities_and_model_lifecycle() -> None:
    gateway = LocalRunnerGateway()

    capabilities = gateway.capabilities("ollama")
    assert capabilities.streaming is True
    assert capabilities.cancellation is True
    assert capabilities.model_listing is True
    assert gateway.pull("ollama", "gemma-3-1b-it").status == "ok"
    assert gateway.load("ollama", "gemma-3-1b-it").status == "ok"
    assert gateway.health("ollama").ready is True
    assert gateway.generate("ollama", ModelRequest(prompt="hello")).text == "[ollama] hello"
    assert gateway.unload("ollama", "gemma-3-1b-it").status == "ok"
    assert gateway.health("ollama").ready is False


def test_stream_emits_shared_events_and_cancel_is_terminal() -> None:
    gateway = LocalRunnerGateway()
    gateway.pull("ollama", "gemma-3-1b-it")
    gateway.load("ollama", "gemma-3-1b-it")
    events = gateway.stream(
        "ollama",
        ModelRequest(prompt="one two", request_id="rc198-cancel"),
    )

    assert next(events).event == "started"
    assert next(events).event == "delta"
    assert gateway.cancel("ollama", "rc198-cancel") is True
    assert next(events).event == "cancelled"
    assert list(events) == []


def test_health_cache_is_reused_until_invalidated() -> None:
    clock = [100.0]
    runner = RunnerRegistry().create("ollama")
    calls = 0
    original_health = runner.health

    def counted_health():
        nonlocal calls
        calls += 1
        return original_health()

    runner.health = counted_health  # type: ignore[method-assign]

    class ExistingRunnerRegistry(RunnerRegistry):
        def create(self, name="ollama", *, config=None):
            return runner

    gateway = LocalRunnerGateway(
        registry=ExistingRunnerRegistry(), clock=lambda: clock[0], health_ttl_seconds=5
    )
    gateway.health("ollama")
    gateway.health("ollama")
    assert calls == 1
    clock[0] = 106.0
    gateway.health("ollama")
    assert calls == 2


def test_queue_rejects_work_beyond_configured_capacity() -> None:
    started = Event()
    release = Event()

    class BlockingRunner(InMemoryRunnerAdapter):
        def generate(self, request: ModelRequest) -> str:
            started.set()
            assert release.wait(timeout=2)
            return super().generate(request)

    class BlockingRegistry(RunnerRegistry):
        def create(self, name="ollama", *, config=None):
            runner = BlockingRunner(name)
            if config is not None:
                runner.configure(config)
            return runner

    gateway = LocalRunnerGateway(registry=BlockingRegistry(), max_concurrency=1, max_queue=0)
    gateway.pull("ollama", "gemma-3-1b-it")
    gateway.load("ollama", "gemma-3-1b-it")
    errors: list[BaseException] = []
    worker = Thread(
        target=lambda: gateway.generate("ollama", ModelRequest(prompt="first")),
        daemon=True,
    )
    worker.start()
    assert started.wait(timeout=2)
    with pytest.raises(RunnerBusyError):
        gateway.generate("ollama", ModelRequest(prompt="second"))
    release.set()
    worker.join(timeout=2)
    assert not worker.is_alive()
    assert errors == []


def test_fastapi_runner_routes_use_gateway_without_command_construction() -> None:
    gateway = LocalRunnerGateway()
    gateway.pull("ollama", "gemma-3-1b-it")
    app = create_app(runner_gateway=gateway)
    client = TestClient(app)

    capabilities = client.get("/api/v1/local-runners/ollama/capabilities")
    assert capabilities.status_code == 200
    assert capabilities.json()["cancellation"] is True
    assert client.post("/api/v1/local-runners/ollama/models/gemma-3-1b-it/load").status_code == 200
    generated = client.post(
        "/api/v1/local-runners/ollama/generate",
        json={"prompt": "api prompt", "request_id": "rc198-api"},
    )
    assert generated.status_code == 200
    assert generated.json()["text"] == "[ollama] api prompt"
    streamed = client.post(
        "/api/v1/local-runners/ollama/stream",
        json={"prompt": "api stream", "request_id": "rc198-stream"},
    )
    assert streamed.status_code == 200
    assert "event: started" in streamed.text
    assert "event: completed" in streamed.text
    assert (
        client.post("/api/v1/local-runners/ollama/models/gemma-3-1b-it/unload").status_code
        == 200
    )
