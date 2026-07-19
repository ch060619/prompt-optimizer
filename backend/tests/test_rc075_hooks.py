from __future__ import annotations

import json
from pathlib import Path
from time import sleep

from backend.rabbit_code.hooks import (
    HookFailureStrategy,
    HookManager,
    HookOutput,
    HookPhase,
    HookSpec,
)
from backend.rabbit_code.permissions import PermissionPolicy

# RC ID: RC-075. Verify ordered hooks, permission gates, failures, timeouts, and config loading.


def test_hooks_run_in_priority_order_and_merge_safe_feedback() -> None:
    calls: list[str] = []
    manager = HookManager(
        [
            HookSpec(
                "later",
                HookPhase.TOOL_BEFORE,
                lambda payload: (calls.append("later"), HookOutput(feedback="later"))[1],
                priority=20,
            ),
            HookSpec(
                "first",
                HookPhase.TOOL_BEFORE,
                lambda payload: (calls.append("first"), HookOutput(feedback="first"))[1],
                priority=10,
            ),
        ]
    )

    result = manager.dispatch(HookPhase.TOOL_BEFORE, {"tool": "search"})

    assert result.allowed
    assert calls == ["first", "later"]
    assert result.feedback == ("first", "later")
    assert [entry.name for entry in manager.audit] == ["first", "later"]


def test_hook_permission_is_checked_before_handler_runs(tmp_path: Path) -> None:
    called = False

    def handler(payload):  # type: ignore[no-untyped-def]
        nonlocal called
        called = True
        return HookOutput()

    policy = PermissionPolicy(tmp_path)
    manager = HookManager(
        [HookSpec("write-hook", HookPhase.PERMISSION_BEFORE, handler, required_action="write")],
        permission_policy=policy,
    )

    result = manager.dispatch(
        HookPhase.PERMISSION_BEFORE,
        {"path": tmp_path / "prompt.txt"},
    )

    assert not called
    assert not result.allowed
    assert "read-only" in result.feedback[0]
    assert manager.audit[0].status == "denied"


def test_hook_timeout_and_exception_follow_failure_strategy() -> None:
    def slow(payload):  # type: ignore[no-untyped-def]
        sleep(0.2)
        return HookOutput(feedback="too late")

    def broken(payload):  # type: ignore[no-untyped-def]
        raise RuntimeError("hook failed")

    manager = HookManager(
        [
            HookSpec(
                "slow",
                HookPhase.ERROR,
                slow,
                timeout_seconds=0.01,
                failure_strategy=HookFailureStrategy.DENY,
                priority=10,
            ),
            HookSpec(
                "broken",
                HookPhase.ERROR,
                broken,
                failure_strategy=HookFailureStrategy.CONTINUE,
                priority=20,
            ),
        ]
    )

    result = manager.dispatch(HookPhase.ERROR, {})

    assert not result.allowed
    assert any("timed out" in feedback for feedback in result.feedback)
    assert any("hook failed" in feedback for feedback in result.feedback)
    assert [entry.status for entry in manager.audit] == ["timeout", "error"]


def test_hook_output_schema_is_strictly_validated() -> None:
    manager = HookManager(
        [
            HookSpec(
                "invalid",
                HookPhase.SESSION_AFTER,
                lambda payload: "not a HookOutput",  # type: ignore[return-value]
                failure_strategy=HookFailureStrategy.DENY,
            )
        ]
    )

    result = manager.dispatch(HookPhase.SESSION_AFTER, {})

    assert not result.allowed
    assert "HookOutput" in result.feedback[0]
    assert manager.audit[0].status == "error"


def test_user_and_project_hook_config_merge_with_project_override(tmp_path: Path) -> None:
    user_path = tmp_path / "user.json"
    project_path = tmp_path / "project.json"
    user_path.write_text(
        json.dumps(
            {
                "hooks": [
                    {"name": "policy", "phase": "tool.after", "handler": "user"},
                ]
            }
        ),
        encoding="utf-8",
    )
    project_path.write_text(
        json.dumps(
            {
                "hooks": [
                    {"name": "policy", "phase": "tool.after", "handler": "project"},
                ]
            }
        ),
        encoding="utf-8",
    )
    manager = HookManager.from_config(
        user_path,
        project_path,
        {
            "user": lambda payload: HookOutput(feedback="user"),
            "project": lambda payload: HookOutput(feedback="project"),
        },
    )

    result = manager.dispatch(HookPhase.TOOL_AFTER, {})

    assert result.feedback == ("project",)
    assert [entry.name for entry in manager.audit] == ["policy"]
