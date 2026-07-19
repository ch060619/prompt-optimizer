from __future__ import annotations

import pytest
from backend.rabbit_code.approval import (
    ApprovalConsumed,
    ApprovalDenied,
    ApprovalExpired,
    ApprovalMismatch,
    ApprovalRequired,
    ApprovalStatus,
    PermissionApprovalEngine,
)
from backend.rabbit_code.permissions import CapabilityPolicy, PermissionMode
from backend.rabbit_code.tool_registry import ToolEffect, ToolMetadata, ToolRegistry

# RC ID: RC-202. Verify frozen approval snapshots and no side effects before approval.


def test_request_contains_complete_normalized_snapshot(tmp_path) -> None:
    engine = PermissionApprovalEngine(tmp_path)

    request = engine.request(
        tool="terminal.exec",
        command=("python", "-c", "print('ok')"),
        paths=("src/../README.md",),
        workdir=".",
        impact="starts a local process",
        arguments={"command": ["python", "-c", "print('ok')"], "cwd": "."},
    )

    assert request.tool == "terminal.exec"
    assert request.command == ["python", "-c", "print('ok')"]
    assert request.paths == [str((tmp_path / "README.md").resolve())]
    assert request.workdir == str(tmp_path.resolve())
    assert request.impact == "starts a local process"
    assert request.authorization_scope == "once"
    assert request.snapshot
    assert engine.status(request.approval_id) is ApprovalStatus.PENDING


def test_denial_and_timeout_never_call_executor(tmp_path) -> None:
    now = [0.0]
    engine = PermissionApprovalEngine(tmp_path, timeout_seconds=2, clock=lambda: now[0])
    calls: list[str] = []
    request = engine.request(
        tool="files.delete",
        command=("delete",),
        paths=("secret.txt",),
        impact="deletes one workspace file",
    )

    engine.deny(request.approval_id, request=request)
    with pytest.raises(ApprovalDenied):
        engine.execute(request.approval_id, lambda: calls.append("denied"), request=request)
    assert calls == []

    request = engine.request(
        tool="files.delete",
        command=("delete",),
        paths=("secret.txt",),
        impact="deletes one workspace file",
    )
    now[0] = 3.0
    with pytest.raises(ApprovalExpired):
        engine.approve(request.approval_id, request=request)
    assert calls == []


def test_approval_freezes_arguments_and_consumes_once(tmp_path) -> None:
    engine = PermissionApprovalEngine(tmp_path)
    calls: list[str] = []
    request = engine.request(
        tool="terminal.exec",
        command=("python", "-c", "print('one')"),
        paths=("output.txt",),
        impact="writes a generated file",
        arguments={"command": ["python", "-c", "print('one')"]},
    )
    engine.approve(request.approval_id, request=request)

    mutated = request.model_copy(
        update={"arguments": {"command": ["python", "-c", "print('two')"]}}
    )
    with pytest.raises(ApprovalMismatch):
        engine.execute(request.approval_id, lambda: calls.append("mutated"), request=mutated)
    assert calls == []

    assert (
        engine.execute(request.approval_id, lambda: calls.append("approved"), request=request)
        is None
    )
    assert calls == ["approved"]
    with pytest.raises(ApprovalConsumed):
        engine.execute(request.approval_id, lambda: calls.append("again"), request=request)
    assert calls == ["approved"]


def test_unapproved_execution_returns_the_shared_request(tmp_path) -> None:
    engine = PermissionApprovalEngine(tmp_path)
    request = engine.request(
        tool="network.request",
        command=("GET", "https://example.test"),
        impact="sends one request to an external service",
    )

    with pytest.raises(ApprovalRequired) as error:
        engine.execute(request.approval_id, lambda: None)
    assert error.value.request.model_dump() == request.model_dump()


def test_tool_registry_freezes_gui_or_tui_approval_before_handler(tmp_path) -> None:
    policy = CapabilityPolicy(tmp_path)
    policy.switch_mode(PermissionMode.HIGH, explicit_confirmation=True)
    engine = PermissionApprovalEngine(tmp_path)
    calls: list[dict[str, object]] = []
    registry = ToolRegistry(permission_policy=policy, approval_engine=engine)
    registry.register(
        ToolMetadata(
            name="network.request",
            description="Send one network request",
            input_schema={
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
                "additionalProperties": False,
            },
            permission=PermissionMode.HIGH,
            effect=ToolEffect.NETWORK,
            idempotent=True,
            cancellable=True,
            audit_action="network.request",
        ),
        lambda payload: calls.append(dict(payload)),
    )

    with pytest.raises(ApprovalRequired) as error:
        registry.invoke("network.request", {"url": "https://example.test/one"})
    request = error.value.request
    assert request.tool == "network.request"
    assert request.arguments == {"url": "https://example.test/one"}
    assert calls == []

    with pytest.raises(ApprovalRequired):
        registry.invoke(
            "network.request",
            {"url": "https://example.test/one"},
            approval_id=request.approval_id,
        )
    assert calls == []

    engine.approve(request.approval_id, request=request)
    assert registry.invoke(
        "network.request",
        {"url": "https://example.test/one"},
        approval_id=request.approval_id,
    ) is None
    assert calls == [{"url": "https://example.test/one"}]

    with pytest.raises(ApprovalMismatch):
        registry.invoke(
            "network.request",
            {"url": "https://example.test/two"},
            approval_id=request.approval_id,
        )
    assert calls == [{"url": "https://example.test/one"}]
