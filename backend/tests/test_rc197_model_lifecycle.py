from __future__ import annotations

import hashlib

import pytest
from fastapi.testclient import TestClient

from prompt_optimizer.api.app import create_app
from prompt_optimizer.model_lifecycle import (
    ModelDirectoryError,
    ModelDirectoryService,
)

# RC ID: RC-197. Verify directory selection, migration safety, version recovery, and cleanup.


def digest(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def install(service: ModelDirectoryService, source, version: str):
    return service.install_version(
        model_id="gemma-3-1b-it",
        source=source,
        version=version,
        checksum=digest(source),
    )


def test_directory_check_reports_space_and_write_access(tmp_path) -> None:
    service = ModelDirectoryService(tmp_path / "registry.json", tmp_path / "models")

    report = service.check_directory(tmp_path / "custom", required_bytes=128)

    assert report.path == str((tmp_path / "custom").resolve())
    assert report.writable is True
    assert report.free_bytes >= 128
    assert report.sufficient is True


def test_migration_verifies_then_switches_and_keeps_source_on_interruption(tmp_path) -> None:
    source = tmp_path / "source.bin"
    source.write_bytes(b"stable model" * 100)
    service = ModelDirectoryService(tmp_path / "registry.json", tmp_path / "models")
    install(service, source, "v1")
    old_root = service.root
    destination = tmp_path / "custom-models"

    def interrupt(_copied: int, _total: int) -> None:
        raise RuntimeError("migration interrupted")

    with pytest.raises(ModelDirectoryError, match="interrupted"):
        service.migrate_directory(destination, progress=interrupt)

    assert service.root == old_root
    assert (old_root / "gemma-3-1b-it" / "versions" / "v1" / "model.bin").is_file()
    assert not (destination / "gemma-3-1b-it" / "versions" / "v1" / "model.bin").exists()

    result = service.migrate_directory(destination)
    assert result.switched is True
    assert service.root == destination.resolve()
    assert (
        destination / "gemma-3-1b-it" / "versions" / "v1" / "model.bin"
    ).read_bytes() == source.read_bytes()
    assert not old_root.exists()


def test_update_retains_previous_version_and_rollback_repairs_corruption(tmp_path) -> None:
    first = tmp_path / "first.bin"
    second = tmp_path / "second.bin"
    first.write_bytes(b"version one")
    second.write_bytes(b"version two")
    service = ModelDirectoryService(tmp_path / "registry.json", tmp_path / "models")

    install(service, first, "v1")
    install(service, second, "v2")
    assert service.active_version("gemma-3-1b-it") == "v2"
    assert service.rollback("gemma-3-1b-it", "v1").active_version == "v1"

    active = service.active_path("gemma-3-1b-it")
    active.write_bytes(b"tampered")
    repaired = service.repair("gemma-3-1b-it", source=first)
    assert repaired.repaired is True
    assert active.read_bytes() == first.read_bytes()


def test_cleanup_prunes_registered_old_versions_but_uninstall_leaves_unregistered_files(
    tmp_path,
) -> None:
    first = tmp_path / "first.bin"
    second = tmp_path / "second.bin"
    first.write_bytes(b"version one")
    second.write_bytes(b"version two")
    service = ModelDirectoryService(tmp_path / "registry.json", tmp_path / "models")
    install(service, first, "v1")
    install(service, second, "v2")
    extra = service.root / "gemma-3-1b-it" / "notes.txt"
    extra.write_text("keep", encoding="utf-8")

    cleanup = service.cleanup("gemma-3-1b-it")
    assert cleanup.deleted_versions == ("v1",)
    assert not (service.root / "gemma-3-1b-it" / "versions" / "v1").exists()
    assert (service.root / "gemma-3-1b-it" / "versions" / "v2" / "model.bin").exists()

    result = service.uninstall("gemma-3-1b-it")
    assert result.deleted is True
    assert extra.is_file()
    assert not (service.root / "gemma-3-1b-it" / "versions" / "v2" / "model.bin").exists()
    assert result.history_preserved is True


def test_invalid_directory_and_unknown_rollback_are_rejected(tmp_path) -> None:
    service = ModelDirectoryService(tmp_path / "registry.json", tmp_path / "models")
    (tmp_path / "file.txt").write_text("not a directory", encoding="utf-8")
    with pytest.raises(ModelDirectoryError, match="directory"):
        service.check_directory(tmp_path / "file.txt", required_bytes=0)
    with pytest.raises(ModelDirectoryError, match="unknown model"):
        service.rollback("gemma-3-1b-it", "missing")


def test_api_exposes_directory_migration_and_registered_uninstall(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("RABBIT_CODE_HOME", str(tmp_path / "data"))
    source = tmp_path / "source.bin"
    source.write_bytes(b"api model")
    checksum = digest(source)
    client = TestClient(create_app())

    checked = client.post(
        "/api/v1/local-models/directory/check",
        json={"path": str(tmp_path / "custom"), "required_bytes": 1},
    )
    assert checked.status_code == 200
    assert checked.json()["sufficient"] is True

    installed = client.post(
        "/api/v1/local-models/gemma-3-1b-it/versions",
        json={"source": str(source), "version": "v1", "checksum": checksum},
    )
    assert installed.status_code == 200
    extra = tmp_path / "data" / "local-models" / "gemma-3-1b-it" / "notes.txt"
    extra.write_text("history", encoding="utf-8")

    migrated = client.post(
        "/api/v1/local-models/directory/migrate",
        json={"destination": str(tmp_path / "migrated")},
    )
    assert migrated.status_code == 200
    assert migrated.json()["switched"] is True

    uninstalled = client.delete("/api/v1/local-models/gemma-3-1b-it/registered")
    assert uninstalled.status_code == 200
    assert uninstalled.json()["history_preserved"] is True
