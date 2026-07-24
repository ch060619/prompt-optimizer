from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

# RC ID: RC-212. Persist minimal, redacted, hash-chained audit decisions.

_GENESIS = "GENESIS"
_DEFAULT_RETENTION_DAYS = 30
_MAX_TEXT_LENGTH = 128
_SAFE_METADATA_KEYS = frozenset(
    {
        "action",
        "approval_id",
        "bytes",
        "capability",
        "config_source",
        "config_version",
        "count",
        "decision",
        "duration_ms",
        "error_category",
        "error_code",
        "execution_location",
        "model",
        "permission_mode",
        "policy",
        "provider",
        "remote",
        "request_id",
        "resource_type",
        "result_count",
        "retryable",
        "scope",
        "status",
        "task_id",
        "tool_id",
    }
)


class AuditCategory(StrEnum):
    PERMISSION = "permission"
    TOOL = "tool"
    CONFIG = "config"
    EXTERNAL_REQUEST = "external_request"


@dataclass(frozen=True)
class AuditEvent:
    sequence: int
    event_id: str
    created_at: datetime
    actor_id: str
    category: AuditCategory
    action: str
    outcome: str
    session_id: str | None
    request_id: str | None
    tool_id: str | None
    task_id: str | None
    resource_id: str | None
    reason_code: str | None
    metadata: Mapping[str, object]
    previous_hash: str
    event_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "event_id": self.event_id,
            "created_at": self.created_at.isoformat(),
            "actor_id": self.actor_id,
            "category": self.category.value,
            "action": self.action,
            "outcome": self.outcome,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "tool_id": self.tool_id,
            "task_id": self.task_id,
            "resource_id": self.resource_id,
            "reason_code": self.reason_code,
            "metadata": dict(self.metadata),
            "previous_hash": self.previous_hash,
            "event_hash": self.event_hash,
        }


