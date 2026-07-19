from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from prompt_optimizer.artifact_manifest import (
    ArtifactDownloader,
    ArtifactDownloadError,
    ArtifactManifest,
    ArtifactVerificationError,
)
from prompt_optimizer.model_manifest import ModelManifestError, load_manifest

# RC ID: RC-209. Verify downloaded binary, model, update, and plugin artifacts.


def _manifest(kind: str = "model", *, digest: str | None = None) -> ArtifactManifest:
    return ArtifactManifest(
        kind=kind,
        name=f"{kind}-artifact",
        version="2026.07.19",
        source_url=f"https://downloads.example.test/{kind}/artifact",
        sha256=digest or hashlib.sha256(b"trusted artifact").hexdigest(),
        license_id="Apache-2.0",
        license_url="https://licenses.example.test/apache-2.0",
        license_version="Apache-2.0",
        license_summary="Apache-2.0 terms apply",
    )


@pytest.mark.parametrize("kind", ["binary", "model", "update", "plugin"])
def test_all_downloaded_artifact_kinds_use_versioned_manifest_and_atomic_install(
    tmp_path: Path, kind: str
) -> None:
    manifest = ArtifactManifest.from_mapping(_manifest(kind).as_mapping())
    downloader = ArtifactDownloader(tmp_path / "artifacts")
    seen_urls: list[str] = []

    def fetch(url: str) -> bytes:
        seen_urls.append(url)
        return b"trusted artifact"

    result = downloader.download(
        manifest,
        destination=tmp_path / "artifacts" / kind / "artifact.bin",
        fetch=fetch,
        license_accepted=True,
        license_confirmation_version="Apache-2.0",
    )

    assert result.manifest == manifest
    assert result.size_bytes == len(b"trusted artifact")
    assert seen_urls == [manifest.source_url]
    assert (tmp_path / "artifacts" / kind / "artifact.bin").read_bytes() == b"trusted artifact"
    assert not list((tmp_path / "artifacts").rglob("*.part"))


def test_hash_mismatch_is_fail_closed_and_preserves_existing_destination(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    destination = root / "update.bin"
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"previous trusted version")
    downloader = ArtifactDownloader(root)

    with pytest.raises(ArtifactVerificationError, match="sha256"):
        downloader.download(
            _manifest("update"),
            destination=destination,
            fetch=lambda _url: b"tampered artifact",
            license_accepted=True,
            license_confirmation_version="Apache-2.0",
        )

    assert destination.read_bytes() == b"previous trusted version"
    assert not list(root.rglob("*.part"))


def test_unavailable_https_source_and_missing_license_confirmation_leave_no_temp_file(
    tmp_path: Path,
) -> None:
    downloader = ArtifactDownloader(tmp_path / "artifacts")
    with pytest.raises(ArtifactDownloadError, match="download failed"):
        downloader.download(
            _manifest("binary"),
            destination=tmp_path / "artifacts" / "binary.bin",
            fetch=lambda _url: (_ for _ in ()).throw(OSError("source unavailable")),
            license_accepted=True,
            license_confirmation_version="Apache-2.0",
        )
    with pytest.raises(ArtifactVerificationError, match="license"):
        downloader.download(
            _manifest("plugin"),
            destination=tmp_path / "artifacts" / "plugin.bin",
            fetch=lambda _url: b"trusted artifact",
            license_accepted=False,
            license_confirmation_version=None,
        )
    assert not list((tmp_path / "artifacts").rglob("*.part"))


def test_manifest_rejects_non_https_source_or_license_and_model_manifest_reuses_policy(
    tmp_path: Path,
) -> None:
    with pytest.raises(ArtifactVerificationError, match="HTTPS"):
        ArtifactManifest(
            **{**_manifest("model").as_mapping(), "source_url": "http://insecure.test/a"}
        )
    with pytest.raises(ArtifactVerificationError, match="HTTPS"):
        ArtifactManifest(
            **{**_manifest("model").as_mapping(), "license_url": "http://insecure.test/license"}
        )

    models = load_manifest(Path(__file__).parents[2] / "data/models/manifest.yml")
    assert all(model.to_artifact_manifest().kind == "model" for model in models)
    invalid = (Path(__file__).parents[2] / "data/models/manifest.yml").read_text(
        encoding="utf-8"
    ).replace("license_url: https://", "license_url: http://", 1)
    invalid_path = tmp_path / "manifest.yml"
    invalid_path.write_text(invalid, encoding="utf-8")
    with pytest.raises(ModelManifestError, match="HTTPS"):
        load_manifest(invalid_path)
