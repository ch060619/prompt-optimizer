from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote
from uuid import uuid4

from prompt_optimizer.storage.backup import (  # type: ignore[import-untyped]
    BackupResult,
    backup_database,
    restore_database,
    verify_database,
)

# RC ID: RC-089. Harden the session database with recovery and privacy boundaries.


SCHEMA_VERSION = 1


class DatabaseCorruptionError(RuntimeError):
    """Raised when startup cannot validate the session database."""


@dataclass(frozen=True)
class StartupReport:
    schema_version: int
    journal_mode: str
    synchronous: int
    recovered_transactions: int
    integrity: str


class SessionDatabase:
    def __init__(self, db_path: Path, *, backup_dir: Path | None = None) -> None:
        self.db_path = db_path.expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir = (backup_dir or self.db_path.parent / "backups").resolve()
        try:
            self.startup_report = self._initialize()
        except sqlite3.DatabaseError as exc:
            raise DatabaseCorruptionError(
                "session database is not readable; use "
                f"SessionDatabase.open_read_only_rescue({self.db_path!r})"
            ) from exc

    def begin_transaction(self, session_id: str) -> str:
        session_id = _require_text(session_id, "session_id")
        transaction_id = uuid4().hex
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO transactions (id, session_id, state, started_at, finished_at)
                VALUES (?, ?, 'started', ?, NULL)
                """,
                (transaction_id, session_id, _now()),
            )
        return transaction_id

    def finish_transaction(self, transaction_id: str, *, committed: bool) -> None:
        state = "committed" if committed else "rolled_back"
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE transactions
                SET state = ?, finished_at = ?
                WHERE id = ? AND state = 'started'
                """,
                (state, _now(), transaction_id),
            )
            if cursor.rowcount != 1:
                raise KeyError(f"open transaction not found: {transaction_id}")

    def save_checkpoint(
        self,
        session_id: str,
        payload: dict[str, Any],
        *,
        owner_id: str,
    ) -> int:
        session_id = _require_text(session_id, "session_id")
        owner_id = _require_text(owner_id, "owner_id")
        transaction_id = self.begin_transaction(session_id)
        try:
            with self._connect() as connection:
                now = _now()
                connection.execute(
                    """
                    INSERT INTO sessions (id, owner_id, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET owner_id = excluded.owner_id,
                                                  updated_at = excluded.updated_at
                    """,
                    (session_id, owner_id, now),
                )
                cursor = connection.execute(
                    """
                    INSERT INTO session_checkpoints
                        (session_id, owner_id, payload_json, committed_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (session_id, owner_id, json.dumps(payload, ensure_ascii=False), now),
                )
                checkpoint_id = cursor.lastrowid
                if checkpoint_id is None:
                    raise RuntimeError("checkpoint insert did not return an id")
            self.finish_transaction(transaction_id, committed=True)
            return int(checkpoint_id)
        except Exception:
            self.finish_transaction(transaction_id, committed=False)
            raise

    def latest_checkpoint(self, session_id: str) -> dict[str, Any]:
        session_id = _require_text(session_id, "session_id")
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT payload_json
                FROM session_checkpoints
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"checkpoint not found: {session_id}")
        payload = json.loads(row["payload_json"])
        if not isinstance(payload, dict):
            raise ValueError("checkpoint payload must be a JSON object")
        return payload

    def export(self, *, owner_id: str | None = None) -> str:
        with self._connect() as connection:
            if owner_id is None:
                rows = connection.execute(
                    """
                    SELECT session_id, owner_id, payload_json, committed_at
                    FROM session_checkpoints
                    ORDER BY id
                    """
                ).fetchall()
            else:
                owner_id = _require_text(owner_id, "owner_id")
                rows = connection.execute(
                    """
                    SELECT session_id, owner_id, payload_json, committed_at
                    FROM session_checkpoints
                    WHERE owner_id = ?
                    ORDER BY id
                    """,
                    (owner_id,),
                ).fetchall()
        return json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "checkpoints": [
                    {
                        "session_id": row["session_id"],
                        "owner_id": row["owner_id"],
                        "payload": json.loads(row["payload_json"]),
                        "committed_at": row["committed_at"],
                    }
                    for row in rows
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )

    def privacy_clear(
        self,
        *,
        owner_id: str | None = None,
        session_id: str | None = None,
        clear_all: bool = False,
    ) -> int:
        if clear_all and (owner_id is not None or session_id is not None):
            raise ValueError("clear_all cannot be combined with a scope")
        if not clear_all and owner_id is None and session_id is None:
            raise ValueError("privacy clear requires owner_id, session_id, or clear_all")
        with self._connect() as connection:
            if clear_all:
                connection.execute("DELETE FROM transactions")
                cursor = connection.execute("DELETE FROM sessions")
            elif session_id is not None:
                session_id = _require_text(session_id, "session_id")
                session_ids = (session_id,)
                cursor = connection.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            else:
                owner_id = _require_text(owner_id or "", "owner_id")
                session_ids = tuple(
                    row["id"]
                    for row in connection.execute(
                        "SELECT id FROM sessions WHERE owner_id = ?", (owner_id,)
                    ).fetchall()
                )
                cursor = connection.execute("DELETE FROM sessions WHERE owner_id = ?", (owner_id,))
            if not clear_all:
                placeholders = ", ".join("?" for _ in session_ids)
                if session_ids:
                    connection.execute(
                        f"DELETE FROM transactions WHERE session_id IN ({placeholders})",
                        session_ids,
                    )
            return cursor.rowcount

    def integrity_check(self) -> str:
        return verify_database(self.db_path)

    def backup(self) -> BackupResult:
        return backup_database(self.db_path, self.backup_dir, schema_version=SCHEMA_VERSION)

    @staticmethod
    def restore_copy(backup_path: Path, destination: Path, *, overwrite: bool = False) -> None:
        restore_database(backup_path, destination, overwrite=overwrite)

    @staticmethod
    def open_read_only_rescue(database_path: Path) -> sqlite3.Connection:
        path = database_path.expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        uri = f"file:{quote(path.as_posix(), safe='/:')}?mode=ro"
        connection = sqlite3.connect(uri, uri=True)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        return connection

    def _initialize(self) -> StartupReport:
        with self._connect() as connection:
            journal_mode = str(connection.execute("PRAGMA journal_mode = WAL").fetchone()[0])
            connection.execute("PRAGMA synchronous = NORMAL")
            synchronous = int(connection.execute("PRAGMA synchronous").fetchone()[0])
            current_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if current_version > SCHEMA_VERSION:
                raise RuntimeError("session database schema is newer than this runtime")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
                """
            )
            if current_version < 1:
                self._apply_v1(connection)
                connection.execute(
                    "INSERT OR IGNORE INTO schema_migrations (version, applied_at) VALUES (1, ?)",
                    (_now(),),
                )
                connection.execute("PRAGMA user_version = 1")
            pending = connection.execute(
                "SELECT id FROM transactions WHERE state = 'started'"
            ).fetchall()
            if pending:
                connection.execute(
                    """
                    UPDATE transactions
                    SET state = 'recovered', finished_at = ?
                    WHERE state = 'started'
                    """,
                    (_now(),),
                )
            integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
            if integrity != "ok":
                raise sqlite3.DatabaseError(f"integrity check failed: {integrity}")
            return StartupReport(1, journal_mode, synchronous, len(pending), integrity)

    @staticmethod
    def _apply_v1(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                owner_id TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS session_checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                owner_id TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                committed_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                state TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT
            );
            """
        )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=30.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.execute("PRAGMA foreign_keys = ON")
        return connection


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _require_text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")
    return value
