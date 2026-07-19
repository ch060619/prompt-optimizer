from __future__ import annotations

from pathlib import Path
from threading import Event, Thread
from time import sleep

import pytest
from backend.rabbit_code.agent import AgentCore, AgentEventType
from backend.rabbit_code.agent_state import AgentState, JsonCheckpointStore
from backend.rabbit_code.run_control import (
    IdempotencyLedger,
    JsonIdempotencyStore,
    JsonRunControlStore,
    OperationKind,
    RunCommand,
    RunController,
    RunStatus,
    UnsafeRetry,
)

from prompt_optimizer.providers.base import (
    ModelRequest,
    ProviderCapabilities,
    ProviderEvent,
    ProviderEventType,
)

# RC ID: RC-073. Verify command recovery, durable attempt chains, and no duplicate writes.


class CountingProvider:
    name = "counting"
    capabilities = ProviderCapabilities(streaming=True)

    def __init__(self) -> None:
        self.calls = 0

    def optimize(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        raise AssertionError("streaming should not call optimize")

    def stream(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        self.calls += 1
        yield ProviderEvent(ProviderEventType.DELTA, text="稳定结果")
        yield ProviderEvent(ProviderEventType.COMPLETED)


class BlockingProvider(CountingProvider):
    def __init__(self) -> None:
        super().__init__()
        self.release = Event()

    def stream(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        self.calls += 1
        self.release.wait(timeout=2)
        yield ProviderEvent(ProviderEventType.DELTA, text="恢复结果")
        yield ProviderEvent(ProviderEventType.COMPLETED)


def test_model_retry_persists_the_full_attempt_chain(tmp_path: Path) -> None:
    store = JsonIdempotencyStore(tmp_path / "ledger")
    ledger = IdempotencyLedger(store)
    calls = 0

    def fail_once() -> str:
        nonlocal calls
        calls += 1
        raise RuntimeError("temporary model failure")

    with pytest.raises(RuntimeError, match="temporary model failure"):
        ledger.execute("request-1", OperationKind.MODEL, fail_once)

    assert ledger.execute("request-1", OperationKind.MODEL, lambda: "recovered") == "recovered"
    reloaded = IdempotencyLedger(JsonIdempotencyStore(tmp_path / "ledger"))

    assert calls == 1
    assert [(record.attempt, record.state) for record in reloaded.history_for("request-1")] == [
        (1, "in_flight"),
        (1, "failed"),
        (2, "in_flight"),
        (2, "succeeded"),
    ]


def test_failed_write_is_never_replayed_after_recovery(tmp_path: Path) -> None:
    ledger = IdempotencyLedger(JsonIdempotencyStore(tmp_path / "ledger"))
    writes: list[str] = []

    def failed_write() -> None:
        writes.append("submitted")
        raise RuntimeError("write acknowledgement lost")

    with pytest.raises(RuntimeError, match="acknowledgement"):
        ledger.execute("write-1", OperationKind.WRITE, failed_write)
    with pytest.raises(UnsafeRetry, match="cannot be safely retried"):
        ledger.execute("write-1", OperationKind.WRITE, lambda: writes.append("duplicate"))

    assert writes == ["submitted"]


def test_run_controller_commands_are_durable_and_retryable(tmp_path: Path) -> None:
    store = JsonRunControlStore(tmp_path / "runs")
    controller = RunController("run-1", store=store)
    controller.command(RunCommand.PAUSE)
    restored = RunController("run-1", store=store)

    assert restored.status is RunStatus.PAUSED
    restored.command(RunCommand.RESUME)
    restored.mark_failed()
    restored.command(RunCommand.RETRY)
    restored.mark_failed()
    regenerated = restored.command(RunCommand.REGENERATE)

    assert regenerated == "run-1:gen-1"
    assert restored.status is RunStatus.RUNNING
    reloaded = RunController("run-1:gen-1", store=store)
    assert [event.command for event in reloaded.events] == [
        RunCommand.PAUSE,
        RunCommand.RESUME,
        RunCommand.RETRY,
        RunCommand.REGENERATE,
    ]


def test_agent_core_pauses_at_event_boundary_and_cancel_is_terminal(tmp_path: Path) -> None:
    provider = BlockingProvider()
    control = RunController("controlled-run")
    checkpoint_store = JsonCheckpointStore(tmp_path / "checkpoints")
    stream = AgentCore(
        provider,
        checkpoint_store=checkpoint_store,
        run_control=control,
    ).stream(ModelRequest(prompt="控制"), request_id="controlled-run")

    assert next(stream).type is AgentEventType.STARTED
    control.command(RunCommand.PAUSE)
    result: list[object] = []
    worker = Thread(target=lambda: result.append(next(stream)), daemon=True)
    worker.start()
    sleep(0.05)
    assert result == []

    provider.release.set()
    control.command(RunCommand.RESUME)
    worker.join(timeout=2)
    assert result and result[0].type is AgentEventType.DELTA  # type: ignore[union-attr]
    assert list(stream)[-1].type is AgentEventType.COMPLETED

    cancelled_control = RunController("cancelled-run")
    cancelled_stream = AgentCore(
        CountingProvider(),
        checkpoint_store=checkpoint_store,
        run_control=cancelled_control,
    ).stream(ModelRequest(prompt="取消"), request_id="cancelled-run")
    assert next(cancelled_stream).type is AgentEventType.STARTED
    cancelled_control.command(RunCommand.CANCEL)
    assert [event.type for event in cancelled_stream] == [AgentEventType.CANCELLED]
    checkpoint = checkpoint_store.load("cancelled-run")
    assert checkpoint is not None
    assert checkpoint.state is AgentState.CANCELLED


def test_agent_core_reuses_successful_model_request_by_idempotency_key() -> None:
    provider = CountingProvider()
    ledger = IdempotencyLedger()
    core = AgentCore(provider, idempotency_ledger=ledger)
    request = ModelRequest(prompt="相同请求")

    first = list(core.stream(request, request_id="same-request"))
    second = list(core.stream(request, request_id="same-request"))

    assert provider.calls == 1
    assert [event.type for event in first] == [event.type for event in second]
    assert "same-request:model" in [record.key for record in ledger.history]
