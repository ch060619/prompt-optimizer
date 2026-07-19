from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

# RC ID: RC-070. Define shared Plan/Edit/high permission modes and task snapshots.


class PermissionMode(StrEnum):
    PLAN = "plan"
    EDIT = "edit"
    HIGH = "high"


class CapabilityDomain(StrEnum):
    FILES = "files"
    TERMINAL = "terminal"
    NETWORK = "network"
    GIT = "git"
    MCP = "mcp"
    DESKTOP = "desktop"


_CAPABILITY_MATRIX: dict[PermissionMode, dict[CapabilityDomain, tuple[str, ...]]] = {
    PermissionMode.PLAN: {
        CapabilityDomain.FILES: ("read", "list", "search"),
        CapabilityDomain.TERMINAL: (),
        CapabilityDomain.NETWORK: (),
        CapabilityDomain.GIT: ("read", "status", "diff"),
        CapabilityDomain.MCP: (),
        CapabilityDomain.DESKTOP: (),
    },
    PermissionMode.EDIT: {
        CapabilityDomain.FILES: (
            "read",
            "list",
            "search",
            "write",
            "create",
            "edit",
            "patch",
        ),
        CapabilityDomain.TERMINAL: (),
        CapabilityDomain.NETWORK: (),
        CapabilityDomain.GIT: ("read", "status", "diff", "write"),
        CapabilityDomain.MCP: (),
        CapabilityDomain.DESKTOP: (),
    },
    PermissionMode.HIGH: {
        CapabilityDomain.FILES: (
            "read",
            "list",
            "search",
            "write",
            "create",
            "edit",
            "patch",
            "delete",
        ),
        CapabilityDomain.TERMINAL: ("execute", "shell"),
        CapabilityDomain.NETWORK: ("connect", "request"),
        CapabilityDomain.GIT: ("read", "status", "diff", "write", "commit"),
        CapabilityDomain.MCP: ("read", "invoke", "write"),
        CapabilityDomain.DESKTOP: ("read", "notify", "control"),
    },
}


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    requires_approval: bool
    reason: str
    mode: PermissionMode


@dataclass(frozen=True)
class ModeChangeEvent:
    sequence: int
    from_mode: PermissionMode
    to_mode: PermissionMode
    actor: str


class PermissionPolicy:
    """Apply one shared capability policy to CLI, GUI, and background tasks."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.resolve()
        self._mode = PermissionMode.PLAN
        self._events: list[ModeChangeEvent] = []
        self._task_modes: dict[str, PermissionMode] = {}

    @property
    def mode(self) -> PermissionMode:
        return self._mode

    @property
    def events(self) -> tuple[ModeChangeEvent, ...]:
        return tuple(self._events)

    def switch_mode(
        self,
        mode: PermissionMode,
        *,
        actor: str = "user",
        explicit_confirmation: bool = False,
    ) -> ModeChangeEvent:
        if not explicit_confirmation:
            raise PermissionError("mode changes require an explicit user action")
        if mode is self._mode:
            raise ValueError(f"mode is already {mode.value}")
        event = ModeChangeEvent(
            sequence=len(self._events),
            from_mode=self._mode,
            to_mode=mode,
            actor=actor,
        )
        self._events.append(event)
        self._mode = mode
        return event

    def restore_mode(self, mode: PermissionMode) -> None:
        """Restore persisted state without presenting it as a user action."""
        self._mode = mode
        self._task_modes.clear()

    def bind_task(self, task_id: str) -> PermissionMode:
        if not task_id:
            raise ValueError("task_id is required")
        self._task_modes.setdefault(task_id, self._mode)
        return self._task_modes[task_id]

    def check(self, action: str, context: dict[str, Any]) -> bool:
        return self.authorize(action, context).allowed

    def capability_matrix(self) -> dict[str, dict[str, tuple[str, ...]]]:
        return {
            mode.value: {
                domain.value: actions
                for domain, actions in domains.items()
            }
            for mode, domains in _CAPABILITY_MATRIX.items()
        }

    def authorize_capability(
        self,
        domain: CapabilityDomain | str,
        action: str,
        context: Mapping[str, Any] | None = None,
        *,
        approval: bool = False,
        task_id: str | None = None,
    ) -> PermissionDecision:
        try:
            normalized_domain = CapabilityDomain(domain)
        except ValueError as exc:
            raise ValueError(f"unsupported capability domain: {domain}") from exc
        mode = self._task_modes.get(task_id, self._mode) if task_id else self._mode
        allowed_actions = _CAPABILITY_MATRIX[mode][normalized_domain]
        if action not in allowed_actions:
            reason = (
                "Plan mode is read-only"
                if mode is PermissionMode.PLAN
                else f"{normalized_domain.value} capability is not allowed in {mode.value} mode"
            )
            return PermissionDecision(
                False,
                False,
                reason,
                mode,
            )
        details = context or {}
        if normalized_domain is CapabilityDomain.FILES:
            mapped_action = action if action in {"read", "list", "search", "delete"} else "write"
            return self.authorize(
                mapped_action,
                details,
                approval=approval,
                task_id=task_id,
            )
        if mode is PermissionMode.HIGH and action not in {
            "read",
            "list",
            "search",
            "status",
            "diff",
        }:
            if not approval:
                return PermissionDecision(
                    False,
                    True,
                    "dangerous capability requires confirmation",
                    mode,
                )
        return PermissionDecision(True, False, "capability allowed", mode)

    def authorize(
        self,
        action: str,
        context: Mapping[str, Any] | None = None,
        *,
        approval: bool = False,
        task_id: str | None = None,
    ) -> PermissionDecision:
        details = context or {}
        mode = self._task_modes.get(task_id, self._mode) if task_id else self._mode
        normalized_action = action.lower()
        if normalized_action in {"read", "list", "search"}:
            return PermissionDecision(True, False, "read-only action allowed", mode)

        dangerous = bool(details.get("dangerous")) or normalized_action in {
            "delete",
            "shell",
            "network",
        }
        if mode is PermissionMode.PLAN:
            return PermissionDecision(False, False, "Plan mode is read-only", mode)

        path = self._context_path(details)
        in_workspace = path is not None and self._is_within_workspace(path)
        if normalized_action in {"write", "create", "edit"}:
            if mode is PermissionMode.EDIT and not in_workspace:
                return PermissionDecision(
                    False,
                    False,
                    "Edit mode is limited to the workspace",
                    mode,
                )
            if mode is PermissionMode.HIGH and not in_workspace:
                dangerous = True

        if dangerous:
            if mode is not PermissionMode.HIGH:
                return PermissionDecision(False, False, "dangerous action requires high mode", mode)
            if not approval:
                return PermissionDecision(
                    False,
                    True,
                    "dangerous action requires confirmation",
                    mode,
                )
        return PermissionDecision(True, False, "action allowed", mode)

    def _context_path(self, context: Mapping[str, Any]) -> Path | None:
        raw_path = context.get("path")
        if not isinstance(raw_path, (str, Path)):
            return None
        return Path(raw_path).expanduser().resolve()

    def _is_within_workspace(self, path: Path) -> bool:
        try:
            path.relative_to(self.workspace_root)
        except ValueError:
            return False
        return True


class CapabilityPolicy(PermissionPolicy):
    """Named policy surface for the six capability domains."""
