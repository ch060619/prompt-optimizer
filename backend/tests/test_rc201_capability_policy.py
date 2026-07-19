from __future__ import annotations

import pytest
from backend.rabbit_code.permissions import (
    CapabilityDomain,
    CapabilityPolicy,
    PermissionMode,
)
from backend.rabbit_code.tool_registry import ToolEffect, ToolMetadata, ToolRegistry

# RC ID: RC-201. Verify the six-domain Plan/Edit/High capability matrix.


def test_matrix_has_minimum_defaults_for_all_capability_domains(tmp_path) -> None:
    policy = CapabilityPolicy(tmp_path)
    matrix = policy.capability_matrix()

    assert set(matrix[PermissionMode.PLAN]) == {domain.value for domain in CapabilityDomain}
    assert "read" in matrix[PermissionMode.PLAN][CapabilityDomain.FILES.value]
    assert matrix[PermissionMode.PLAN][CapabilityDomain.TERMINAL.value] == ()
    assert matrix[PermissionMode.PLAN][CapabilityDomain.NETWORK.value] == ()
    assert "diff" in matrix[PermissionMode.PLAN][CapabilityDomain.GIT.value]
    assert matrix[PermissionMode.PLAN][CapabilityDomain.MCP.value] == ()
    assert matrix[PermissionMode.PLAN][CapabilityDomain.DESKTOP.value] == ()


@pytest.mark.parametrize(
    ("domain", "action"),
    [
        (CapabilityDomain.FILES, "write"),
        (CapabilityDomain.TERMINAL, "execute"),
        (CapabilityDomain.NETWORK, "connect"),
        (CapabilityDomain.GIT, "commit"),
        (CapabilityDomain.MCP, "invoke"),
        (CapabilityDomain.DESKTOP, "control"),
    ],
)
def test_plan_denies_non_read_capabilities(tmp_path, domain, action) -> None:
    policy = CapabilityPolicy(tmp_path)

    decision = policy.authorize_capability(domain, action)

    assert decision.allowed is False
    assert decision.requires_approval is False
    assert decision.mode is PermissionMode.PLAN


def test_edit_allows_workspace_files_but_high_requires_approval_for_external_domains(
    tmp_path,
) -> None:
    policy = CapabilityPolicy(tmp_path)
    policy.switch_mode(PermissionMode.EDIT, explicit_confirmation=True)

    file_decision = policy.authorize_capability(
        CapabilityDomain.FILES,
        "write",
        context={"path": tmp_path / "notes.txt"},
    )
    terminal_decision = policy.authorize_capability(CapabilityDomain.TERMINAL, "execute")

    assert file_decision.allowed is True
    assert terminal_decision.allowed is False

    policy.switch_mode(PermissionMode.HIGH, explicit_confirmation=True)
    pending = policy.authorize_capability(CapabilityDomain.NETWORK, "connect")
    approved = policy.authorize_capability(
        CapabilityDomain.NETWORK,
        "connect",
        approval=True,
    )
    assert pending.requires_approval is True
    assert pending.allowed is False
    assert approved.allowed is True


def test_tool_registry_maps_network_effect_to_capability_approval(tmp_path) -> None:
    policy = CapabilityPolicy(tmp_path)
    policy.switch_mode(PermissionMode.HIGH, explicit_confirmation=True)
    registry = ToolRegistry(permission_policy=policy)
    registry.register(
        ToolMetadata(
            name="net.fetch",
            description="Fetch a remote resource",
            input_schema={"type": "object", "properties": {}},
            permission=PermissionMode.HIGH,
            effect=ToolEffect.NETWORK,
            idempotent=True,
            cancellable=True,
            audit_action="net.fetch",
        ),
        lambda _payload: "ok",
    )

    with pytest.raises(PermissionError, match="confirmation"):
        registry.invoke("net.fetch", {})
    assert registry.invoke("net.fetch", {}, approval=True) == "ok"
