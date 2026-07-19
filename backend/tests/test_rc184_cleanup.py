from __future__ import annotations

import json

import pytest

from prompt_optimizer.cleanup import CleanupError, LocalDataCleanupService, migrate_opaque_config
from prompt_optimizer.secrets import MemorySecretStore, new_secret_reference

# RC ID: RC-184. Verify preview, cancel, migration, credential and local-data cleanup.


def test_cleanup_preview_and_cancel_do_not_change_anything(tmp_path) -> None:
    store = MemorySecretStore()
    reference = new_secret_reference()
    store.put(reference, "provider-secret")
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"api_key": reference}), encoding="utf-8")
    database = tmp_path / "rabbit-code.sqlite3"
    database.write_bytes(b"database-secret")
    service = LocalDataCleanupService(
        secret_store=store,
        paths=[config, database],
        config_paths=[config],
    )

    plan = service.preview()
    cancelled = service.clear_all(confirm=False)

    assert plan.display()["credential_count"] == 1
    assert cancelled.cancelled is True
    assert config.exists() and database.exists()
    assert store.get(reference) == "provider-secret"


def test_confirmed_cleanup_removes_opaque_credentials_and_files(tmp_path) -> None:
    store = MemorySecretStore()
    reference = new_secret_reference()
    store.put(reference, "provider-secret")
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"api_key": reference}), encoding="utf-8")
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "trace.log").write_bytes(b"secret-cache")
    service = LocalDataCleanupService(
        secret_store=store,
        paths=[config, cache],
        config_paths=[config],
    )

    result = service.clear_all(confirm=True)

    assert result.cancelled is False
    assert result.deleted_credentials == 1
    assert store.get(reference) is None
    assert not config.exists() and not cache.exists()


def test_cleanup_requires_process_guard_before_mutating(tmp_path) -> None:
    target = tmp_path / "database.sqlite3"
    target.write_text("keep", encoding="utf-8")
    service = LocalDataCleanupService(
        secret_store=MemorySecretStore(),
        paths=[target],
        process_guard=lambda: False,
    )

    with pytest.raises(CleanupError):
        service.clear_all(confirm=True)
    assert target.read_text(encoding="utf-8") == "keep"


def test_config_migration_copies_opaque_reference_and_rejects_plaintext(tmp_path) -> None:
    source = tmp_path / "source.json"
    destination = tmp_path / "migrated" / "config.json"
    reference = new_secret_reference()
    source.write_text(json.dumps({"api_key": reference, "provider": "openai"}), encoding="utf-8")

    migrate_opaque_config(source, destination)

    assert json.loads(destination.read_text(encoding="utf-8"))["api_key"] == reference
    source.write_text(json.dumps({"api_key": "plain-secret"}), encoding="utf-8")
    with pytest.raises(CleanupError):
        migrate_opaque_config(source, destination)
