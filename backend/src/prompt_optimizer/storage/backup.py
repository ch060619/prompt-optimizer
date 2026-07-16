from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

# RC ID: RC-053. Provide verified SQLite backup and explicit restore primitives.


@dataclass(frozen=True)
class BackupResult:
    database_path: Path
    manifest_path: Path
    config_path: Path | None
    manifest: dict[str, Any]


def read_schema_version(database_path: Path) -> int:
    with _read_only_connection(database_path) as connection:
        return int(connection.execute("PRAGMA user_version").fetchone()[0])


def verify_database(database_path: Path) -> str:
    with _read_only_connection(database_path) as connection:
        result = connection.execute("PRAGMA integrity_check").fetchone()
    if result is None or result[0] != "ok":
        raise RuntimeError(f"SQLite 完整性检查失败：{database_path}")
    return "ok"


def backup_database(
    source: Path,
    destination_dir: Path,
    *,
    schema_version: int,
    target_schema_version: int | None = None,
    config_path: Path | None = None,
) -> BackupResult:
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    verify_database(source)
    destination_dir.mkdir(parents=True, exist_ok=True)
    target_version = target_schema_version if target_schema_version is not None else schema_version
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    stem = f"{source.stem}-pre-v{schema_version}-to-v{target_version}-{stamp}"
    database_path = destination_dir / f"{stem}.sqlite3"
    manifest_path = destination_dir / f"{stem}.json"

    with _read_only_connection(source) as source_connection:
        destination_connection = sqlite3.connect(database_path)
        try:
            source_connection.backup(destination_connection)
        finally:
            destination_connection.close()
    verify_database(database_path)

    config_backup: Path | None = None
    if config_path is not None and config_path.is_file():
        config_backup = destination_dir / f"{stem}-config{config_path.suffix}"
        shutil.copy2(config_path, config_backup)

    manifest: dict[str, Any] = {
        "created_at": datetime.now(UTC).isoformat(),
        "source_database": os.fspath(source),
        "database_backup": database_path.name,
        "database_sha256": _sha256(database_path),
        "schema_version_before": schema_version,
        "schema_version_after": target_version,
        "config_source": os.fspath(config_path) if config_path is not None else None,
        "config_backup": config_backup.name if config_backup is not None else None,
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return BackupResult(database_path, manifest_path, config_backup, manifest)


def restore_database(
    backup_path: Path,
    destination: Path,
    *,
    overwrite: bool = False,
    config_backup: Path | None = None,
    config_destination: Path | None = None,
) -> None:
    backup_path = backup_path.resolve()
    destination = destination.resolve()
    verify_database(backup_path)
    if destination.exists() and not overwrite:
        raise FileExistsError(f"恢复目标已存在：{destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.stem}-restore-",
        suffix=destination.suffix,
        dir=destination.parent,
    )
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        with _read_only_connection(backup_path) as source_connection:
            destination_connection = sqlite3.connect(temporary)
            try:
                source_connection.backup(destination_connection)
            finally:
                destination_connection.close()
        verify_database(temporary)
        os.replace(temporary, destination)
        if config_backup is not None and config_destination is not None:
            config_destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(config_backup, config_destination)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def _read_only_connection(database_path: Path) -> Iterator[sqlite3.Connection]:
    database_path = database_path.resolve()
    if not database_path.is_file():
        raise FileNotFoundError(database_path)
    normalized = database_path.as_posix()
    uri = f"file:{quote(normalized, safe='/:')}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        yield connection
    finally:
        connection.close()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
