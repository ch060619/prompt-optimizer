from __future__ import annotations

import copy
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from threading import Lock
from typing import Any

from packages.protocol.rabbit_code_protocol import ApprovalRequest

from .approval import (
    ApprovalMismatch,
    ApprovalRequired,
    ApprovalStatus,
    PermissionApprovalEngine,
)
from .authorizations import AuthorizationStore
from .permissions import (
    CapabilityDomain,
    PermissionDecision,
    PermissionMode,
    PermissionPolicy,
)

# RC ID: RC-097. Validate tool metadata before startup or model exposure.


class ToolRegistryError(RuntimeError):
    pass


class DuplicateToolError(ToolRegistryError):
    pass


class ToolSchemaError(ToolRegistryError):
    pass


class ToolNotFound(ToolRegistryError, KeyError):
    pass


class ToolUnavailable(ToolRegistryError):
    pass


class ToolEffect(StrEnum):
    READ = "read"
    WRITE = "write"
    MIXED = "mixed"
    NETWORK = "network"
    PROCESS = "process"


ToolHandler = Callable[[Mapping[str, Any]], Any]


@dataclass(frozen=True)
class ToolMetadata:
    name: str
    description: str
    input_schema: Mapping[str, Any]
    permission: PermissionMode
    effect: ToolEffect
    idempotent: bool
    cancellable: bool
    audit_action: str


@dataclass(frozen=True)
class ToolDefinition:
    metadata: ToolMetadata
    handler: ToolHandler | None = None


@dataclass(frozen=True)
class ToolAudit:
    sequence: int
    tool_name: str
    action: str
    allowed: bool
    outcome: str
    reason: str


