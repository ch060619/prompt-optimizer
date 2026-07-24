from __future__ import annotations

import sqlite3
from pathlib import Path

# RC ID: RC-214. Apply versioned SQLite migrations with a writer lock.

TARGET_SCHEMA_VERSION = 2
REQUIRED_V2_TABLES = frozenset(
    {
        "schema_migrations",
        "workspaces",
        "sessions",
        "messages",
        "content_blocks",
        "tool_calls",
        "file_snapshots",
        "prompt_versions_v2",
        "provider_references",
        "model_manifests",
        "settings",
    }
)


class MigrationError(RuntimeError):
    """Raised when the database cannot be brought to a supported schema."""


class SQLiteMigrationRunner:
    def __init__(self, migrations_dir: Path | None = None) -> None:
        self.migrations_dir = migrations_dir or Path(__file__).resolve().parents[3] / "migrations"

    def apply(self, database_path: Path, *, target_version: int = TARGET_SCHEMA_VERSION) -> int:
        if target_version < 1:
            raise ValueError("target_version must be positive")
        database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = self._connect(database_path)
        try:
            current_version = self._user_version(connection)
            if current_version > target_version:
                raise MigrationError(
                    f"database version {current_version} is newer than supported {target_version}"
                )
            for version in range(max(current_version + 1, 2), target_version + 1):
                self._apply_one(connection, version)
            final_version = self._user_version(connection)
            if final_version != target_version:
                raise MigrationError(
                    f"migration ended at version {final_version}, expected {target_version}"
                )
            self._assert_required_tables(connection)
            return final_version
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _apply_one(self, connection: sqlite3.Connection, version: int) -> None:
        matches = sorted(self.migrations_dir.glob(f"{version:04d}_*.sql"))
        if len(matches) != 1:
            raise MigrationError(
                f"expected one migration for version {version}, found {len(matches)}"
            )
        script = matches[0].read_text(encoding="utf-8")
        try:
            connection.executescript(script)
        except sqlite3.DatabaseError as error:
            raise MigrationError(f"migration {version} failed: {error}") from error

    @staticmethod
    def _connect(database_path: Path) -> sqlite3.Connection:
        connection = sqlite3.connect(database_path, timeout=30.0)
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA synchronous = NORMAL")
        return connection

    @staticmethod
    def _user_version(connection: sqlite3.Connection) -> int:
        return int(connection.execute("PRAGMA user_version").fetchone()[0])

    @staticmethod
    def _assert_required_tables(connection: sqlite3.Connection) -> None:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        actual = {str(row[0]) for row in rows}
        missing = REQUIRED_V2_TABLES - actual
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise MigrationError(f"schema is missing required tables: {missing_list}")
