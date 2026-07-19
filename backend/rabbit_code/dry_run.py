from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

# RC ID: RC-105. Produce read-only dry-run plans and stable machine event streams.


class LogLevel(StrEnum):
    QUIET = "quiet"
    ERROR = "error"
    INFO = "info"
    DEBUG = "debug"


class MachineEventType(StrEnum):
    DRY_RUN = "dry_run"
    STARTED = "started"
    PROGRESS = "progress"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass(frozen=True)
class DryRunAction:
    command: tuple[str, ...]
    cwd: Path
    permission: str
    would_execute: bool = False
    reason: str = "dry-run is read-only"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["command"] = list(self.command)
        payload["cwd"] = self.cwd.as_posix()
        return payload


@dataclass(frozen=True)
class MachineEvent:
    sequence: int
    type: MachineEventType
    payload: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "seq": self.sequence,
            "type": self.type.value,
            "payload": dict(self.payload),
        }


class MachineEventStream:
    def __init__(self) -> None:
        self._events: list[MachineEvent] = []

    @property
    def events(self) -> tuple[MachineEvent, ...]:
        return tuple(self._events)

    def emit(
        self,
        event_type: MachineEventType,
        payload: Mapping[str, Any] | None = None,
    ) -> MachineEvent:
        event = MachineEvent(len(self._events), event_type, dict(payload or {}))
        self._events.append(event)
        return event

    def jsonl(self) -> str:
        return "".join(
            json.dumps(event.to_dict(), ensure_ascii=False) + "\n"
            for event in self._events
        )

    def json(self) -> dict[str, Any]:
        return {"events": [event.to_dict() for event in self._events]}


class DryRunPlanner:
    def plan(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        permission: str = "read-only",
    ) -> DryRunAction:
        if not command or any(not str(item) for item in command):
            raise ValueError("dry-run command must be non-empty")
        if not cwd.is_dir():
            raise FileNotFoundError(cwd)
        return DryRunAction(tuple(str(item) for item in command), cwd.resolve(), permission)
