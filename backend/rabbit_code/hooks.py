from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .permissions import PermissionPolicy

# RC ID: RC-075. Run ordered, permission-gated hooks with bounded failure handling.


class HookPhase(StrEnum):
    SESSION_BEFORE = "session.before"
    SESSION_AFTER = "session.after"
    TOOL_BEFORE = "tool.before"
    TOOL_AFTER = "tool.after"
    PERMISSION_BEFORE = "permission.before"
    PERMISSION_AFTER = "permission.after"
    ERROR = "error"


class HookFailureStrategy(StrEnum):
    CONTINUE = "continue"
    DENY = "deny"
    STOP = "stop"


HookHandler = Callable[[Mapping[str, Any]], "HookOutput"]


@dataclass(frozen=True)
class HookOutput:
    allow: bool = True
    feedback: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.feedback is not None and not isinstance(self.feedback, str):
            raise TypeError("hook feedback must be text")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class HookSpec:
    name: str
    phase: HookPhase
    handler: HookHandler
    priority: int = 100
    timeout_seconds: float = 1.0
    failure_strategy: HookFailureStrategy = HookFailureStrategy.CONTINUE
    required_action: str | None = None
    enabled: bool = True

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("hook name is required")
        if self.priority < 0:
            raise ValueError("hook priority must be non-negative")
        if self.timeout_seconds <= 0:
            raise ValueError("hook timeout must be positive")


@dataclass(frozen=True)
class HookAudit:
    sequence: int
    name: str
    phase: HookPhase
    status: str
    feedback: str | None = None


@dataclass(frozen=True)
class HookDispatchResult:
    phase: HookPhase
    allowed: bool
    feedback: tuple[str, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)
    executed: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


class HookManager:
    def __init__(
        self,
        hooks: list[HookSpec] | tuple[HookSpec, ...],
        *,
        permission_policy: PermissionPolicy | None = None,
    ) -> None:
        self.permission_policy = permission_policy
        self._hooks = tuple(hooks)
        self._audit: list[HookAudit] = []

    @property
    def hooks(self) -> tuple[HookSpec, ...]:
        return self._hooks

    @property
    def audit(self) -> tuple[HookAudit, ...]:
        return tuple(self._audit)

    def dispatch(self, phase: HookPhase, payload: Mapping[str, Any]) -> HookDispatchResult:
        feedback: list[str] = []
        metadata: dict[str, Any] = {}
        executed: list[str] = []
        allowed = True
        for spec in sorted(
            (hook for hook in self._hooks if hook.enabled and hook.phase is phase),
            key=lambda hook: (hook.priority, hook.name),
        ):
            if spec.required_action and self.permission_policy is not None:
                decision = self.permission_policy.authorize(
                    spec.required_action,
                    payload,
                    approval=bool(payload.get("approval", False)),
                )
                if not decision.allowed:
                    allowed = False
                    feedback.append(decision.reason)
                    self._record(spec, "denied", decision.reason)
                    if spec.failure_strategy is HookFailureStrategy.STOP:
                        break
                    continue
            try:
                output = self._invoke(spec, payload)
                if not isinstance(output, HookOutput):
                    raise TypeError("hook must return HookOutput")
            except TimeoutError:
                message = f"hook {spec.name} timed out"
                feedback.append(message)
                self._record(spec, "timeout", message)
                if spec.failure_strategy is HookFailureStrategy.DENY:
                    allowed = False
                if spec.failure_strategy is HookFailureStrategy.STOP:
                    break
                continue
            except Exception as exc:
                message = f"hook {spec.name} failed: {exc}"
                feedback.append(message)
                self._record(spec, "error", message)
                if spec.failure_strategy is HookFailureStrategy.DENY:
                    allowed = False
                if spec.failure_strategy is HookFailureStrategy.STOP:
                    break
                continue
            executed.append(spec.name)
            if not output.allow:
                allowed = False
            if output.feedback:
                feedback.append(output.feedback)
            metadata.update(output.metadata)
            self._record(spec, "completed", output.feedback)
        return HookDispatchResult(phase, allowed, tuple(feedback), metadata, tuple(executed))

    @classmethod
    def from_config(
        cls,
        user_path: Path | None,
        project_path: Path | None,
        handlers: Mapping[str, HookHandler],
        *,
        permission_policy: PermissionPolicy | None = None,
    ) -> HookManager:
        merged: dict[str, dict[str, Any]] = {}
        for path in (user_path, project_path):
            if path is None or not path.is_file():
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or not isinstance(payload.get("hooks"), list):
                raise ValueError("hook config must contain a hooks list")
            for item in payload["hooks"]:
                if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                    raise ValueError("hook config entries require a name")
                merged[item["name"]] = item
        specs = []
        for item in merged.values():
            handler_name = item.get("handler", item["name"])
            if handler_name not in handlers:
                raise ValueError(f"no handler registered for hook {handler_name}")
            specs.append(
                HookSpec(
                    name=item["name"],
                    phase=HookPhase(item["phase"]),
                    handler=handlers[handler_name],
                    priority=int(item.get("priority", 100)),
                    timeout_seconds=float(item.get("timeout_seconds", 1.0)),
                    failure_strategy=HookFailureStrategy(
                        item.get("failure_strategy", HookFailureStrategy.CONTINUE.value)
                    ),
                    required_action=item.get("required_action"),
                    enabled=bool(item.get("enabled", True)),
                )
            )
        return cls(specs, permission_policy=permission_policy)

    def _invoke(self, spec: HookSpec, payload: Mapping[str, Any]) -> HookOutput:
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(spec.handler, MappingProxyType(dict(payload)))
            return future.result(timeout=spec.timeout_seconds)
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def _record(self, spec: HookSpec, status: str, feedback: str | None) -> None:
        self._audit.append(HookAudit(len(self._audit), spec.name, spec.phase, status, feedback))
