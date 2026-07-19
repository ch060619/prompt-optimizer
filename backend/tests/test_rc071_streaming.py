from __future__ import annotations

from pathlib import Path

import pytest
from backend.rabbit_code.agent import AgentCore, AgentEvent, AgentEventType
from backend.rabbit_code.agent_state import AgentState, JsonCheckpointStore
from backend.rabbit_code.streaming import StreamAccumulator

from prompt_optimizer.providers.base import (
    ModelRequest,
    ProviderCapabilities,
    ProviderEvent,
    ProviderEventType,
)

# RC ID: RC-071. Verify ordered unified events, aggregation, warnings, and cancellation persistence.


class FakeProvider:
    name = "fake"
    capabilities = ProviderCapabilities(streaming=True)

    def optimize(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        raise AssertionError("streaming should not call optimize")

    def stream(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        yield ProviderEvent(ProviderEventType.STARTED)
        yield ProviderEvent(ProviderEventType.DELTA, text="第一段")
        yield ProviderEvent(ProviderEventType.DELTA, text="第二段")
        yield ProviderEvent(ProviderEventType.COMPLETED)


def test_accumulator_preserves_order_and_aggregates_text() -> None:
    accumulator = StreamAccumulator()
    for event in (
        AgentEvent(AgentEventType.STARTED, sequence=0),
        AgentEvent(AgentEventType.PROGRESS, "准备模型", 1),
        AgentEvent(AgentEventType.DELTA, "第一段", 2),
        AgentEvent(AgentEventType.WARNING, payload={"message": "部分结果"}, sequence=3),
        AgentEvent(AgentEventType.DELTA, "第二段", 4),
        AgentEvent(AgentEventType.COMPLETED, sequence=5),
    ):
        accumulator.add(event)

    summary = accumulator.summary()
    assert summary.text == "第一段第二段"
    assert summary.terminal is AgentEventType.COMPLETED
    assert [event.type for event in summary.events] == [
        AgentEventType.STARTED,
        AgentEventType.PROGRESS,
        AgentEventType.DELTA,
        AgentEventType.WARNING,
        AgentEventType.DELTA,
        AgentEventType.COMPLETED,
    ]


def test_accumulator_rejects_gaps_and_events_after_terminal() -> None:
    accumulator = StreamAccumulator()
    accumulator.add(AgentEvent(AgentEventType.STARTED, sequence=0))
    with pytest.raises(ValueError, match="not contiguous"):
        accumulator.add(AgentEvent(AgentEventType.DELTA, "gap", sequence=2))

    accumulator.add(AgentEvent(AgentEventType.COMPLETED, sequence=1))
    with pytest.raises(ValueError, match="after a terminal"):
        accumulator.add(AgentEvent(AgentEventType.WARNING, sequence=2))


def test_agent_core_sequences_events_and_closing_stream_persists_cancelled(
    tmp_path: Path,
) -> None:
    store = JsonCheckpointStore(tmp_path)
    stream = AgentCore(FakeProvider(), checkpoint_store=store).stream(
        ModelRequest(prompt="关闭测试"),
        request_id="closed-run",
    )

    first = next(stream)
    stream.close()
    checkpoint = store.load("closed-run")

    assert first.sequence == 0
    assert checkpoint is not None
    assert checkpoint.state is AgentState.CANCELLED
    assert checkpoint.events[-1].payload["reason"] == "stream closed"


def test_agent_core_stream_is_aggregatable() -> None:
    accumulator = StreamAccumulator()
    for event in AgentCore(FakeProvider()).stream(ModelRequest(prompt="聚合测试")):
        accumulator.add(event)

    assert accumulator.summary().text
    assert accumulator.terminal is AgentEventType.COMPLETED
