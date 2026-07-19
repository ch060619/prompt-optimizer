from __future__ import annotations

import json
import os
import re
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from threading import Event, Lock
from typing import Any, Protocol
from uuid import uuid4

# RC ID: RC-073. Provide cooperative run control and idempotent model/write operation accounting.


class RunStatus(StrEnum):
    RUNNING = "running"
    PAUSED = "paused"
    FAILED = "failed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RunCommand(StrEnum):
    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"
    RETRY = "retry"
    REGENERATE = "regenerate"


class OperationKind(StrEnum):
    MODEL = "model"
    WRITE = "write"


class RunCancelled(RuntimeError):
    pass


class UnsafeRetry(RuntimeError):
    pass


@dataclass(frozen=True)
class RunCommandEvent:
    sequence: int
    command: RunCommand
    status: RunStatus
    run_id: str
    attempt: int = 1


@dataclass(frozen=True)
class OperationRecord:
    key: str
    kind: OperationKind
    attempt: int
    state: str
    result: Any = None
    error: str | None = None


@dataclass(frozen=True)
class RunCheckpoint:
    run_id: str
    status: RunStatus
    generation: int
    attempt: int
    events: tuple[RunCommandEvent, ...]


class IdempotencyStore(Protocol):
    def load(self, key: str) -> OperationRecord | None:
        pass

    def save(self, record: OperationRecord) -> None:
        pass

    def load_chain(self, key: str) -> tuple[OperationRecord, ...]:
        pass


class RunControlStore(Protocol):
    def load(self, run_id: str) -> RunCheckpoint | None:
        pass

    def save(self, checkpoint: RunCheckpoint) -> None:
        pass


class InMemoryIdempotencyStore:
    def __init__(self) -> None:
        self._records: dict[str, list[OperationRecord]] = {}

    def load(self, key: str) -> OperationRecord | None:
        records = self._records.get(key, [])
        return records[-1] if records else None

    def save(self, record: OperationRecord) -> None:
        self._records.setdefault(record.key, []).append(record)

    def load_chain(self, key: str) -> tuple[OperationRecord, ...]:
        return tuple(self._records.get(key, ()))


class JsonIdempotencyStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def load(self, key: str) -> OperationRecord | None:
        records = self.load_chain(key)
        return records[-1] if records else None

    def save(self, record: OperationRecord) -> None:
        path = self._path(record.key)
        records = [*self.load_chain(record.key), record]
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        try:
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                json.dump(
                    {
                        "key": record.key,
                        "records": [_operation_payload(item) for item in records],
                    },
                    handle,
                    ensure_ascii=False,
                    sort_keys=True,
                )
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def load_chain(self, key: str) -> tuple[OperationRecord, ...]:
        path = self._path(key)
        if not path.is_file():
            return ()
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw_records = payload.get("records")
        if raw_records is None:
            raw_records = [payload]
        if not isinstance(raw_records, list):
            raise ValueError("idempotency records must be a list")
        return tuple(_operation_from_payload(item) for item in raw_records)

    def _path(self, key: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9._:-]+", key):
            raise ValueError("invalid idempotency key")
        return self.directory / f"{key}.json"


class InMemoryRunControlStore:
    def __init__(self) -> None:
        self._checkpoints: dict[str, RunCheckpoint] = {}

    def load(self, run_id: str) -> RunCheckpoint | None:
        return self._checkpoints.get(run_id)

    def save(self, checkpoint: RunCheckpoint) -> None:
        self._checkpoints[checkpoint.run_id] = checkpoint


