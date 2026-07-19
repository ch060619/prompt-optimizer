from __future__ import annotations

from pathlib import Path
from threading import Event

import pytest
from backend.rabbit_code.agent import AgentCore, AgentEventType
from backend.rabbit_code.agent_state import (
    AgentState,
    AgentStateMachine,
    JsonCheckpointStore,
)

from prompt_optimizer.providers.base import (
    ModelRequest,
    ProviderCapabilities,
    ProviderEvent,
    ProviderEventType,
)

# RC ID: RC-068. Verify Agent transitions, replay, checkpoints, completion, failure, and cancel.


class FakeProvider:
    name = "fake"
    capabilities = ProviderCapabilities(streaming=True)

    def optimize(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        raise AssertionError("state-machine stream should not call optimize")

    def stream(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        yield ProviderEvent(ProviderEventType.STARTED)
        yield ProviderEvent(ProviderEventType.DELTA, text="状态")
        yield ProviderEvent(ProviderEventType.COMPLETED)


class FailingProvider(FakeProvider):
    def stream(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        raise RuntimeError("provider failed")
        yield  # pragma: no cover


def test_state_machine_rejects_illegal_transitions_and_replays_events() -> None:
    machine = AgentStateMachine("run-1")
    machine.transition(AgentState.CONTEXT)
    machine.transition(AgentState.MODEL)
    machine.transition(AgentState.COMPLETED)

    replayed = AgentStateMachine.replay("run-1", machine.events)

    assert replayed.state is AgentState.COMPLETED
    assert replayed.events == machine.events
    with pytest.raises(TypeError):
        replayed.events[0].payload["mutate"] = True  # type: ignore[index]
    with pytest.raises(ValueError, match="invalid Agent transition"):
        replayed.transition(AgentState.MODEL)


def test_json_checkpoint_store_round_trips_a_completed_run(tmp_path: Path) -> None:
    store = JsonCheckpointStore(tmp_path)
    machine = AgentStateMachine("persistent-run", store)
    machine.transition(AgentState.CONTEXT)
    machine.transition(AgentState.MODEL)
    machine.transition(AgentState.COMPLETED)

    checkpoint = store.load("persistent-run")

    assert checkpoint is not None
    assert checkpoint.state is AgentState.COMPLETED
    assert checkpoint.events == machine.events


def test_agent_core_persists_completed_checkpoint(tmp_path: Path) -> None:
    store = JsonCheckpointStore(tmp_path)
    core = AgentCore(FakeProvider(), checkpoint_store=store)

    events = list(core.stream(ModelRequest(prompt="测试状态机"), request_id="completed-run"))
    checkpoint = store.load("completed-run")

    assert [event.type for event in events] == [
        AgentEventType.STARTED,
        AgentEventType.DELTA,
        AgentEventType.COMPLETED,
    ]
    assert checkpoint is not None
    assert checkpoint.state is AgentState.COMPLETED
    assert [event.to_state for event in checkpoint.events] == [
        AgentState.CONTEXT,
        AgentState.MODEL,
        AgentState.COMPLETED,
    ]


def test_agent_core_persists_cancelled_checkpoint(tmp_path: Path) -> None:
    store = JsonCheckpointStore(tmp_path)
    cancellation = Event()
    cancellation.set()

    events = list(
        AgentCore(FakeProvider(), checkpoint_store=store).stream(
            ModelRequest(prompt="取消测试"),
            cancellation=cancellation,
            request_id="cancelled-run",
        )
    )

    checkpoint = store.load("cancelled-run")
    assert [event.type for event in events] == [AgentEventType.STARTED, AgentEventType.CANCELLED]
    assert checkpoint is not None
    assert checkpoint.state is AgentState.CANCELLED


def test_agent_core_persists_failed_checkpoint(tmp_path: Path) -> None:
    store = JsonCheckpointStore(tmp_path)

    events = list(
        AgentCore(FailingProvider(), checkpoint_store=store).stream(
            ModelRequest(prompt="失败测试"),
            request_id="failed-run",
        )
    )

    checkpoint = store.load("failed-run")
    assert events[-1].type is AgentEventType.FAILED
    assert checkpoint is not None
    assert checkpoint.state is AgentState.FAILED
