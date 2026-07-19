from __future__ import annotations

from pathlib import Path

import pytest
from backend.rabbit_code.agent import AgentCore, AgentEventType
from backend.rabbit_code.budget import BudgetController, BudgetExceeded, BudgetLimits

from prompt_optimizer.providers.base import (
    ModelRequest,
    ProviderCapabilities,
    ProviderEvent,
    ProviderEventType,
)

# RC ID: RC-072. Verify atomic budgets, warnings, wall time, concurrency, and Agent termination.


class FakeProvider:
    name = "fake"
    capabilities = ProviderCapabilities(streaming=True)

    def optimize(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        raise AssertionError("budget stream should not call optimize")

    def stream(self, request: ModelRequest):  # type: ignore[no-untyped-def]
        yield ProviderEvent(ProviderEventType.DELTA, text="输出")
        yield ProviderEvent(ProviderEventType.COMPLETED)


def test_round_budget_warns_near_limit_and_overflow_is_atomic() -> None:
    budget = BudgetController(BudgetLimits(max_rounds=2, max_input_tokens=10, warning_ratio=0.8))

    assert budget.start_round(input_tokens=2) == ()
    notices = budget.start_round(input_tokens=2)
    before = budget.usage

    with pytest.raises(BudgetExceeded, match="rounds"):
        budget.start_round(input_tokens=2)

    assert any(notice.dimension == "rounds" for notice in notices)
    assert budget.usage == before
    budget.finish_round()
    budget.finish_round()


def test_output_cost_context_and_concurrency_limits_are_enforced() -> None:
    budget = BudgetController(
        BudgetLimits(max_output_tokens=2, max_cost=1.0, max_context_tokens=4, max_concurrency=1)
    )
    budget.start_round(input_tokens=1, context_tokens=4)

    with pytest.raises(BudgetExceeded, match="concurrency"):
        budget.start_round(input_tokens=1, context_tokens=1)
    with pytest.raises(BudgetExceeded, match="output_tokens"):
        budget.record_output(output_tokens=3)
    with pytest.raises(BudgetExceeded, match="cost"):
        budget.record_output(output_tokens=1, cost=1.1)

    assert budget.usage.output_tokens == 0
    assert budget.usage.cost == 0
    budget.finish_round()


def test_wall_clock_limit_is_checked(monkeypatch: pytest.MonkeyPatch) -> None:
    budget = BudgetController(BudgetLimits(max_wall_clock_seconds=1.0))
    monkeypatch.setattr("backend.rabbit_code.budget.time.monotonic", lambda: budget._started_at + 2)

    with pytest.raises(BudgetExceeded, match="wall_clock_seconds"):
        budget.check_wall_clock()


def test_agent_emits_warning_and_budget_failure_event(tmp_path: Path) -> None:
    warning_budget = BudgetController(BudgetLimits(max_rounds=1, warning_ratio=0.5))
    warning_events = list(
        AgentCore(FakeProvider(), budget=warning_budget).stream(ModelRequest(prompt="预算警告"))
    )
    assert any(event.type is AgentEventType.WARNING for event in warning_events)
    assert warning_events[-1].type is AgentEventType.COMPLETED
    assert warning_budget.usage.active_concurrency == 0

    failing_budget = BudgetController(BudgetLimits(max_rounds=0))
    failing_events = list(
        AgentCore(FakeProvider(), budget=failing_budget).stream(
            ModelRequest(prompt="预算终止"),
            request_id=str(tmp_path),
        )
    )
    assert failing_events[-1].type is AgentEventType.FAILED
    assert "rounds" in str(failing_events[-1].payload)
