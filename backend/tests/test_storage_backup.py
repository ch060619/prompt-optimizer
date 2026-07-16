from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from prompt_optimizer.auth.service import AuthService
from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.storage.backup import backup_database, restore_database, verify_database
from prompt_optimizer.storage.service import SCHEMA_VERSION, StorageService

# RC ID: RC-053. Verify versioned SQLite migration, backup, rollback, integrity, and restore.


def _create_legacy_v2_copy(path: Path) -> int:
    storage = StorageService(path)
    user = storage.create_user("migration-user", AuthService().hash_password("secret123"))
    version_id = storage.save_version(
        "原始提示词",
        "优化后的提示词",
        Analyzer().analyze("目标：优化提示词。输出格式：列表。"),
        owner_id=user.id,
    )
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA user_version = 0")
    return version_id


def _counts(path: Path) -> tuple[int, int, int]:
    with sqlite3.connect(path) as connection:
        return tuple(
            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("users", "prompt_versions", "tasks")
        )


def _user_version(path: Path) -> int:
    with sqlite3.connect(path) as connection:
        return int(connection.execute("PRAGMA user_version").fetchone()[0])


def test_new_schema_is_versioned_and_reopen_is_idempotent(tmp_path: Path) -> None:
    database = tmp_path / "prompt_optimizer.sqlite3"

    StorageService(database)
    before = _counts(database)
    StorageService(database)

    assert SCHEMA_VERSION == 1
    assert _user_version(database) == SCHEMA_VERSION
    assert _counts(database) == before
    assert not list((tmp_path / "backups").glob("*.sqlite3"))


def test_legacy_copy_is_backed_up_with_config_and_migrated(tmp_path: Path) -> None:
    database = tmp_path / "legacy.sqlite3"
    config = tmp_path / "settings.json"
    config.write_text('{"provider": "offline"}\n', encoding="utf-8")
    _create_legacy_v2_copy(database)
    before = _counts(database)

    StorageService(database, config_path=config)

    backup_dir = tmp_path / "backups"
    backups = list(backup_dir.glob("*.sqlite3"))
    manifests = [path for path in backup_dir.glob("*.json") if "-config" not in path.stem]
    assert len(backups) == 1
    assert len(manifests) == 1
    manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert manifest["schema_version_before"] == 0
    assert manifest["schema_version_after"] == SCHEMA_VERSION
    assert manifest["config_backup"]
    assert (backup_dir / manifest["config_backup"]).read_text(encoding="utf-8") == config.read_text(
        encoding="utf-8"
    )
    assert verify_database(backups[0]) == "ok"
    assert _user_version(database) == SCHEMA_VERSION
    assert _counts(database) == before


def test_failed_migration_rolls_back_and_keeps_backup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = tmp_path / "failed-migration.sqlite3"
    _create_legacy_v2_copy(database)
    original_hash = hashlib.sha256(database.read_bytes()).hexdigest()

    def fail_migration(*_: object) -> None:
        raise RuntimeError("injected migration failure")

    monkeypatch.setattr(StorageService, "_ensure_column", fail_migration)
    with pytest.raises(RuntimeError, match="injected migration failure"):
        StorageService(database)

    assert hashlib.sha256(database.read_bytes()).hexdigest() == original_hash
    assert _user_version(database) == 0
    assert verify_database(database) == "ok"
    assert len(list((tmp_path / "backups").glob("*.sqlite3"))) == 1


def test_restore_requires_explicit_destination_and_preserves_counts(tmp_path: Path) -> None:
    source = tmp_path / "source.sqlite3"
    _create_legacy_v2_copy(source)
    backup = backup_database(source, tmp_path / "manual-backups", schema_version=0)
    destination = tmp_path / "restored.sqlite3"

    assert verify_database(backup.database_path) == "ok"
    assert not destination.exists()
    restore_database(backup.database_path, destination)

    assert verify_database(destination) == "ok"
    assert _counts(destination) == _counts(source)