class ToolRegistry:
    def __init__(
        self,
        *,
        permission_policy: PermissionPolicy | None = None,
        approval_engine: PermissionApprovalEngine | None = None,
        authorization_store: AuthorizationStore | None = None,
    ) -> None:
        self._definitions: dict[str, ToolDefinition] = {}
        self._audits: list[ToolAudit] = []
        self._lock = Lock()
        self.permission_policy = permission_policy
        self.authorization_store = authorization_store
        self.approval_engine = approval_engine or (
            authorization_store.engine if authorization_store is not None else None
        )

    @property
    def audits(self) -> tuple[ToolAudit, ...]:
        with self._lock:
            return tuple(self._audits)

    def register(
        self,
        definition: ToolDefinition | ToolMetadata | Mapping[str, Any],
        handler: ToolHandler | None = None,
    ) -> ToolDefinition:
        normalized = _normalize_definition(definition, handler)
        _validate_metadata(normalized.metadata)
        with self._lock:
            if normalized.metadata.name in self._definitions:
                raise DuplicateToolError(f"tool is already registered: {normalized.metadata.name}")
            self._definitions[normalized.metadata.name] = normalized
        return normalized

    def startup(self) -> tuple[ToolDefinition, ...]:
        with self._lock:
            definitions = tuple(self._definitions.values())
        missing_handlers = [
            item.metadata.name for item in definitions if item.handler is None
        ]
        if missing_handlers:
            raise ToolUnavailable(
                f"tools without handlers cannot start: {', '.join(missing_handlers)}"
            )
        return definitions

    def get(self, name: str) -> ToolDefinition:
        with self._lock:
            try:
                return self._definitions[name]
            except KeyError as exc:
                raise ToolNotFound(name) from exc

    def model_tools(self) -> tuple[ToolMetadata, ...]:
        return tuple(item.metadata for item in self.startup())

    def catalog(self) -> tuple[dict[str, Any], ...]:
        return tuple(_metadata_payload(item.metadata) for item in self.startup())

    def validate_input(self, name: str, payload: Mapping[str, Any]) -> None:
        definition = self.get(name)
        if not isinstance(payload, Mapping):
            raise ToolSchemaError("tool input must be an object")
        _validate_input(definition.metadata.input_schema, payload)

    def invoke(
        self,
        name: str,
        payload: Mapping[str, Any],
        *,
        approval: bool = False,
        approval_id: str | None = None,
        approval_request: ApprovalRequest | None = None,
        session_id: str | None = None,
    ) -> Any:
        definition = self.get(name)
        if definition.handler is None:
            self._audit(
                name,
                definition.metadata.audit_action,
                False,
                "unavailable",
                "missing handler",
            )
            raise ToolUnavailable(f"tool is not executable: {name}")
        handler = definition.handler
        self.validate_input(name, payload)
        decision = self._authorize(definition.metadata, payload, approval=False)
        if not decision.allowed:
            if decision.requires_approval and self.approval_engine is not None:
                request = approval_request
                if request is None and approval_id is not None:
                    request = self.approval_engine.get(approval_id)
                if request is None:
                    request = self.request_approval(name, payload)
                    if (
                        self.authorization_store is None
                        or self.authorization_store.authorize(
                            request,
                            session_id=session_id,
                        )
                        is None
                    ):
                        self._audit(
                            name,
                            definition.metadata.audit_action,
                            False,
                            "approval_required",
                            "dangerous operation requires approval",
                        )
                        raise ApprovalRequired(request)
                self._assert_approval_matches(name, payload, request)
                if (
                    approval
                    and self.approval_engine.status(request.approval_id)
                    is ApprovalStatus.PENDING
                ):
                    self.approval_engine.approve(request.approval_id, request=request)
                try:
                    result = self.approval_engine.execute(
                        request.approval_id,
                        lambda: handler(payload),
                        request=request,
                    )
                except Exception as exc:
                    self._audit(name, definition.metadata.audit_action, False, "denied", str(exc))
                    raise
                self._audit(
                    name,
                    definition.metadata.audit_action,
                    True,
                    "succeeded",
                    "approved tool completed",
                )
                return result
            if approval:
                decision = self._authorize(definition.metadata, payload, approval=True)
            if not decision.allowed:
                self._audit(
                    name,
                    definition.metadata.audit_action,
                    False,
                    "denied",
                    decision.reason,
                )
                raise PermissionError(decision.reason)
        try:
            result = definition.handler(payload)
        except Exception as exc:
            self._audit(name, definition.metadata.audit_action, True, "failed", str(exc))
            raise
        self._audit(name, definition.metadata.audit_action, True, "succeeded", "tool completed")
        return result

    def request_approval(
        self,
        name: str,
        payload: Mapping[str, Any],
    ) -> ApprovalRequest:
        if self.approval_engine is None:
            raise PermissionError("no approval engine is configured")
        definition = self.get(name)
        if definition.handler is None:
            raise ToolUnavailable(f"tool is not executable: {name}")
        self.validate_input(name, payload)
        decision = self._authorize(definition.metadata, payload, approval=False)
        if not decision.requires_approval:
            raise PermissionError(decision.reason)
        return self.approval_engine.request(
            tool=name,
            command=_approval_command(definition.metadata.name, payload),
            paths=_approval_paths(payload),
            workdir=_approval_workdir(payload),
            impact=f"{definition.metadata.effect.value} operation for {name}",
            arguments=payload,
            description=definition.metadata.description,
            risk="high",
        )

    def _authorize(
        self,
        metadata: ToolMetadata,
        payload: Mapping[str, Any],
        *,
        approval: bool,
    ) -> Any:
        if self.permission_policy is None:
            return PermissionDecision(
                True,
                False,
                "no shared permission policy configured",
                metadata.permission,
            )
        if metadata.effect is ToolEffect.READ:
            domain, action = CapabilityDomain.FILES, "read"
        elif metadata.effect is ToolEffect.NETWORK:
            domain, action = CapabilityDomain.NETWORK, "connect"
        elif metadata.effect is ToolEffect.PROCESS:
            domain, action = CapabilityDomain.TERMINAL, "execute"
        else:
            domain, action = CapabilityDomain.FILES, "write"
        context: dict[str, Any] = {"dangerous": metadata.effect in {
            ToolEffect.NETWORK,
            ToolEffect.PROCESS,
        }}
        raw_path = payload.get("path")
        if isinstance(raw_path, str):
            candidate = Path(raw_path).expanduser()
            context["path"] = (
                candidate
                if candidate.is_absolute()
                else self.permission_policy.workspace_root / candidate
            )
        decision = self.permission_policy.authorize_capability(
            domain,
            action,
            context,
            approval=approval,
        )
        return decision

    @staticmethod
    def _assert_approval_matches(
        name: str,
        payload: Mapping[str, Any],
        request: ApprovalRequest,
    ) -> None:
        if request.tool != name or request.arguments != dict(payload):
            raise ApprovalMismatch("approval snapshot no longer matches the requested operation")

    def _audit(
        self,
        name: str,
        action: str,
        allowed: bool,
        outcome: str,
        reason: str,
    ) -> None:
        with self._lock:
            self._audits.append(
                ToolAudit(len(self._audits), name, action, allowed, outcome, reason)
            )


