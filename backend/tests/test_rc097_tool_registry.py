from __future__ import annotations

from pathlib import Path

import pytest
from backend.rabbit_code.permissions import PermissionMode, PermissionPolicy
from backend.rabbit_code.tool_registry import (
    DuplicateToolError,
    ToolEffect,
    ToolMetadata,
    ToolRegistry,
    ToolSchemaError,
    ToolUnavailable,
)

# RC ID: RC-097. Verify metadata, schema, startup, model exposure, and audit gates.


def _metadata(name: str = "read_file") -> ToolMetadata:
    return ToolMetadata(
        name=name,
        description="Read one workspace file",
        input_schema={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        },
        permission=PermissionMode.PLAN,
        effect=ToolEffect.READ,
        idempotent=True,
        cancellable=False,
        audit_action="read_file",
    )


def test_registry_validates_metadata_and_generates_model_catalog() -> None:
    registry = ToolRegistry()
    registry.register(_metadata(), lambda payload: payload["path"])

    definitions = registry.startup()
    catalog = registry.catalog()
    assert len(definitions) == 1
    assert catalog[0]["name"] == "read_file"
    assert catalog[0]["input_schema"]["required"] == ["path"]


def test_duplicate_missing_and_invalid_metadata_are_rejected() -> None:
    registry = ToolRegistry()
    registry.register(_metadata(), lambda payload: None)
    with pytest.raises(DuplicateToolError, match="already registered"):
        registry.register(_metadata(), lambda payload: None)
    with pytest.raises(ToolSchemaError, match="missing tool metadata"):
        registry.register({"name": "missing"})
    with pytest.raises(ToolSchemaError, match="root type"):
        registry.register(
            {
                "name": "bad_schema",
                "description": "Bad",
                "input_schema": {"type": "array"},
                "permission": "plan",
                "effect": "read",
                "idempotent": True,
                "cancellable": False,
                "audit_action": "bad_schema",
            }
        )


def test_missing_handler_cannot_start_or_enter_model_request() -> None:
    registry = ToolRegistry()
    registry.register(_metadata())
    with pytest.raises(ToolUnavailable, match="without handlers"):
        registry.startup()
    with pytest.raises(ToolUnavailable, match="not executable"):
        registry.invoke("read_file", {"path": "file.txt"})
    assert registry.audits[-1].outcome == "unavailable"


def test_input_schema_permission_and_audit_are_enforced(tmp_path: Path) -> None:
    policy = PermissionPolicy(tmp_path)
    registry = ToolRegistry(permission_policy=policy)
    registry.register(_metadata(), lambda payload: "ok")
    with pytest.raises(ToolSchemaError, match="missing required"):
        registry.invoke("read_file", {})
    assert registry.invoke("read_file", {"path": "file.txt"}) == "ok"
    assert registry.audits[-1].allowed
    assert registry.audits[-1].action == "read_file"


def test_write_tool_requires_edit_or_high_permission(tmp_path: Path) -> None:
    policy = PermissionPolicy(tmp_path)
    registry = ToolRegistry(permission_policy=policy)
    metadata = ToolMetadata(
        name="write_file",
        description="Write a workspace file",
        input_schema={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
            "additionalProperties": False,
        },
        permission=PermissionMode.EDIT,
        effect=ToolEffect.WRITE,
        idempotent=False,
        cancellable=True,
        audit_action="write_file",
    )
    registry.register(metadata, lambda payload: "written")
    with pytest.raises(PermissionError, match="Plan mode"):
        registry.invoke("write_file", {"path": "file.txt"})
    policy.switch_mode(PermissionMode.EDIT, explicit_confirmation=True)
    assert registry.invoke("write_file", {"path": "file.txt"}) == "written"
