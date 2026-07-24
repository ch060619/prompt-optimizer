from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from backend.rabbit_code.security import (
    EnvironmentVariableDenied,
    SecurityRisk,
    UntrustedPathError,
    classify_command,
    normalize_workspace_path,
    sanitize_environment,
)
from backend.rabbit_code.trust import TrustManifest, TrustRegistry

from prompt_optimizer.artifact_manifest import ArtifactDownloader, ArtifactDownloadError

# RC ID: RC-239. Keep the release threat matrix deterministic and offline.


def test_command_injection_is_classified_before_execution() -> None:
    assert classify_command(("echo", "safe")) is SecurityRisk.SAFE
    assert classify_command(("echo", "value; whoami")) is SecurityRisk.SHELL_SYNTAX


def test_workspace_path_escape_and_symlink_boundary_are_rejected(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    with pytest.raises(UntrustedPathError, match="within the workspace"):
        normalize_workspace_path(root, "../outside")


def test_environment_allowlist_rejects_loader_injection() -> None:
    with pytest.raises(EnvironmentVariableDenied, match="LD_PRELOAD"):
        sanitize_environment({"LD_PRELOAD": "evil.so"})


def test_artifact_destination_escape_is_rejected(tmp_path: Path) -> None:
    downloader = ArtifactDownloader(tmp_path / "artifacts")
    with pytest.raises(ArtifactDownloadError, match="escapes"):
        downloader.download(
            # A destination escape is rejected before the fetcher can run.
            manifest=_artifact_manifest(),
            destination=tmp_path / "outside.bin",
            fetch=lambda _url: b"never fetched",
            license_accepted=True,
            license_confirmation_version="Apache-2.0",
        )


def test_unapproved_trust_permission_is_rejected() -> None:
    registry = TrustRegistry(allowed_sources={"local"}, allowed_permissions={"read"})
    manifest = TrustManifest(
        kind="mcp",
        name="remote-mcp",
        version="1.0.0",
        source="local",
        sha256=hashlib.sha256(b"artifact").hexdigest(),
        permissions=frozenset({"shell"}),
    )
    with pytest.raises(PermissionError, match="permission"):
        registry.register(manifest, explicit_confirmation=True)


def _artifact_manifest():
    from prompt_optimizer.artifact_manifest import ArtifactManifest

    return ArtifactManifest(
        kind="update",
        name="update-artifact",
        version="3.0.0",
        source_url="https://downloads.example.test/update",
        sha256=hashlib.sha256(b"trusted").hexdigest(),
        license_id="Apache-2.0",
        license_url="https://licenses.example.test/apache-2.0",
        license_version="Apache-2.0",
        license_summary="Apache-2.0 terms apply",
    )
