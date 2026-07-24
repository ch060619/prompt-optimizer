from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from prompt_optimizer.api.app import create_app
from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.retention import (
    RetentionError,
    RetentionPolicy,
    RetentionService,
)
from prompt_optimizer.services import AppServices
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService


def _old_timestamp() -> str:
    return "2020-01-01T00:00:00+00:00"


def test_policy_rejects_unsafe_limits_and_exposes_defaults() -> None:
    policy = RetentionPolicy()

    assert policy.display() == {
        "log_level": "info",
        "max_log_file_bytes": 5 * 1024 * 1024,
        "max_log_total_bytes": 50 * 1024 * 1024,
        "cache_max_bytes": 100 * 1024 * 1024,
        "session_retention_days": 30,
        "prompt_history_retention_days": 365,
        "prompt_history_max_entries": 500,
    }
    with pytest.raises(ValueError):
        RetentionPolicy(max_log_file_bytes=20, max_log_total_bytes=10)


def test_preview_and_apply_rotate_bounded_files_without_touching_other_data(tmp_path: Path) -> None:
    storage = StorageService(tmp_path / "rabbit-code.sqlite3")
    logs = storage.file_store.category_path("logs")
    cache = storage.file_store.category_path("cache")
    attachments = storage.file_store.category_path("attachments")
    models = storage.file_store.category_path("models")
    logs.mkdir(parents=True)
    cache.mkdir(parents=True)
    attachments.mkdir(parents=True)
    models.mkdir(parents=True)
    oversized_log = logs / "app.jsonl"
    oversized_log.write_bytes(b"123456")
    old_log = logs / "old.jsonl"
    old_log.write_bytes(b"1234")
    old_cache = cache / "old.bin"
    old_cache.write_bytes(b"cache-old")
    retained_cache = cache / "retained.bin"
    retained_cache.write_bytes(b"cache-new")
    attachment = attachments / "source.txt"
    attachment.write_text("do not delete", encoding="utf-8")
    model = models / "weights.bin"
    model.write_bytes(b"model")

    storage.create_task(task_id="finished", owner_id=1, kind="optimize", input_json={})
    storage.create_task(task_id="running", owner_id=1, kind="optimize", input_json={})
    storage.update_task("finished", 1, status="succeeded")
    with sqlite3.connect(storage.db_path) as connection:
        connection.execute("UPDATE tasks SET updated_at = ?", (_old_timestamp(),))
    version_id = storage.save_version(
        "original",
        "optimized",
        Analyzer().analyze("优化提示词"),
        owner_id=1,
    )
    with sqlite3.connect(storage.db_path) as connection:
        connection.execute(
            "UPDATE prompt_versions SET created_at = ? WHERE id = ?",
            (_old_timestamp(), version_id),
        )

    policy = RetentionPolicy(
        max_log_file_bytes=5,
        max_log_total_bytes=5,
        cache_max_bytes=8,
        session_retention_days=30,
        prompt_history_retention_days=30,
        prompt_history_max_entries=500,
    )
    service = RetentionService(storage)
    now = datetime(2026, 1, 1, tzinfo=UTC)
    plan = service.preview(policy=policy, now=now)

    assert oversized_log in plan.rotate_log_paths
    assert old_log in plan.delete_log_paths
    assert old_cache in plan.delete_cache_paths
    assert "finished" in plan.delete_task_ids
    assert "running" not in plan.delete_task_ids
    assert version_id in plan.delete_history_ids
    assert attachment.exists() and model.exists()
    assert service.apply(confirm=False, policy=policy, now=now).cancelled is True
    assert oversized_log.exists() and old_cache.exists()

    result = service.apply(confirm=True, policy=policy, now=now)

    assert result.cancelled is False
    assert not oversized_log.exists()
    assert list(logs.glob("app.jsonl.*"))
    assert not old_log.exists() and not old_cache.exists()
    assert attachment.exists() and model.exists()
    with sqlite3.connect(storage.db_path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM tasks WHERE id = 'finished'"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM tasks WHERE id = 'running'"
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM prompt_versions WHERE id = ?", (version_id,)
        ).fetchone()[0] == 0


def test_running_process_blocks_retention_mutation(tmp_path: Path) -> None:
    storage = StorageService(tmp_path / "rabbit-code.sqlite3")
    cache = storage.file_store.category_path("cache")
    cache.mkdir(parents=True)
    target = cache / "keep.bin"
    target.write_bytes(b"keep")
    service = RetentionService(storage, process_guard=lambda: False)

    with pytest.raises(RetentionError):
        service.apply(confirm=True, policy=RetentionPolicy(cache_max_bytes=1))
    assert target.exists()


def test_retention_api_preview_and_cancel_are_non_destructive(tmp_path: Path) -> None:
    services = AppServices(versions=VersionService(StorageService(tmp_path / "api.sqlite3")))
    with TestClient(create_app(services)) as client:
        preview = client.get("/api/v1/data/retention/preview")
        cancelled = client.post("/api/v1/data/retention", json={"confirm": False})

    assert preview.status_code == 200
    assert preview.json()["policy"]["max_log_file_bytes"] == 5 * 1024 * 1024
    assert cancelled.status_code == 200
    assert cancelled.json()["cancelled"] is True
