from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.storage.service import StorageService

# RC ID: RC-064. Verify SQLite/file boundaries, atomic writes, and cleanup isolation.


def test_file_store_uses_versioned_categories_and_rejects_escape_keys(tmp_path: Path) -> None:
    storage = StorageService(tmp_path / "boundary.sqlite3")

    storage.file_store.write_text("models", "model.bin", "model-data")
    storage.file_store.write_text("cache", "preview.txt", "cached")

    assert storage.file_store.read_text("models", "model.bin") == "model-data"
    assert storage.file_store.category_path("models").parent.name == "v1"
    with pytest.raises(ValueError):
        storage.file_store.write_text("models", "../outside.bin", "blocked")
    with pytest.raises(ValueError):
        storage.file_store.write_text("sessions", "session.json", "metadata belongs in SQLite")


def test_concurrent_file_writes_leave_a_complete_payload(tmp_path: Path) -> None:
    storage = StorageService(tmp_path / "concurrent-files.sqlite3")
    payloads = [f"payload-{index}" * 100 for index in range(12)]

    def write(payload: str) -> None:
        storage.file_store.write_text("logs", "run.log", payload)

    with ThreadPoolExecutor(max_workers=6) as executor:
        list(executor.map(write, payloads))

    assert storage.file_store.read_text("logs", "run.log") in payloads


def test_crash_during_atomic_replace_preserves_previous_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage = StorageService(tmp_path / "crash-files.sqlite3")
    storage.file_store.write_text("attachments", "report.txt", "before")

    def fail_replace(_: str | Path, __: str | Path) -> None:
        raise OSError("injected replace failure")

    monkeypatch.setattr("prompt_optimizer.storage.files.os.replace", fail_replace)
    with pytest.raises(OSError, match="injected replace failure"):
        storage.file_store.write_text("attachments", "report.txt", "after")

    assert storage.file_store.read_text("attachments", "report.txt") == "before"
    assert not list(storage.file_store.category_path("attachments").glob(".*.tmp"))


def test_concurrent_sqlite_writes_and_cache_cleanup_preserve_metadata(tmp_path: Path) -> None:
    database = tmp_path / "metadata.sqlite3"
    storage = StorageService(database)
    analysis = Analyzer().analyze("目标：并发保存版本。输出格式：列表。")
    storage.file_store.write_text("models", "model.bin", "model-data")
    storage.file_store.write_text("cache", "derived.json", "cached")

    def save(index: int) -> int:
        return storage.save_version(
            f"原始提示词 {index}",
            f"优化提示词 {index}",
            analysis,
            owner_id=1,
        )

    with ThreadPoolExecutor(max_workers=6) as executor:
        version_ids = list(executor.map(save, range(18)))

    storage.file_store.clear_cache()

    with sqlite3.connect(database) as connection:
        count = connection.execute("SELECT COUNT(*) FROM prompt_versions").fetchone()[0]
    assert count == len(version_ids)
    assert storage.get_version(version_ids[0], owner_id=1).id == version_ids[0]
    assert storage.file_store.read_text("models", "model.bin") == "model-data"
    assert not storage.file_store.category_path("cache").exists()
