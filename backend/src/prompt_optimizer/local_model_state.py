from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

# RC IDs: RC-194, RC-225. Keep local model lifecycle states and restart recovery explicit.

LocalModelStatus = Literal[
    "not_installed",
    "downloading",
    "paused",
    "verifying",
    "loading",
    "ready",
    "busy",
    "stopping",
    "unloaded",
    "corrupt",
    "update",
    "failed",
    "disabled",
]
LocalModelEventName = Literal[
    "download_started",
    "download_progress",
    "download_paused",
    "download_completed",
    "verified",
    "load_started",
    "ready",
    "busy",
    "unload_started",
    "unloaded",
    "corrupt",
    "update_available",
    "update_started",
    "failed",
    "reset",
    "disable",
    "enable",
]
RunnerRecoveryStatus = Literal["unknown", "not_installed", "ready", "busy"]


class LocalModelStateError(ValueError):
    """Raised when a local model lifecycle event is not reachable."""


_EVENT_TARGETS: dict[LocalModelEventName, LocalModelStatus] = {
    "download_started": "downloading",
    "download_progress": "downloading",
    "download_paused": "paused",
    "download_completed": "verifying",
    "verified": "loading",
    "load_started": "loading",
    "ready": "ready",
    "busy": "busy",
    "unload_started": "stopping",
    "unloaded": "unloaded",
    "corrupt": "corrupt",
    "update_available": "update",
    "update_started": "update",
    "failed": "failed",
    "reset": "not_installed",
    "disable": "disabled",
    "enable": "ready",
}

_ALLOWED_TRANSITIONS: dict[LocalModelStatus, frozenset[LocalModelEventName]] = {
    "not_installed": frozenset({"download_started", "update_started"}),
    "downloading": frozenset(
        {
            "download_started",
            "download_progress",
            "download_paused",
            "download_completed",
            "failed",
            "corrupt",
            "reset",
        }
    ),
    "paused": frozenset({"download_started", "download_progress", "reset", "failed"}),
    "verifying": frozenset({"download_started", "verified", "corrupt", "failed", "reset"}),
    "loading": frozenset({"ready", "busy", "failed", "corrupt", "reset"}),
    "ready": frozenset(
        {
            "load_started",
            "busy",
            "unload_started",
            "update_available",
            "update_started",
            "reset",
            "disable",
        }
    ),
    "busy": frozenset({"ready", "unload_started", "failed", "disable"}),
    "stopping": frozenset({"ready", "unloaded", "failed"}),
    "unloaded": frozenset({"load_started", "download_started", "update_started", "reset"}),
    "corrupt": frozenset(
        {
            "download_started",
            "download_progress",
            "verified",
            "unload_started",
            "reset",
            "failed",
        }
    ),
    "update": frozenset(
        {
            "update_started",
            "download_started",
            "download_progress",
            "download_completed",
            "verified",
            "load_started",
            "ready",
            "failed",
            "corrupt",
            "reset",
        }
    ),
    "failed": frozenset(
        {
            "download_started",
            "download_progress",
            "verified",
            "load_started",
            "unload_started",
            "reset",
            "failed",
        }
    ),
    "disabled": frozenset({"enable", "reset"}),
}


@dataclass(frozen=True)
class LocalModelState:
    model_id: str
    runner: str
    status: LocalModelStatus = "not_installed"
    progress: int = 0
    installed_path: str | None = None
    version: str | None = None
    error: str | None = None
    last_event: str = "recovered"

    @property
    def recovery_actions(self) -> tuple[str, ...]:
        if self.status in {"failed", "corrupt"}:
            return ("retry", "repair", "uninstall")
        if self.status in {"not_installed", "unloaded"}:
            return ("install",)
        if self.status == "update":
            return ("update", "uninstall")
        return ()

    def to_dict(self) -> dict[str, object]:
        return {
            "model_id": self.model_id,
            "runner": self.runner,
            "status": self.status,
            "progress": self.progress,
            "installed_path": self.installed_path,
            "version": self.version,
            "error": self.error,
            "last_event": self.last_event,
            "recovery_actions": list(self.recovery_actions),
        }


