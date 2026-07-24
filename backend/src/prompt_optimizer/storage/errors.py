from __future__ import annotations

import sqlite3
from types import TracebackType
from typing import Any, Literal


class StorageError(RuntimeError):
    code = "STORAGE_ERROR"
    retryable = False
    recovery_action = "repair"


class DatabaseLockedError(StorageError):
    code = "DATABASE_LOCKED"
    retryable = True
    recovery_action = "wait_and_retry"


class StorageDiskFullError(StorageError):
    code = "DISK_FULL"
    recovery_action = "free_disk"


def classify_sqlite_error(error: sqlite3.OperationalError) -> StorageError:
    detail = str(error).lower()
    if "locked" in detail or "busy" in detail:
        return DatabaseLockedError("database is locked; wait for the active writer")
    if "full" in detail or "no space" in detail or "disk i/o" in detail:
        return StorageDiskFullError("database storage is full; free disk space")
    return StorageError(f"database operation failed: {error}")


class ResilientSQLiteConnection(sqlite3.Connection):
    def execute(self, sql: str, parameters: Any = ()) -> sqlite3.Cursor:
        try:
            return super().execute(sql, parameters)
        except sqlite3.OperationalError as error:
            raise classify_sqlite_error(error) from error

    def executemany(self, sql: str, parameters: Any) -> sqlite3.Cursor:
        try:
            return super().executemany(sql, parameters)
        except sqlite3.OperationalError as error:
            raise classify_sqlite_error(error) from error

    def executescript(self, sql_script: str) -> sqlite3.Cursor:
        try:
            return super().executescript(sql_script)
        except sqlite3.OperationalError as error:
            raise classify_sqlite_error(error) from error

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        try:
            super().__exit__(exc_type, exc_value, traceback)
        except sqlite3.OperationalError as error:
            raise classify_sqlite_error(error) from error
        return False
