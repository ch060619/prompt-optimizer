from __future__ import annotations

from pathlib import Path

import pytest
from backend.rabbit_code.permissions import PermissionMode, PermissionPolicy

from prompt_optimizer.contracts import Permission

# RC ID: RC-070. Verify Plan/Edit/high matrices, confirmation, path bounds, and task snapshots.


def test_plan_mode_is_read_only_and_policy_implements_permission_port(tmp_path: Path) -> None:
    policy = PermissionPolicy(tmp_path)

    assert isinstance(policy, Permission)
    assert policy.check("read", {"path": tmp_path / "prompt.txt"})
    decision = policy.authorize("write", {"path": tmp_path / "prompt.txt"})

    assert not decision.allowed
    assert decision.reason == "Plan mode is read-only"


def test_edit_mode_allows_workspace_write_but_rejects_escape(tmp_path: Path) -> None:
    policy = PermissionPolicy(tmp_path)
    policy.switch_mode(PermissionMode.EDIT, explicit_confirmation=True)

    inside = policy.authorize("write", {"path": tmp_path / "notes.txt"})
    outside = policy.authorize("write", {"path": tmp_path.parent / "outside.txt"})

    assert inside.allowed
    assert not outside.allowed
    assert "workspace" in outside.reason


def test_high_mode_requires_confirmation_for_dangerous_actions(tmp_path: Path) -> None:
    policy = PermissionPolicy(tmp_path)
    event = policy.switch_mode(
        PermissionMode.HIGH,
        actor="cli",
        explicit_confirmation=True,
    )

    pending = policy.authorize("shell", {"dangerous": True})
    approved = policy.authorize("shell", {"dangerous": True}, approval=True)

    assert event.from_mode is PermissionMode.PLAN
    assert event.to_mode is PermissionMode.HIGH
    assert not pending.allowed
    assert pending.requires_approval
    assert approved.allowed


def test_mode_switch_requires_explicit_confirmation_and_records_events(tmp_path: Path) -> None:
    policy = PermissionPolicy(tmp_path)

    with pytest.raises(PermissionError, match="explicit user action"):
        policy.switch_mode(PermissionMode.EDIT)

    policy.switch_mode(PermissionMode.EDIT, actor="gui", explicit_confirmation=True)
    policy.switch_mode(PermissionMode.PLAN, actor="gui", explicit_confirmation=True)

    assert [(event.sequence, event.from_mode, event.to_mode) for event in policy.events] == [
        (0, PermissionMode.PLAN, PermissionMode.EDIT),
        (1, PermissionMode.EDIT, PermissionMode.PLAN),
    ]


def test_existing_task_keeps_its_original_mode_after_switch(tmp_path: Path) -> None:
    policy = PermissionPolicy(tmp_path)
    task_mode = policy.bind_task("task-1")
    policy.switch_mode(PermissionMode.HIGH, explicit_confirmation=True)

    old_task = policy.authorize(
        "write",
        {"path": tmp_path.parent / "outside.txt"},
        task_id="task-1",
    )
    new_session = policy.authorize("write", {"path": tmp_path.parent / "outside.txt"})

    assert task_mode is PermissionMode.PLAN
    assert not old_task.allowed
    assert old_task.mode is PermissionMode.PLAN
    assert not new_session.allowed
    assert new_session.requires_approval