@dataclass(frozen=True)
class LocalModelEvent:
    event: LocalModelEventName
    message: str
    state: LocalModelState

    def to_dict(self) -> dict[str, object]:
        return {
            "event": self.event,
            "message": self.message,
            "state": self.state.to_dict(),
        }


class LocalModelStateMachine:
    def __init__(self, state: LocalModelState) -> None:
        self.state = state

    def apply(
        self,
        event: LocalModelEventName,
        *,
        message: str = "",
        progress: int | None = None,
        error: str | None = None,
    ) -> LocalModelEvent:
        if event not in _ALLOWED_TRANSITIONS[self.state.status]:
            raise LocalModelStateError(
                f"cannot apply {event!r} from {self.state.status!r}"
            )
        next_state = replace(
            self.state,
            status=_EVENT_TARGETS[event],
            progress=(
                self.state.progress
                if progress is None
                else min(100, max(0, progress))
            ),
            error=error,
            last_event=event,
        )
        if next_state.status in {"not_installed", "unloaded"}:
            next_state = replace(next_state, progress=0)
        if next_state.status in {"ready", "busy"}:
            next_state = replace(next_state, progress=100)
        self.state = next_state
        return LocalModelEvent(event=event, message=message, state=next_state)


def state_from_install_snapshot(payload: dict[str, object]) -> LocalModelState:
    """Translate the persisted installer contract into the GUI lifecycle contract."""
    model_id = _string(payload, "model_id")
    runner = _string(payload, "runner")
    status = payload.get("status")
    phase = payload.get("phase")
    raw_error = payload.get("error")
    error = raw_error if isinstance(raw_error, str) else None
    if status == "failed":
        lifecycle_status: LocalModelStatus = (
            "corrupt" if error and "checksum" in error.lower() else "failed"
        )
    elif status == "cancelled":
        lifecycle_status = "not_installed"
    elif phase == "download" and status in {"downloading", "paused"}:
        lifecycle_status = "paused" if status == "paused" else "downloading"
    elif phase == "verify":
        lifecycle_status = "verifying"
    elif phase == "install":
        lifecycle_status = "loading"
    elif status == "health_check":
        lifecycle_status = "loading"
    elif status == "running":
        lifecycle_status = "busy"
    elif status == "ready":
        lifecycle_status = "ready"
    else:
        lifecycle_status = "not_installed"
    progress = payload.get("progress")
    raw_installed_path = payload.get("installed_path")
    installed_path = raw_installed_path if isinstance(raw_installed_path, str) else None
    raw_version = payload.get("version")
    version = raw_version if isinstance(raw_version, str) else None
    return LocalModelState(
        model_id=model_id,
        runner=runner,
        status=lifecycle_status,
        progress=progress if isinstance(progress, int) else 0,
        installed_path=installed_path,
        version=version,
        error=error,
        last_event="recovered",
    )


def recover_state(
    state: LocalModelState,
    *,
    installed_path: Path | None = None,
    runner_status: RunnerRecoveryStatus = "unknown",
) -> LocalModelState:
    """Recover only from durable files and the runner's reported status after restart."""
    file_exists = installed_path is not None and installed_path.is_file()
    if state.status in {"downloading", "paused", "verifying"}:
        return state
    if state.status in {"failed", "corrupt", "update", "disabled"}:
        return state
    if not file_exists:
        return replace(state, status="not_installed", progress=0, last_event="recovered")
    if runner_status == "busy":
        return replace(state, status="busy", progress=100, last_event="recovered")
    if runner_status == "ready":
        return replace(state, status="ready", progress=100, last_event="recovered")
    return replace(state, status="ready", progress=100, last_event="recovered")


def recover_install_state(
    state_path: Path,
    *,
    runner_status: RunnerRecoveryStatus = "unknown",
) -> LocalModelState:
    """Load installer state and verify the recorded installed file before exposing ready."""
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise LocalModelStateError(f"invalid local model state: {state_path}") from exc
    if not isinstance(payload, dict):
        raise LocalModelStateError(f"invalid local model state: {state_path}")
    state = state_from_install_snapshot(payload)
    installed_path = Path(state.installed_path) if state.installed_path else None
    return recover_state(state, installed_path=installed_path, runner_status=runner_status)


def _string(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise LocalModelStateError(f"local model state field {key!r} is invalid")
    return value