class JsonRunControlStore:
    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)

    def load(self, run_id: str) -> RunCheckpoint | None:
        path = self._path(run_id)
        if not path.is_file():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("run_id") != run_id:
            raise ValueError("invalid run control checkpoint")
        raw_events = payload.get("events", [])
        if not isinstance(raw_events, list):
            raise ValueError("run control events must be a list")
        events = tuple(
            RunCommandEvent(
                sequence=int(item["sequence"]),
                command=RunCommand(item["command"]),
                status=RunStatus(item["status"]),
                run_id=item["run_id"],
                attempt=int(item.get("attempt", 1)),
            )
            for item in raw_events
        )
        return RunCheckpoint(
            run_id=run_id,
            status=RunStatus(payload["status"]),
            generation=int(payload.get("generation", 0)),
            attempt=int(payload.get("attempt", 1)),
            events=events,
        )

    def save(self, checkpoint: RunCheckpoint) -> None:
        path = self._path(checkpoint.run_id)
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        payload = {
            "run_id": checkpoint.run_id,
            "status": checkpoint.status.value,
            "generation": checkpoint.generation,
            "attempt": checkpoint.attempt,
            "events": [
                {
                    "sequence": event.sequence,
                    "command": event.command.value,
                    "status": event.status.value,
                    "run_id": event.run_id,
                    "attempt": event.attempt,
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

    def _path(self, run_id: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9._:-]+", run_id):
            raise ValueError("invalid run id")
        return self.directory / f"{run_id.replace(':', '--')}.json"


class IdempotencyLedger:
    def __init__(self, store: IdempotencyStore | None = None) -> None:
        self.store = store or InMemoryIdempotencyStore()
        self._lock = Lock()
        self._operation_locks: dict[str, Lock] = {}
        self._history: list[OperationRecord] = []

    @property
    def history(self) -> tuple[OperationRecord, ...]:
        with self._lock:
            return tuple(self._history)

    def history_for(self, key: str) -> tuple[OperationRecord, ...]:
        loader = getattr(self.store, "load_chain", None)
        if callable(loader):
            return tuple(loader(key))
        record = self.store.load(key)
        return (record,) if record is not None else ()

    def execute(
        self,
        key: str,
        kind: OperationKind,
        operation: Callable[[], Any],
    ) -> Any:
        operation_lock = self._operation_lock(key)
        with operation_lock:
            existing = self.store.load(key)
            if existing is not None:
                if existing.kind is not kind:
                    raise UnsafeRetry(f"operation kind changed for {key}")
                if existing.state == "succeeded":
                    return existing.result
                if kind is OperationKind.WRITE:
                    raise UnsafeRetry(f"write operation {key} cannot be safely retried")
            attempt = self._begin(key, kind)
            try:
                result = operation()
            except Exception as exc:
                self._finish(key, OperationRecord(key, kind, attempt, "failed", error=str(exc)))
                raise
            succeeded = OperationRecord(key, kind, attempt, "succeeded", result=result)
            self._finish(key, succeeded)
            return result

    def execute_stream(
        self,
        key: str,
        kind: OperationKind,
        operation: Callable[[], Iterable[Any]],
    ) -> Iterator[Any]:
        operation_lock = self._operation_lock(key)
        operation_lock.acquire()
        try:
            existing = self.store.load(key)
            if existing is not None:
                if existing.kind is not kind:
                    raise UnsafeRetry(f"operation kind changed for {key}")
                if existing.state == "succeeded":
                    if not isinstance(existing.result, list):
                        raise UnsafeRetry(f"completed stream {key} has no replayable result")
                    yield from existing.result
                    return
                if kind is OperationKind.WRITE:
                    raise UnsafeRetry(f"write operation {key} cannot be safely retried")
            attempt = self._begin(key, kind)
            result: list[Any] = []
            try:
                for item in operation():
                    result.append(item)
                    yield item
            except GeneratorExit:
                self._finish(
                    key,
                    OperationRecord(key, kind, attempt, "failed", error="stream closed"),
                )
                raise
            except Exception as exc:
                self._finish(
                    key,
                    OperationRecord(key, kind, attempt, "failed", error=str(exc)),
                )
                raise
            else:
                self._finish(key, OperationRecord(key, kind, attempt, "succeeded", result=result))
        finally:
            operation_lock.release()

    def _begin(self, key: str, kind: OperationKind) -> int:
        with self._lock:
            existing = self.store.load(key)
            if existing is not None:
                if existing.kind is not kind:
                    raise UnsafeRetry(f"operation kind changed for {key}")
                if existing.state == "succeeded":
                    raise AssertionError("successful operations are handled before _begin")
                if kind is OperationKind.WRITE:
                    raise UnsafeRetry(f"write operation {key} cannot be safely retried")
            attempt = (existing.attempt if existing else 0) + 1
            self._save(OperationRecord(key, kind, attempt, "in_flight"))
            return attempt

    def _finish(self, key: str, record: OperationRecord) -> None:
        with self._lock:
            self._save(record)

    def _save(self, record: OperationRecord) -> None:
        self.store.save(record)
        self._history.append(record)

    def _operation_lock(self, key: str) -> Lock:
        with self._lock:
            return self._operation_locks.setdefault(key, Lock())


class RunController:
    def __init__(self, run_id: str | None = None, store: RunControlStore | None = None) -> None:
        self.run_id = run_id or uuid4().hex
        self._status = RunStatus.RUNNING
        self._pause_gate = Event()
        self._pause_gate.set()
        self._cancel = Event()
        self._lock = Lock()
        self._events: list[RunCommandEvent] = []
        self._generation = 0
        self._attempt = 1
        self._store = store
        if store is not None:
            checkpoint = store.load(self.run_id)
            if checkpoint is not None:
                self._status = checkpoint.status
                self._generation = checkpoint.generation
                self._attempt = checkpoint.attempt
                self._events = list(checkpoint.events)
                if self._status is RunStatus.PAUSED:
                    self._pause_gate.clear()
                elif self._status is RunStatus.CANCELLED:
                    self._cancel.set()

    @property
    def status(self) -> RunStatus:
        with self._lock:
            return self._status

    @property
    def events(self) -> tuple[RunCommandEvent, ...]:
        with self._lock:
            return tuple(self._events)

    def command(self, command: RunCommand) -> str | None:
        with self._lock:
            if command is RunCommand.PAUSE:
                if self._status is not RunStatus.RUNNING:
                    raise ValueError("only running runs can be paused")
                self._status = RunStatus.PAUSED
                self._pause_gate.clear()
            elif command is RunCommand.RESUME:
                if self._status is not RunStatus.PAUSED:
                    raise ValueError("run is not paused")
                self._status = RunStatus.RUNNING
                self._pause_gate.set()
            elif command is RunCommand.CANCEL:
                if self._status in {RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED}:
                    return None
                self._status = RunStatus.CANCELLED
                self._cancel.set()
                self._pause_gate.set()
            elif command is RunCommand.RETRY:
                if self._status is not RunStatus.FAILED:
                    raise ValueError("only failed runs can be retried")
                self._status = RunStatus.RUNNING
                self._attempt += 1
                self._cancel.clear()
                self._pause_gate.set()
            elif command is RunCommand.REGENERATE:
                if self._status in {RunStatus.RUNNING, RunStatus.PAUSED}:
                    raise ValueError("stop the active run before regenerating")
                self._generation += 1
                self._attempt = 1
                self._status = RunStatus.RUNNING
                self._cancel.clear()
                self._pause_gate.set()
                self.run_id = f"{self.run_id.split(':gen-')[0]}:gen-{self._generation}"
            else:
                raise ValueError(f"unsupported run command: {command}")
            self._events.append(
                RunCommandEvent(
                    len(self._events), command, self._status, self.run_id, self._attempt
                )
            )
            self._save()
            return self.run_id if command is RunCommand.REGENERATE else None

    def check(self) -> None:
        self._pause_gate.wait()
        if self._cancel.is_set() or self.status is RunStatus.CANCELLED:
            raise RunCancelled("run cancelled")

    def mark_failed(self) -> None:
        with self._lock:
            if self._status is RunStatus.CANCELLED:
                return
            self._status = RunStatus.FAILED
            self._pause_gate.set()
            self._save()

    def mark_completed(self) -> None:
        with self._lock:
            if self._status in {RunStatus.CANCELLED, RunStatus.FAILED}:
                return
            self._status = RunStatus.COMPLETED
            self._save()

    def _save(self) -> None:
        if self._store is not None:
            self._store.save(
                RunCheckpoint(
                    self.run_id,
                    self._status,
                    self._generation,
                    self._attempt,
                    tuple(self._events),
                )
            )


def _operation_payload(record: OperationRecord) -> dict[str, Any]:
    return {
        "key": record.key,
        "kind": record.kind.value,
        "attempt": record.attempt,
        "state": record.state,
        "result": _json_value(record.result),
        "error": record.error,
    }


def _operation_from_payload(payload: Mapping[str, Any]) -> OperationRecord:
    return OperationRecord(
        key=str(payload["key"]),
        kind=OperationKind(payload["kind"]),
        attempt=int(payload["attempt"]),
        state=str(payload["state"]),
        result=payload.get("result"),
        error=payload.get("error"),
    )


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return {
            key: _json_value(getattr(value, key))
            for key in value.__dataclass_fields__
        }
    raise TypeError(f"idempotency result is not JSON serializable: {type(value).__name__}")
