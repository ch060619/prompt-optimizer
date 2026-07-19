from __future__ import annotations

from threading import Event, Lock, Thread
from time import sleep

import pytest
from backend.rabbit_code.budget import BudgetLimits
from backend.rabbit_code.permissions import PermissionMode
from backend.rabbit_code.subagents import (
    SubAgentLimitError,
    SubAgentManager,
    SubAgentSpec,
    SubAgentState,
)

# RC ID: RC-074. Verify bounded child execution, copied context, and cascading cancellation.


def test_read_only_children_run_in_parallel_and_merge_in_input_order() -> None:
    active = 0
    peak = 0
    lock = Lock()

    def execute(task):  # type: ignore[no-untyped-def]
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        task.context["nested"]["value"] = 99  # type: ignore[index]
        sleep(0.05)
        with lock:
            active -= 1
        return f"{task.spec.task_id}:{task.context['nested']['value']}"

    manager = SubAgentManager(
        execute,
        parent_permission=PermissionMode.EDIT,
        max_concurrency=2,
    )
    context = {"nested": {"value": 1}}
    results = manager.run_many(
        [
            SubAgentSpec("child-a", "查找 A", context, permission=PermissionMode.PLAN),
            SubAgentSpec("child-b", "查找 B", context, permission=PermissionMode.PLAN),
        ]
    )

    assert [result.task_id for result in results] == ["child-a", "child-b"]
    assert [result.state for result in results] == [SubAgentState.COMPLETED] * 2
    assert [result.output for result in results] == ["child-a:99", "child-b:99"]
    assert manager.peak_concurrency == 2
    assert context == {"nested": {"value": 1}}
    assert manager.summarize(results).merged_output == "child-a:99\nchild-b:99"


def test_child_cannot_escalate_permission_or_depth() -> None:
    manager = SubAgentManager(lambda task: "ok", parent_permission=PermissionMode.EDIT)

    with pytest.raises(PermissionError, match="parent permission"):
        manager.run_many(
            [SubAgentSpec("high", "危险", {}, permission=PermissionMode.HIGH)]
        )
    with pytest.raises(SubAgentLimitError, match="depth"):
        manager.run_many([SubAgentSpec("nested", "递归", {}, depth=2)])


def test_child_budget_rejects_work_before_executor_runs() -> None:
    called = False

    def execute(task):  # type: ignore[no-untyped-def]
        nonlocal called
        called = True
        return "should not run"

    results = SubAgentManager(execute).run_many(
        [SubAgentSpec("over-budget", "超预算", {}, budget=BudgetLimits(max_rounds=0))]
    )

    assert not called
    assert results[0].state is SubAgentState.FAILED
    assert "rounds" in results[0].error


def test_parent_cancel_cascades_to_running_children() -> None:
    started = Event()

    def execute(task):  # type: ignore[no-untyped-def]
        started.set()
        while not task.cancellation.is_set():
            sleep(0.01)
        return "late result"

    manager = SubAgentManager(execute, max_concurrency=2)
    holder: list[tuple[object, ...]] = []
    worker = Thread(
        target=lambda: holder.append(
            manager.run_many(
                [
                    SubAgentSpec("child-a", "任务 A", {}),
                    SubAgentSpec("child-b", "任务 B", {}),
                ]
            )
        ),
        daemon=True,
    )
    worker.start()
    assert started.wait(timeout=2)
    manager.cancel()
    worker.join(timeout=2)

    assert holder
    assert [result.state for result in holder[0]] == [
        SubAgentState.CANCELLED,
        SubAgentState.CANCELLED,
    ]
    assert all(result.output is None for result in holder[0])
