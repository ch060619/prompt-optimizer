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
from backend.rabbit_code.budget import BudgetController, BudgetExceeded, BudgetLimits
from backend.rabbit_code.context_budget import ContextBlock, ContextCompressor, ContextTier
from backend.rabbit_code.permissions import PermissionMode
from backend.rabbit_code.run_control import IdempotencyLedger, OperationKind
from backend.rabbit_code.tool_registry import ToolEffect, ToolMetadata, ToolRegistry

from prompt_optimizer.providers.base import (
    ModelRequest,
    ProviderCapabilities,
    ProviderEvent,
    ProviderEventType,
)

# RC ID: RC-230. Keep Agent Core behavior checks deterministic and offline.


class FakeProvider:
    name = "fake"
    capabilities = ProviderCapabilities(streaming=True)

    def __init__(self, events: tuple[ProviderEvent, ...], on_delta: object = None) -> None:
        self.events = events
        self.calls = 0
        self.on_delta = on_delta

    def optimize(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        raise AssertionError("Agent Core stream must not call optimize")

    def stream(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        self.calls += 1
        for event in self.events:
            if event.type is ProviderEventType.DELTA and callable(self.on_delta):
                self.on_delta()
            yield event


def test_state_machine_covers_tool_loop_and_rejects_terminal_reentry() -> None:
    machine = AgentStateMachine("tool-loop")
    for state in (
        AgentState.CONTEXT,
        AgentState.MODEL,
        AgentState.TOOL_PENDING,
        AgentState.APPROVAL,
        AgentState.TOOL_RUNNING,
        AgentState.CONTINUING,
        AgentState.MODEL,
        AgentState.COMPLETED,
    ):
        machine.transition(state)

    assert machine.state is AgentState.COMPLETED
    with pytest.raises(ValueError, match="invalid Agent transition"):
        machine.transition(AgentState.MODEL)


def test_tool_loop_building_block_invokes_calls_in_order_and_audits_results() -> None:
    calls: list[str] = []
    registry = ToolRegistry()
    registry.register(
        ToolMetadata(
            name="read-file",
            description="Read a workspace file.",
            input_schema={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
            permission=PermissionMode.PLAN,
            effect=ToolEffect.READ,
            idempotent=True,
            cancellable=True,
            audit_action="read_file",
        ),
        lambda payload: calls.append(str(payload["path"])) or "content",
    )

    assert registry.invoke("read-file", {"path": "README.md"}) == "content"
    assert registry.invoke("read-file", {"path": "docs/plan.md"}) == "content"
    assert calls == ["README.md", "docs/plan.md"]
    assert [audit.outcome for audit in registry.audits] == ["succeeded", "succeeded"]


def test_agent_core_honors_preflight_cancellation_without_calling_provider() -> None:
    cancellation = Event()
    cancellation.set()
    provider = FakeProvider((ProviderEvent(ProviderEventType.COMPLETED),))

    events = list(
        AgentCore(provider).stream(
            ModelRequest(prompt="cancel"),
            cancellation=cancellation,
        )
    )

    assert [event.type for event in events] == [AgentEventType.STARTED, AgentEventType.CANCELLED]
    assert provider.calls == 0


def test_agent_core_stops_after_cancellation_between_provider_events() -> None:
    cancellation = Event()
    provider = FakeProvider(
        (
            ProviderEvent(ProviderEventType.STARTED),
            ProviderEvent(ProviderEventType.DELTA, text="first"),
            ProviderEvent(ProviderEventType.DELTA, text="second"),
            ProviderEvent(ProviderEventType.COMPLETED),
        ),
        on_delta=cancellation.set,
    )

    events = list(
        AgentCore(provider).stream(
            ModelRequest(prompt="cancel after first"),
            cancellation=cancellation,
        )
    )

    assert [event.type for event in events] == [
        AgentEventType.STARTED,
        AgentEventType.CANCELLED,
    ]


def test_idempotency_ledger_retries_failed_model_and_replays_success() -> None:
    ledger = IdempotencyLedger()
    attempts = 0

    def operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("transient")
        return "done"

    with pytest.raises(RuntimeError, match="transient"):
        ledger.execute("model-retry", OperationKind.MODEL, operation)
    assert ledger.execute("model-retry", OperationKind.MODEL, operation) == "done"
    assert ledger.execute("model-retry", OperationKind.MODEL, operation) == "done"
    assert attempts == 2
    assert [record.attempt for record in ledger.history if record.state == "failed"] == [1]
    assert [record.attempt for record in ledger.history if record.state == "succeeded"] == [2]


def test_budget_failure_is_atomic_and_agent_emits_terminal_failure() -> None:
    budget = BudgetController(BudgetLimits(max_output_tokens=1))
    budget.start_round(input_tokens=1)
    with pytest.raises(BudgetExceeded, match="output_tokens"):
        budget.record_output(output_tokens=2)
    assert budget.usage.output_tokens == 0
    budget.finish_round()

    provider = FakeProvider((ProviderEvent(ProviderEventType.COMPLETED),))
    events = list(
        AgentCore(provider, budget=BudgetController(BudgetLimits(max_rounds=0))).stream(
            ModelRequest(prompt="budget failure")
        )
    )
    assert events[-1].type is AgentEventType.FAILED
    assert provider.calls == 0


def test_context_compression_deduplicates_and_preserves_provenance() -> None:
    result = ContextCompressor(max_tokens=18).compress(
        [
            ContextBlock("instructions", "must follow rules", ContextTier.INSTRUCTION, True),
            ContextBlock("task", "complete the task", ContextTier.TASK, True),
            ContextBlock("source-a", "same source text " * 20, ContextTier.RELATED),
            ContextBlock("source-b", "same source text " * 20, ContextTier.RELATED),
        ]
    )

    assert result.deduplicated == 1
    assert result.estimated_tokens <= 18
    assert [block.source for block in result.blocks[:2]] == ["instructions", "task"]
    assert all(block.source for block in result.blocks)
    assert result.compressed


def test_json_checkpoint_recovery_replays_state_and_rejects_tampering(tmp_path: Path) -> None:
    store = JsonCheckpointStore(tmp_path)
    machine = AgentStateMachine("recoverable", store)
    machine.transition(AgentState.CONTEXT)
    machine.transition(AgentState.MODEL)
    machine.transition(AgentState.COMPLETED)

    recovered = store.load("recoverable")
    assert recovered is not None
    assert recovered.state is AgentState.COMPLETED
    assert len(recovered.events) == 3

    path = tmp_path / "recoverable.json"
    path.write_text(
        path.read_text(encoding="utf-8").replace('"state": "completed"', '"state": "failed"'),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="does not match"):
        store.load("recoverable")