class AuditLogService:
    """SQLite audit log with explicit retention and destructive cleanup controls."""

    def __init__(
        self,
        db_path: Path,
        *,
        retention_days: int | None = _DEFAULT_RETENTION_DAYS,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._clock = clock or (lambda: datetime.now(UTC))
        _validate_retention_days(retention_days)
        self._initialize(retention_days)

    @property
    def retention_days(self) -> int | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT value FROM audit_settings WHERE name = 'retention_days'"
            ).fetchone()
        if row is None:
            raise RuntimeError("audit retention setting is missing")
        return _decode_retention(row[0])

    def set_retention_days(self, retention_days: int | None) -> None:
        _validate_retention_days(retention_days)
        encoded = _encode_retention(retention_days)
        with self._connect() as connection:
            connection.execute(
                "UPDATE audit_settings SET value = ? WHERE name = 'retention_days'",
                (encoded,),
            )

    def record(
        self,
        *,
        actor_id: str,
        category: AuditCategory,
        action: str,
        outcome: str,
        session_id: str | None = None,
        request_id: str | None = None,
        tool_id: str | None = None,
        task_id: str | None = None,
        resource_id: str | None = None,
        reason_code: str | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> AuditEvent:
        actor_id = _required_text(actor_id, "actor_id")
        action = _required_text(action, "action")
        outcome = _required_text(outcome, "outcome")
        if not isinstance(category, AuditCategory):
            raise TypeError("category must be an AuditCategory")
        values = {
            name: _optional_text(value, name)
            for name, value in (
                ("session_id", session_id),
                ("request_id", request_id),
                ("tool_id", tool_id),
                ("task_id", task_id),
                ("resource_id", resource_id),
                ("reason_code", reason_code),
            )
        }
        created_at = _utc(self._clock())
        safe_metadata = _safe_metadata(metadata or {})
        event_id = uuid4().hex
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            previous_hash = _latest_hash(connection)
            payload = _event_payload(
                event_id=event_id,
                created_at=created_at,
                actor_id=actor_id,
                category=category,
                action=action,
                outcome=outcome,
                values=values,
                reason_code=values["reason_code"],
                metadata=safe_metadata,
                previous_hash=previous_hash,
            )
            event_hash = _hash_payload(payload)
            cursor = connection.execute(
                """
                INSERT INTO audit_events (
                    event_id, created_at, actor_id, category, action, outcome,
                    session_id, request_id, tool_id, task_id, resource_id,
                    reason_code, metadata_json, previous_hash, event_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    created_at.isoformat(),
                    actor_id,
                    category.value,
                    action,
                    outcome,
                    values["session_id"],
                    values["request_id"],
                    values["tool_id"],
                    values["task_id"],
                    values["resource_id"],
                    values["reason_code"],
                    json.dumps(safe_metadata, ensure_ascii=False, sort_keys=True),
                    previous_hash,
                    event_hash,
                ),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("audit event insert did not return a sequence")
            sequence = int(cursor.lastrowid)
        return AuditEvent(
            sequence=sequence,
            event_id=event_id,
            created_at=created_at,
            actor_id=actor_id,
            category=category,
            action=action,
            outcome=outcome,
            session_id=values["session_id"],
            request_id=values["request_id"],
            tool_id=values["tool_id"],
            task_id=values["task_id"],
            resource_id=values["resource_id"],
            reason_code=values["reason_code"],
            metadata=safe_metadata,
            previous_hash=previous_hash,
            event_hash=event_hash,
        )

    def record_permission(self, **kwargs: object) -> AuditEvent:
        return self.record(category=AuditCategory.PERMISSION, **_record_kwargs(kwargs))

    def record_tool(self, **kwargs: object) -> AuditEvent:
        return self.record(category=AuditCategory.TOOL, **_record_kwargs(kwargs))

    def record_config(self, **kwargs: object) -> AuditEvent:
        return self.record(category=AuditCategory.CONFIG, **_record_kwargs(kwargs))

    def record_external_request(self, **kwargs: object) -> AuditEvent:
        return self.record(category=AuditCategory.EXTERNAL_REQUEST, **_record_kwargs(kwargs))

    def query(
        self,
        *,
        session_id: str | None = None,
        category: AuditCategory | None = None,
        actor_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[AuditEvent, ...]:
        if limit < 1 or limit > 1000 or offset < 0:
            raise ValueError("limit must be 1..1000 and offset must be non-negative")
        clauses: list[str] = []
        parameters: list[object] = []
        if session_id is not None:
            clauses.append("session_id = ?")
            parameters.append(_required_text(session_id, "session_id"))
        if category is not None:
            if not isinstance(category, AuditCategory):
                raise TypeError("category must be an AuditCategory")
            clauses.append("category = ?")
            parameters.append(category.value)
        if actor_id is not None:
            clauses.append("actor_id = ?")
            parameters.append(_required_text(actor_id, "actor_id"))
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM audit_events {where} ORDER BY sequence LIMIT ? OFFSET ?",
                (*parameters, limit, offset),
            ).fetchall()
        return tuple(_event_from_row(row) for row in rows)

    def purge_expired(self, *, now: datetime | None = None) -> int:
        retention = self.retention_days
        if retention is None:
            return 0
        cutoff = _utc(now or self._clock()) - timedelta(days=retention)
        return self._delete("created_at < ?", (cutoff.isoformat(),))

    def clear_session(self, session_id: str, *, confirm: bool = False) -> int:
        if not confirm:
            raise PermissionError("session audit deletion requires explicit confirmation")
        return self._delete(
            "session_id = ?",
            (_required_text(session_id, "session_id"),),
        )

    def clear_all(self, *, confirm: bool = False) -> int:
        if not confirm:
            raise PermissionError("all audit deletion requires explicit confirmation")
        return self._delete("1 = 1", ())

    def verify_chain(self) -> bool:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM audit_events ORDER BY sequence").fetchall()
        previous_hash = _GENESIS
        for row in rows:
            event = _event_from_row(row)
            payload = _event_payload_from_event(event, previous_hash=previous_hash)
            if event.previous_hash != previous_hash or event.event_hash != _hash_payload(payload):
                return False
            previous_hash = event.event_hash
        return True

    def _delete(self, where: str, parameters: tuple[object, ...]) -> int:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            deleted = connection.execute(
                f"DELETE FROM audit_events WHERE {where}", parameters
            ).rowcount
            if deleted:
                _rebuild_chain(connection)
            connection.commit()
            if deleted:
                connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                connection.execute("VACUUM")
        return deleted

    def _initialize(self, retention_days: int | None) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_settings (
                    name TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "INSERT OR IGNORE INTO audit_settings(name, value) VALUES ('retention_days', ?)",
                (_encode_retention(retention_days),),
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    action TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    session_id TEXT,
                    request_id TEXT,
                    tool_id TEXT,
                    task_id TEXT,
                    resource_id TEXT,
                    reason_code TEXT,
                    metadata_json TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS audit_events_session_sequence "
                "ON audit_events(session_id, sequence)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS audit_events_created_at ON audit_events(created_at)"
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=30.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection


def _record_kwargs(values: Mapping[str, object]) -> dict[str, Any]:
    return dict(values)


def _required_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > _MAX_TEXT_LENGTH:
        raise ValueError(f"{name} must be non-empty and at most {_MAX_TEXT_LENGTH} characters")
    return value.strip()


def _optional_text(value: object, name: str) -> str | None:
    if value is None:
        return None
    return _required_text(value, name)


def _safe_metadata(metadata: Mapping[str, object]) -> dict[str, object]:
    safe: dict[str, object] = {}
    for key, value in metadata.items():
        if key not in _SAFE_METADATA_KEYS:
            continue
        if isinstance(value, bool):
            safe[key] = value
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            safe[key] = value
        elif isinstance(value, str) and len(value) <= _MAX_TEXT_LENGTH:
            safe[key] = value
    return safe


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _encode_retention(value: int | None) -> str:
    return "none" if value is None else str(value)


def _decode_retention(value: str) -> int | None:
    return None if value == "none" else int(value)


def _validate_retention_days(value: int | None) -> None:
    if value is not None and (not isinstance(value, int) or isinstance(value, bool) or value < 0):
        raise ValueError("retention_days must be a non-negative integer or None")


def _latest_hash(connection: sqlite3.Connection) -> str:
    row = connection.execute(
        "SELECT event_hash FROM audit_events ORDER BY sequence DESC LIMIT 1"
    ).fetchone()
    return str(row[0]) if row is not None else _GENESIS


def _event_payload(
    *,
    event_id: str,
    created_at: datetime,
    actor_id: str,
    category: AuditCategory,
    action: str,
    outcome: str,
    values: Mapping[str, str | None],
    reason_code: str | None,
    metadata: Mapping[str, object],
    previous_hash: str,
) -> dict[str, object]:
    return {
        "event_id": event_id,
        "created_at": created_at.isoformat(),
        "actor_id": actor_id,
        "category": category.value,
        "action": action,
        "outcome": outcome,
        "session_id": values["session_id"],
        "request_id": values["request_id"],
        "tool_id": values["tool_id"],
        "task_id": values["task_id"],
        "resource_id": values["resource_id"],
        "reason_code": reason_code,
        "metadata": dict(metadata),
        "previous_hash": previous_hash,
    }


def _event_payload_from_event(event: AuditEvent, *, previous_hash: str) -> dict[str, object]:
    values = {
        "session_id": event.session_id,
        "request_id": event.request_id,
        "tool_id": event.tool_id,
        "task_id": event.task_id,
        "resource_id": event.resource_id,
    }
    return _event_payload(
        event_id=event.event_id,
        created_at=event.created_at,
        actor_id=event.actor_id,
        category=event.category,
        action=event.action,
        outcome=event.outcome,
        values=values,
        reason_code=event.reason_code,
        metadata=event.metadata,
        previous_hash=previous_hash,
    )


def _hash_payload(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _event_from_row(row: sqlite3.Row) -> AuditEvent:
    return AuditEvent(
        sequence=int(row["sequence"]),
        event_id=str(row["event_id"]),
        created_at=datetime.fromisoformat(str(row["created_at"])),
        actor_id=str(row["actor_id"]),
        category=AuditCategory(str(row["category"])),
        action=str(row["action"]),
        outcome=str(row["outcome"]),
        session_id=row["session_id"],
        request_id=row["request_id"],
        tool_id=row["tool_id"],
        task_id=row["task_id"],
        resource_id=row["resource_id"],
        reason_code=row["reason_code"],
        metadata=json.loads(str(row["metadata_json"])),
        previous_hash=str(row["previous_hash"]),
        event_hash=str(row["event_hash"]),
    )


def _rebuild_chain(connection: sqlite3.Connection) -> None:
    rows = connection.execute("SELECT * FROM audit_events ORDER BY sequence").fetchall()
    previous_hash = _GENESIS
    for row in rows:
        event = _event_from_row(row)
        payload = _event_payload_from_event(event, previous_hash=previous_hash)
        event_hash = _hash_payload(payload)
        connection.execute(
            "UPDATE audit_events SET previous_hash = ?, event_hash = ? WHERE sequence = ?",
            (previous_hash, event_hash, event.sequence),
        )
        previous_hash = event_hash
