from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from threading import Lock
from typing import Any, Protocol

# RC ID: RC-099. Gate browser, database, external-service, plugin, and MCP extensions per session.


class ExtensionError(RuntimeError):
    pass


class ExtensionNotFound(ExtensionError):
    pass


class ExtensionPermissionDenied(ExtensionError, PermissionError):
    pass


class ExtensionStateError(ExtensionError):
    pass


class ExtensionKind(StrEnum):
    BROWSER = "browser"
    DATABASE = "database"
    EXTERNAL_SERVICE = "external_service"
    PLUGIN = "plugin"
    MCP = "mcp"


class ExtensionPermission(StrEnum):
    NETWORK = "network"
    WORKSPACE_WRITE = "workspace_write"


class ExtensionAdapter(Protocol):
    def invoke(self, action: str, payload: Mapping[str, Any]) -> Any:
        pass


ExtensionHandler = Callable[[str, Mapping[str, Any]], Any]


@dataclass(frozen=True)
class ExtensionSpec:
    name: str
    kind: ExtensionKind
    description: str
    permissions: frozenset[ExtensionPermission]

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9_.-]{1,63}", self.name):
            raise ValueError("extension name must be a lowercase identifier")
        if not self.description.strip():
            raise ValueError("extension description is required")


@dataclass(frozen=True)
class ExtensionRecord:
    spec: ExtensionSpec
    installed: bool = True


@dataclass(frozen=True)
class ExtensionAudit:
    sequence: int
    session_id: str
    extension_name: str
    action: str
    allowed: bool
    reason: str


class CallableExtensionAdapter:
    def __init__(self, handler: ExtensionHandler) -> None:
        self.handler = handler

    def invoke(self, action: str, payload: Mapping[str, Any]) -> Any:
        return self.handler(action, payload)


class ExtensionManager:
    def __init__(self) -> None:
        self._records: dict[str, ExtensionRecord] = {}
        self._adapters: dict[str, ExtensionAdapter] = {}
        self._grants: dict[str, dict[str, frozenset[ExtensionPermission]]] = {}
        self._audit: list[ExtensionAudit] = []
        self._lock = Lock()

    @property
    def audit(self) -> tuple[ExtensionAudit, ...]:
        with self._lock:
            return tuple(self._audit)

    def install(self, spec: ExtensionSpec, adapter: ExtensionAdapter) -> ExtensionRecord:
        if spec.name in self._records:
            raise ExtensionStateError(f"extension is already installed: {spec.name}")
        self._records[spec.name] = ExtensionRecord(spec)
        self._adapters[spec.name] = adapter
        return self._records[spec.name]

    def uninstall(self, name: str) -> None:
        self._record(name)
        del self._records[name]
        self._adapters.pop(name, None)
        for grants in self._grants.values():
            grants.pop(name, None)

    def list_extensions(self) -> tuple[ExtensionRecord, ...]:
        return tuple(self._records[name] for name in sorted(self._records))

    def approve(
        self,
        session_id: str,
        name: str,
        permissions: Iterable[ExtensionPermission],
        *,
        explicit_confirmation: bool = False,
    ) -> frozenset[ExtensionPermission]:
        if not explicit_confirmation:
            raise ExtensionPermissionDenied("extension approval requires explicit confirmation")
        record = self._record(name)
        if not session_id:
            raise ValueError("session_id is required")
        requested = frozenset(ExtensionPermission(item) for item in permissions)
        if not requested <= record.spec.permissions:
            undeclared = requested - record.spec.permissions
            raise ExtensionPermissionDenied(
                "extension did not declare permissions: "
                f"{', '.join(sorted(item.value for item in undeclared))}"
            )
        with self._lock:
            self._grants.setdefault(session_id, {})[name] = requested
            self._append_audit(session_id, name, "approve", True, "session approval granted")
        return requested

    def revoke(self, session_id: str, name: str) -> None:
        self._record(name)
        with self._lock:
            self._grants.setdefault(session_id, {}).pop(name, None)
            self._append_audit(session_id, name, "revoke", True, "session approval revoked")

    def invoke(
        self,
        session_id: str,
        name: str,
        action: str,
        payload: Mapping[str, Any],
        *,
        required_permissions: Iterable[ExtensionPermission] = (),
    ) -> Any:
        record = self._record(name)
        requested = frozenset(ExtensionPermission(item) for item in required_permissions)
        with self._lock:
            session_grants = self._grants.get(session_id, {})
            approved = name in session_grants
            granted = session_grants.get(name, frozenset())
        if not approved:
            reason = "extension is disabled for this session"
            self._audit_denied(session_id, name, action, reason)
            raise ExtensionPermissionDenied(reason)
        if not requested <= granted:
            missing = requested - granted
            reason = "missing session permission: " + ", ".join(
                sorted(item.value for item in missing)
            )
            self._audit_denied(session_id, name, action, reason)
            raise ExtensionPermissionDenied(reason)
        if not requested <= record.spec.permissions:
            reason = "requested extension permission was not declared"
            self._audit_denied(session_id, name, action, reason)
            raise ExtensionPermissionDenied(reason)
        adapter = self._adapters.get(name)
        if adapter is None:
            raise ExtensionStateError(f"extension adapter is missing: {name}")
        try:
            result = adapter.invoke(action, payload)
        except Exception as exc:
            with self._lock:
                self._append_audit(session_id, name, action, True, f"failed: {exc}")
            raise
        with self._lock:
            self._append_audit(session_id, name, action, True, "extension completed")
        return result

    def _record(self, name: str) -> ExtensionRecord:
        try:
            return self._records[name]
        except KeyError as exc:
            raise ExtensionNotFound(f"extension is not installed: {name}") from exc

    def _audit_denied(self, session_id: str, name: str, action: str, reason: str) -> None:
        with self._lock:
            self._append_audit(session_id, name, action, False, reason)

    def _append_audit(
        self,
        session_id: str,
        name: str,
        action: str,
        allowed: bool,
        reason: str,
    ) -> None:
        self._audit.append(
            ExtensionAudit(len(self._audit), session_id, name, action, allowed, reason)
        )
