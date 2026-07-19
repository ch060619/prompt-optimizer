from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from backend.rabbit_code.session_database import (
    DatabaseCorruptionError,
    SessionDatabase,
)

# RC ID: RC-089. Verify migration, WAL, recovery, backup, rescue, export, and privacy cleanup.


def test_database_initializes_migrations_wal_and_integrity(tmp_path: Path) -> None:
    database = SessionDatabase(tmp_path / "sessions.sqlite3")

    assert database.startup_report.schema_version == 1
    assert database.startup_report.journal_mode == "wal"
    assert database.startup_report.synchronous == 1
    assert database.integrity_check() == "ok"
    with sqlite3.connect(database.db_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 1


def test_startup_marks_unfinished_transaction_as_recovered(tmp_path: Path) -> None:
    path = tmp_path / "sessions.sqlite3"
    database = SessionDatabase(path)
    transaction_id = database.begin_transaction("session-1")

    recovered = SessionDatabase(path)

    assert recovered.startup_report.recovered_transactions == 1
    with sqlite3.connect(path) as connection:
        state = connection.execute(
            "SELECT state FROM transactions WHERE id = ?", (transaction_id,)
        ).fetchone()[0]
    assert state == "recovered"


def test_checkpoint_export_privacy_clear_and_backup_restore(tmp_path: Path) -> None:
    path = tmp_path / "sessions.sqlite3"
    database = SessionDatabase(path, backup_dir=tmp_path / "backups")
    checkpoint_id = database.save_checkpoint(
        "session-a", {"messages": ["a"]}, owner_id="alice"
    )
    database.save_checkpoint("session-b", {"messages": ["b"]}, owner_id="bob")
    assert checkpoint_id == 1
    assert database.latest_checkpoint("session-a") == {"messages": ["a"]}
    assert json.loads(database.export(owner_id="alice"))["checkpoints"][0]["owner_id"] == "alice"

    backup = database.backup()
    restored_path = tmp_path / "restored.sqlite3"
    SessionDatabase.restore_copy(backup.database_path, restored_path)
    restored = SessionDatabase(restored_path)
    assert restored.latest_checkpoint("session-b") == {"messages": ["b"]}

    assert database.privacy_clear(owner_id="alice") == 1
    with pytest.raises(KeyError):
        database.latest_checkpoint("session-a")
    assert database.latest_checkpoint("session-b") == {"messages": ["b"]}


def test_corrupt_database_reports_read_only_rescue_path(tmp_path: Path) -> None:
    path = tmp_path / "corrupt.sqlite3"
    path.write_bytes(b"not a sqlite database")

    with pytest.raises(DatabaseCorruptionError, match="read_only_rescue"):
        SessionDatabase(path)
    connection = SessionDatabase.open_read_only_rescue(path)
    try:
        assert connection.execute("PRAGMA query_only").fetchone()[0] == 1
    finally:
        connection.close()


def test_privacy_clear_requires_an_explicit_scope(tmp_path: Path) -> None:
    database = SessionDatabase(tmp_path / "sessions.sqlite3")
    with pytest.raises(ValueError, match="requires"):
        database.privacy_clear()
    with pytest.raises(ValueError, match="clear_all"):
        database.privacy_clear(owner_id="alice", clear_all=True)
