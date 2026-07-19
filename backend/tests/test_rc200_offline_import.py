from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from prompt_optimizer.offline_import import (
    OfflineImportError,
    OfflineModelImporter,
    model_filename,
)
from prompt_optimizer.providers.runners import InMemoryRunnerAdapter

# RC ID: RC-200. Verify offline media validation and manual import without network access.


def build_media(tmp_path: Path, *, content: bytes = b"offline model") -> tuple[Path, str]:
    source_manifest = yaml.safe_load(
        (Path(__file__).parents[2] / "data/models/manifest.yml").read_text(encoding="utf-8")
    )
    model = source_manifest["models"][0]
    model["model_id"] = "offline/test-model"
    model["revision"] = "a" * 40
    model["file_sha256"] = hashlib.sha256(content).hexdigest()
    model["disk_bytes"] = 1
    model["ram_bytes"] = 1
    model["vram_bytes"] = 1
    package = tmp_path / "media"
    (package / "models").mkdir(parents=True)
    (package / "dependencies").mkdir()
    (package / "manifest.yml").write_text(
        yaml.safe_dump(source_manifest, sort_keys=False), encoding="utf-8"
    )
    model_path = package / "models" / model_filename(model["model_id"], model["quantization"])
    model_path.write_bytes(content)
    return package, model["model_id"]


def test_offline_import_validates_media_and_runs_the_existing_health_contract(
    tmp_path: Path,
) -> None:
    package, model_id = build_media(tmp_path)
    runner = InMemoryRunnerAdapter("ollama")
    importer = OfflineModelImporter(
        tmp_path / "models",
        runner=runner,
        disk_usage=lambda _path: (100, 1, 99),
        resource_probe=lambda: 1,
    )

    result = importer.import_package(
        package,
        model_id=model_id,
        license_accepted=True,
        license_confirmation_version="LicenseRef-Gemma-Terms",
    )

    assert result.ready is True
    assert result.version == "a" * 40
    assert result.health_report is not None
    assert result.health_report["ready"] is True
    assert Path(result.installed_path).is_file()


def test_offline_import_rejects_tampering_before_target_write(tmp_path: Path) -> None:
    package, model_id = build_media(tmp_path)
    model_file = next((package / "models").iterdir())
    model_file.write_bytes(b"tampered")
    target = tmp_path / "models"
    importer = OfflineModelImporter(target, disk_usage=lambda _path: (100, 1, 99))

    with pytest.raises(OfflineImportError, match="checksum"):
        importer.import_package(
            package,
            model_id=model_id,
            license_accepted=True,
            license_confirmation_version="LicenseRef-Gemma-Terms",
        )
    assert not target.exists()


def test_offline_import_rejects_missing_dependencies_license_version_and_disk(
    tmp_path: Path,
) -> None:
    package, model_id = build_media(tmp_path)
    (package / "dependencies").rmdir()
    importer = OfflineModelImporter(tmp_path / "models", disk_usage=lambda _path: (100, 1, 0))

    with pytest.raises(OfflineImportError, match="dependencies"):
        importer.import_package(
            package,
            model_id=model_id,
            license_accepted=True,
            license_confirmation_version="LicenseRef-Gemma-Terms",
        )

    package, model_id = build_media(tmp_path / "second")
    with pytest.raises(OfflineImportError, match="accepted"):
        OfflineModelImporter(tmp_path / "models2").import_package(
            package,
            model_id=model_id,
            license_accepted=False,
            license_confirmation_version=None,
        )

    package, model_id = build_media(tmp_path / "version")
    with pytest.raises(OfflineImportError, match="version"):
        OfflineModelImporter(tmp_path / "models-version").import_package(
            package,
            model_id=model_id,
            license_accepted=True,
            license_confirmation_version="LicenseRef-Gemma-Terms",
            expected_version="b" * 40,
        )

    package, model_id = build_media(tmp_path / "third")
    with pytest.raises(OfflineImportError, match="free space"):
        OfflineModelImporter(
            tmp_path / "models3", disk_usage=lambda _path: (100, 99, 0)
        ).import_package(
            package,
            model_id=model_id,
            license_accepted=True,
            license_confirmation_version="LicenseRef-Gemma-Terms",
        )


def test_offline_import_cli_uses_the_same_contract(tmp_path: Path) -> None:
    package, model_id = build_media(tmp_path)
    repository = Path(__file__).parents[2]
    target = tmp_path / "cli-models"
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        (
            str(repository / "backend" / "src"),
            str(repository / "backend"),
            str(repository / "packages" / "protocol"),
        )
    )
    result = subprocess.run(
        [
            sys.executable,
            "scripts/import-local-model.py",
            str(package),
            "--target-root",
            str(target),
            "--model-id",
            model_id,
            "--accept-license",
            "--license-confirmation-version",
            "LicenseRef-Gemma-Terms",
        ],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["ready"] is True