def _normalize_definition(
    definition: ToolDefinition | ToolMetadata | Mapping[str, Any],
    handler: ToolHandler | None,
) -> ToolDefinition:
    if isinstance(definition, ToolDefinition):
        if handler is not None:
            raise ToolRegistryError("handler must be supplied only once")
        return definition
    if isinstance(definition, ToolMetadata):
        return ToolDefinition(definition, handler)
    if not isinstance(definition, Mapping):
        raise ToolRegistryError("tool definition must be an object")
    required = (
        "name",
        "description",
        "input_schema",
        "permission",
        "effect",
        "idempotent",
        "cancellable",
        "audit_action",
    )
    missing = [key for key in required if key not in definition]
    if missing:
        raise ToolSchemaError(f"missing tool metadata: {', '.join(missing)}")
    try:
        metadata = ToolMetadata(
            name=str(definition["name"]),
            description=str(definition["description"]),
            input_schema=copy.deepcopy(definition["input_schema"]),
            permission=PermissionMode(definition["permission"]),
            effect=ToolEffect(definition["effect"]),
            idempotent=definition["idempotent"],
            cancellable=definition["cancellable"],
            audit_action=str(definition["audit_action"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ToolSchemaError(f"invalid tool metadata: {exc}") from exc
    return ToolDefinition(metadata, handler)


def _validate_metadata(metadata: ToolMetadata) -> None:
    if not re.fullmatch(r"[a-z][a-z0-9_.-]{1,63}", metadata.name):
        raise ToolSchemaError("tool name must be 2-64 lowercase identifier characters")
    if not metadata.description.strip():
        raise ToolSchemaError("tool description is required")
    if not isinstance(metadata.idempotent, bool) or not isinstance(metadata.cancellable, bool):
        raise ToolSchemaError("idempotent and cancellable must be booleans")
    if not re.fullmatch(r"[a-z][a-z0-9_.-]{1,63}", metadata.audit_action):
        raise ToolSchemaError("audit_action must be a lowercase identifier")
    _validate_schema(metadata.input_schema)
    if metadata.effect is ToolEffect.READ and metadata.permission is not PermissionMode.PLAN:
        raise ToolSchemaError("read-only tools must use Plan permission")
    if metadata.effect is not ToolEffect.READ and metadata.permission is PermissionMode.PLAN:
        raise ToolSchemaError("mutating tools cannot use Plan permission")


def _validate_schema(schema: Mapping[str, Any]) -> None:
    if not isinstance(schema, Mapping) or schema.get("type") != "object":
        raise ToolSchemaError("input_schema root type must be object")
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    if not isinstance(properties, Mapping):
        raise ToolSchemaError("input_schema properties must be an object")
    if not isinstance(required, list) or any(not isinstance(item, str) for item in required):
        raise ToolSchemaError("input_schema required must be a string list")
    if any(item not in properties for item in required):
        raise ToolSchemaError("input_schema required fields must be declared")
    if "additionalProperties" in schema and not isinstance(schema["additionalProperties"], bool):
        raise ToolSchemaError("input_schema additionalProperties must be boolean")
    for name, value in properties.items():
        if not isinstance(name, str) or not isinstance(value, Mapping):
            raise ToolSchemaError("input_schema property definitions must be objects")
        if value.get("type") not in {"string", "integer", "number", "boolean", "array", "object"}:
            raise ToolSchemaError(f"unsupported input_schema type for {name}")


def _validate_input(schema: Mapping[str, Any], payload: Mapping[str, Any]) -> None:
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    missing = [name for name in required if name not in payload]
    if missing:
        raise ToolSchemaError(f"missing required tool input: {', '.join(missing)}")
    if schema.get("additionalProperties", True) is False:
        unknown = [name for name in payload if name not in properties]
        if unknown:
            raise ToolSchemaError(f"unknown tool input: {', '.join(unknown)}")
    for name, value in payload.items():
        definition = properties.get(name)
        if not isinstance(definition, Mapping):
            continue
        expected = definition.get("type")
        if not _matches_type(value, expected):
            raise ToolSchemaError(f"invalid type for tool input: {name}")


def _matches_type(value: Any, expected: Any) -> bool:
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, Mapping)
    return False


def _metadata_payload(metadata: ToolMetadata) -> dict[str, Any]:
    return {
        "name": metadata.name,
        "description": metadata.description,
        "input_schema": copy.deepcopy(dict(metadata.input_schema)),
        "permission": metadata.permission.value,
        "effect": metadata.effect.value,
        "idempotent": metadata.idempotent,
        "cancellable": metadata.cancellable,
        "audit_action": metadata.audit_action,
    }


def _approval_command(name: str, payload: Mapping[str, Any]) -> tuple[str, ...]:
    raw_command = payload.get("command", payload.get("args"))
    if isinstance(raw_command, (list, tuple)) and raw_command:
        return tuple(str(item) for item in raw_command)
    return (name,)


def _approval_paths(payload: Mapping[str, Any]) -> tuple[str, ...]:
    paths: list[str] = []
    for key in ("path", "source", "destination"):
        value = payload.get(key)
        if isinstance(value, (str, Path)):
            paths.append(str(value))
    raw_paths = payload.get("paths")
    if isinstance(raw_paths, (list, tuple)):
        paths.extend(str(item) for item in raw_paths)
    return tuple(paths)


def _approval_workdir(payload: Mapping[str, Any]) -> str:
    for key in ("cwd", "workdir"):
        value = payload.get(key)
        if isinstance(value, (str, Path)) and value:
            return str(value)
    return "."
