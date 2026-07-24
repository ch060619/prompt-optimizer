from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from prompt_optimizer.auth.service import AuthService
from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.storage.migrations import MigrationError, SQLiteMigrationRunner
from prompt_optimizer.storage.service import StorageService

# RC ID: RC-214. Verify migration locking, transactions, indexes, backup, and integrity gates.


def test_storage_applies_v2_migration_and_indexes(tmp_path: Path) -> None:
    database = tmp_path / "storage.sqlite3"
    storage = StorageService(database)

    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 2
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert connection.execute(
            "SELECT version FROM schema_migrations WHERE version = 2"
        ).fetchone() == (2,)
        indexes = {
            row[1]
            for row in connection.execute("PRAGMA index_list(prompt_versions)")
        }
    with storage._connect() as connection:
        assert connection.execute("PRAGMA synchronous").fetchone()[0] == 1
    assert "prompt_versions_owner_created" in indexes


def test_migration_runner_serializes_concurrent_apply(tmp_path: Path) -> None:
    database = tmp_path / "concurrent-migrations.sqlite3"

    def apply(_: int) -> int:
        return SQLiteMigrationRunner().apply(database)

    with ThreadPoolExecutor(max_workers=4) as executor:
        versions = list(executor.map(apply, range(4)))

    assert versions == [2, 2, 2, 2]
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 1


def test_migration_failure_rolls_back_the_script(tmp_path: Path) -> None:
    migrations = tmp_path / "migrations"
    migrations.mkdir()
    (migrations / "0002_broken.sql").write_text(
        "PRAGMA foreign_keys = ON;\n"
        "BEGIN IMMEDIATE;\n"
        "CREATE TABLE partial (id INTEGER PRIMARY KEY);\n"
        "THIS IS NOT SQL;\n"
        "COMMIT;\n",
        encoding="utf-8",
    )
    database = tmp_path / "failed.sqlite3"

    with pytest.raises(MigrationError, match="migration 2 failed"):
        SQLiteMigrationRunner(migrations).apply(database)

    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 0
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE name = 'partial'"
        ).fetchone() is None


def test_composite_version_write_rolls_back_implicit_project(tmp_path: Path) -> None:
    database = tmp_path / "atomic.sqlite3"
    storage = StorageService(database)
    user = storage.create_user("atomic-user", AuthService().hash_password("secret123"))
    with sqlite3.connect(database) as connection:
        connection.execute("DELETE FROM project_spaces WHERE owner_id = ?", (user.id,))
        connection.execute(
            """
            CREATE TRIGGER fail_prompt_version
            BEFORE INSERT ON prompt_versions
            BEGIN
                SELECT RAISE(ABORT, 'injected version failure');
            END
            """
        )

    with pytest.raises(sqlite3.IntegrityError, match="injected version failure"):
        storage.save_version(
            "original",
            "optimized",
            Analyzer().analyze("目标：写一个摘要。输出格式：列表。"),
            owner_id=user.id,
        )

    with sqlite3.connect(database) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM project_spaces WHERE owner_id = ?", (user.id,)
        ).fetchone()[0] == 0


def test_corrupt_database_is_rejected_before_startup(tmp_path: Path) -> None:
    database = tmp_path / "corrupt.sqlite3"
    database.write_bytes(b"not a sqlite database")

    with pytest.raises(sqlite3.DatabaseError):
        StorageService(database)
