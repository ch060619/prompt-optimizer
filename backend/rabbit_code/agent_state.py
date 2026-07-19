from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Protocol
from uuid import uuid4

# RC ID: RC-068. Define the observable Agent state machine and persistent checkpoints.


class AgentState(StrEnum):
    RECEIVED = "received"
    CONTEXT = "context"
    MODEL = "model"
    TOOL_PENDING = "tool_pending"
    APPROVAL = "approval"
    TOOL_RUNNING = "tool_running"
    CONTINUING = "continuing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


ALLOWED_TRANSITIONS: dict[AgentState, frozenset[AgentState]] = {
    AgentState.RECEIVED: frozenset({AgentState.CONTEXT, AgentState.FAILED, AgentState.CANCELLED}),
    AgentState.CONTEXT: frozenset({AgentState.MODEL, AgentState.FAILED, AgentState.CANCELLED}),
    AgentState.MODEL: frozenset(
        {
            AgentState.TOOL_PENDING,
            AgentState.CONTINUING,
            AgentState.COMPLETED,
            AgentState.FAILED,
            AgentState.CANCELLED,
        }
    ),
    AgentState.TOOL_PENDING: frozenset(
        {AgentState.APPROVAL, AgentState.FAILED, AgentState.CANCELLED}
    ),
    AgentState.APPROVAL: frozenset(
        {
            AgentState.TOOL_RUNNING,
            AgentState.CONTINUING,
            AgentState.FAILED,
            AgentState.CANCELLED,
        }
    ),
    AgentState.TOOL_RUNNING: frozenset(
        {AgentState.CONTINUING, AgentState.FAILED, AgentState.CANCELLED}
    ),
    AgentState.CONTINUING: frozenset(
        {AgentState.MODEL, AgentState.COMPLETED, AgentState.FAILED, AgentState.CANCELLED}
    ),
    AgentState.COMPLETED: frozenset(),
    AgentState.FAILED: frozenset(),
    AgentState.CANCELLED: frozenset(),
}


@dataclass(frozen=True)
class AgentStateEvent:
    sequence: int
    from_state: AgentState
    to_state: AgentState
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))


@dataclass(frozen=True)
class AgentCheckpoint:
    run_id: str
    state: AgentState
    events: tuple[AgentStateEvent, ...]


class CheckpointStore(Protocol):
    def save(self, checkpoint: AgentCheckpoint) -> None:
        pass

    def load(self, run_id: str) -> AgentCheckpoint | None:
        pass


class InMemoryCheckpointStore:
    def __init__(self) -> None:
        self._checkpoints: dict[str, AgentCheckpoint] = {}

    def save(self, checkpoint: AgentCheckpoint) -> None:
        self._checkpoints[checkpoint.run_id] = checkpoint

    def load(self, run_id: str) -> AgentCheckpoint | None:
        return self._checkpoints.get(run_id)


class JsonCheckpointStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, checkpoint: AgentCheckpoint) -> None:
        path = self._path(checkpoint.run_id)
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        payload = {
            "run_id": checkpoint.run_id,
            "state": checkpoint.state.value,
            "events": [
                {
                    "sequence": event.sequence,
                    "from_state": event.from_state.value,
                    "to_state": event.to_state.value,
                    "payload": dict(event.payload),
                }
                for event in checkpoint.events
            ],
        }
        try:
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                json.dump(payload, handle, ensure_ascii=False, sort_keys=True)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def load(self, run_id: str) -> AgentCheckpoint | None:
        path = self._path(run_id)
        if not path.is_file():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("run_id") != run_id:
            raise ValueError("invalid Agent checkpoint")
        raw_events = payload.get("events")
        if not isinstance(raw_events, list):
            raise ValueError("Agent checkpoint events must be a list")
        events = tuple(
            AgentStateEvent(
                sequence=int(item["sequence"]),
                from_state=AgentState(item["from_state"]),
                to_state=AgentState(item["to_state"]),
                payload=item.get("payload", {}),
            )
            for item in raw_events
        )
        machine = AgentStateMachine.replay(run_id, events)
        expected_state = AgentState(payload["state"])
        if machine.state is not expected_state:
            raise ValueError("Agent checkpoint state does not match its events")
        return machine.checkpoint()

    def _path(self, run_id: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9._-]+", run_id):
            raise ValueError("invalid Agent checkpoint id")
        return self.directory / f"{run_id}.json"


class AgentStateMachine:
    def __init__(self, run_id: str, store: CheckpointStore | None = None) -> None:
        if not run_id:
            raise ValueError("run_id is required")
        self.run_id = run_id
        self.store = store
        self._state = AgentState.RECEIVED
        self._events: list[AgentStateEvent] = []

    @property
    def state(self) -> AgentState:
        return self._state

    @property
    def events(self) -> tuple[AgentStateEvent, ...]:
        return tuple(self._events)

    def transition(
        self,
        target: AgentState,
        payload: Mapping[str, Any] | None = None,
    ) -> AgentStateEvent:
        if target not in ALLOWED_TRANSITIONS[self._state]:
            raise ValueError(f"invalid Agent transition: {self._state.value} -> {target.value}")
        event = AgentStateEvent(
            sequence=len(self._events),
            from_state=self._state,
            to_state=target,
            payload=payload or {},
        )
        self._apply(event)
        self._save()
        return event

    def checkpoint(self) -> AgentCheckpoint:
        return AgentCheckpoint(self.run_id, self._state, self.events)

    @classmethod
    def replay(
        cls,
        run_id: str,
        events: Sequence[AgentStateEvent],
        store: CheckpointStore | None = None,
    ) -> AgentStateMachine:
        machine = cls(run_id, store)
        for event in events:
            machine._apply(event)
        return machine

    def _apply(self, event: AgentStateEvent) -> None:
        if event.sequence != len(self._events):
            raise ValueError("Agent event sequence is not contiguous")
        if event.from_state is not self._state:
            raise ValueError("Agent event does not continue the current state")
        if event.to_state not in ALLOWED_TRANSITIONS[self._state]:
            raise ValueError(
                f"invalid Agent transition: {self._state.value} -> {event.to_state.value}"
            )
        self._state = event.to_state
        self._events.append(event)

    def _save(self) -> None:
        if self.store is not None:
            self.store.save(self.checkpoint())
