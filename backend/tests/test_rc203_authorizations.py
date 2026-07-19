from __future__ import annotations

import pytest
from backend.rabbit_code.approval import (
    ApprovalDenied,
    ApprovalRequired,
    PermissionApprovalEngine,
)
from backend.rabbit_code.authorizations import (
    AuthorizationRule,
    AuthorizationScope,
    AuthorizationStore,
    CommandMatch,
    PathMatch,
)
from backend.rabbit_code.permissions import CapabilityPolicy, PermissionMode
from backend.rabbit_code.tool_registry import ToolEffect, ToolMetadata, ToolRegistry

# RC ID: RC-203. Verify scoped grants, structured matching, edit, deny, and revoke.


def _request(
    engine: PermissionApprovalEngine,
    tmp_path,
    *,
    command=("python", "-c", "print(1)"),
    path="out.txt",
):
    return engine.request(
        tool="terminal.exec",
        command=command,
        paths=(path,),
        workdir=".",
        impact="starts one local process",
        arguments={"command": list(command), "path": path},
    )


def test_once_approval_does_not_create_a_reusable_grant(tmp_path) -> None:
    engine = PermissionApprovalEngine(tmp_path)
    store = AuthorizationStore(engine)
    request = _request(engine, tmp_path)

    grant = store.approve_once(request)

    assert grant.scope is AuthorizationScope.ONCE
    assert store.authorize(_request(engine, tmp_path)) is None
    assert store.grants[0].revoked is False


def test_session_grant_is_scoped_and_revoke_takes_effect_immediately(tmp_path) -> None:
    engine = PermissionApprovalEngine(tmp_path)
    store = AuthorizationStore(engine)
    first = _request(engine, tmp_path)
    grant = store.approve_session(first, session_id="session-a")

    same_session = _request(engine, tmp_path)
    other_session = _request(engine, tmp_path)
    assert store.authorize(same_session, session_id="session-a") == grant
    assert store.authorize(other_session, session_id="session-b") is None

    store.revoke(grant.grant_id)
    revoked_request = _request(engine, tmp_path)
    assert store.authorize(revoked_request, session_id="session-a") is None


def test_rule_uses_structured_exact_or_prefix_matching_without_shell_globs(tmp_path) -> None:
    engine = PermissionApprovalEngine(tmp_path)
    store = AuthorizationStore(engine)
    first = _request(engine, tmp_path, command=("python", "-m", "pytest"), path="src/test.py")
    rule = AuthorizationRule(
        rule_id="src-tests",
        tool=first.tool,
        command=tuple(first.command),
        paths=(str((tmp_path / "src").resolve()),),
        workdir=first.workdir,
        command_match=CommandMatch.PREFIX,
        path_match=PathMatch.WITHIN,
    )
    grant = store.approve_rule(first, rule)

    matching = _request(
        engine,
        tmp_path,
        command=("python", "-m", "pytest", "src/test.py"),
        path="src/other.py",
    )
    non_matching_tool = matching.model_copy(update={"tool": "shell.exec"})
    assert store.authorize(matching) == grant
    assert store.authorize(non_matching_tool) is None


def test_deny_has_no_executor_and_edit_creates_a_new_pending_snapshot(tmp_path) -> None:
    engine = PermissionApprovalEngine(tmp_path)
    store = AuthorizationStore(engine)
    denied = _request(engine, tmp_path)
    calls: list[str] = []
    store.deny(denied)
    with pytest.raises(ApprovalDenied):
        engine.execute(denied.approval_id, lambda: calls.append("denied"), request=denied)
    assert calls == []

    original = _request(engine, tmp_path)
    edited = store.edit_request(
        original,
        command=("python", "-c", "print(2)"),
        arguments={"command": ["python", "-c", "print(2)"], "path": "out.txt"},
    )
    assert edited.approval_id != original.approval_id
    assert edited.request_id == original.request_id
    assert edited.command[-1] == "print(2)"
    with pytest.raises(ApprovalRequired):
        engine.execute(edited.approval_id, lambda: calls.append("edited"), request=edited)
    assert calls == []


def test_registry_reuses_only_a_matching_session_grant(tmp_path) -> None:
    policy = CapabilityPolicy(tmp_path)
    policy.switch_mode(PermissionMode.HIGH, explicit_confirmation=True)
    engine = PermissionApprovalEngine(tmp_path)
    store = AuthorizationStore(engine)
    calls: list[dict[str, object]] = []
    registry = ToolRegistry(
        permission_policy=policy,
        authorization_store=store,
    )
    registry.register(
        ToolMetadata(
            name="terminal.exec",
            description="Run a bounded command",
            input_schema={
                "type": "object",
                "properties": {
                    "command": {"type": "array"},
                    "cwd": {"type": "string"},
                },
                "required": ["command"],
                "additionalProperties": False,
            },
            permission=PermissionMode.HIGH,
            effect=ToolEffect.PROCESS,
            idempotent=False,
            cancellable=True,
            audit_action="terminal.exec",
        ),
        lambda payload: calls.append(dict(payload)),
    )
    payload = {"command": ["python", "-c", "print(1)"], "cwd": "."}
    with pytest.raises(ApprovalRequired) as error:
        registry.invoke("terminal.exec", payload, session_id="session-a")
    first = error.value.request
    store.approve_session(first, session_id="session-a")

    assert registry.invoke("terminal.exec", payload, session_id="session-a") is None
    assert calls == [payload]
    with pytest.raises(ApprovalRequired):
        registry.invoke(
            "terminal.exec",
            {"command": ["python", "-c", "print(2)"], "cwd": "."},
            session_id="session-a",
        )
    assert calls == [payload]
