from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import uuid4

# RC ID: RC-085. Keep temporary, session, project, and user memory isolated.


class MemoryScope(StrEnum):
    TEMPORARY = "temporary"
    SESSION = "session"
    PROJECT = "project"
    USER = "user"


class MemoryScopeDisabled(PermissionError):
    """Raised when an operation targets a disabled memory scope."""


@dataclass(frozen=True)
class MemoryEntry:
    id: str
    scope: MemoryScope
    scope_id: str
    content: str
    source: str
    purpose: str


class MemoryStore:
    """An in-process memory boundary with one table per memory scope."""

    def __init__(self) -> None:
        self._tables: dict[MemoryScope, dict[str, dict[str, MemoryEntry]]] = {
            scope: {} for scope in MemoryScope
        }
        self._enabled: dict[tuple[MemoryScope, str], bool] = {}

    def write(
        self,
        scope: MemoryScope,
        scope_id: str,
        content: str,
        *,
        source: str,
        purpose: str,
        confirmed: bool = False,
    ) -> MemoryEntry:
        scope, scope_id = self._target(scope, scope_id)
        self._require_enabled(scope, scope_id)
        self._require_write_confirmation(source, purpose, confirmed)
        entry = MemoryEntry(
            id=uuid4().hex,
            scope=scope,
            scope_id=scope_id,
            content=self._require_text(content, "content"),
            source=self._require_text(source, "source"),
            purpose=self._require_text(purpose, "purpose"),
        )
        self._tables[scope].setdefault(scope_id, {})[entry.id] = entry
        return entry

    def list(self, scope: MemoryScope, scope_id: str) -> tuple[MemoryEntry, ...]:
        scope, scope_id = self._target(scope, scope_id)
        self._require_enabled(scope, scope_id)
        return tuple(self._tables[scope].get(scope_id, {}).values())

    def get(self, scope: MemoryScope, scope_id: str, entry_id: str) -> MemoryEntry:
        scope, scope_id = self._target(scope, scope_id)
        self._require_enabled(scope, scope_id)
        try:
            return self._tables[scope][scope_id][entry_id]
        except KeyError as exc:
            raise KeyError(f"memory entry not found: {entry_id}") from exc

    def edit(
        self,
        scope: MemoryScope,
        scope_id: str,
        entry_id: str,
        content: str,
        *,
        source: str,
        purpose: str,
        confirmed: bool = False,
    ) -> MemoryEntry:
        scope, scope_id = self._target(scope, scope_id)
        self._require_enabled(scope, scope_id)
        self._require_write_confirmation(source, purpose, confirmed)
        current = self.get(scope, scope_id, entry_id)
        updated = MemoryEntry(
            id=current.id,
            scope=current.scope,
            scope_id=current.scope_id,
            content=self._require_text(content, "content"),
            source=self._require_text(source, "source"),
            purpose=self._require_text(purpose, "purpose"),
        )
        self._tables[scope][scope_id][entry_id] = updated
        return updated

    def delete(self, scope: MemoryScope, scope_id: str, entry_id: str) -> None:
        scope, scope_id = self._target(scope, scope_id)
        self._require_enabled(scope, scope_id)
        try:
            del self._tables[scope][scope_id][entry_id]
        except KeyError as exc:
            raise KeyError(f"memory entry not found: {entry_id}") from exc

    def clear(self, scope: MemoryScope, scope_id: str) -> None:
        scope, scope_id = self._target(scope, scope_id)
        self._require_enabled(scope, scope_id)
        self._tables[scope].pop(scope_id, None)

    def clear_all(self) -> None:
        for table in self._tables.values():
            table.clear()

    def set_enabled(self, scope: MemoryScope, scope_id: str, enabled: bool) -> None:
        scope, scope_id = self._target(scope, scope_id)
        self._enabled[(scope, scope_id)] = enabled

    def is_enabled(self, scope: MemoryScope, scope_id: str) -> bool:
        scope, scope_id = self._target(scope, scope_id)
        return self._enabled.get((scope, scope_id), True)

    def _target(self, scope: MemoryScope, scope_id: str) -> tuple[MemoryScope, str]:
        try:
            normalized_scope = MemoryScope(scope)
        except ValueError as exc:
            raise ValueError(f"unknown memory scope: {scope}") from exc
        return normalized_scope, self._require_text(scope_id, "scope_id")

    def _require_enabled(self, scope: MemoryScope, scope_id: str) -> None:
        if not self._enabled.get((scope, scope_id), True):
            raise MemoryScopeDisabled(f"memory scope is disabled: {scope.value}/{scope_id}")

    @staticmethod
    def _require_write_confirmation(source: str, purpose: str, confirmed: bool) -> None:
        if not confirmed:
            raise PermissionError("memory writes require confirmation of source and purpose")
        MemoryStore._require_text(source, "source")
        MemoryStore._require_text(purpose, "purpose")

    @staticmethod
    def _require_text(value: str, name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be non-empty")
        return value
