from __future__ import annotations

import hashlib
import os
import re
import urllib.parse
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

# RC ID: RC-209. Verify versioned downloaded artifacts before atomic installation.


class ArtifactVerificationError(ValueError):
    """Raised when a downloaded artifact cannot pass its manifest policy."""


class ArtifactDownloadError(RuntimeError):
    """Raised when an artifact cannot be fetched or promoted safely."""


@dataclass(frozen=True)
class ArtifactManifest:
    kind: str
    name: str
    version: str
    source_url: str
    sha256: str
    license_id: str
    license_url: str
    license_version: str
    license_summary: str

    def __post_init__(self) -> None:
        if self.kind not in {"binary", "model", "update", "plugin"}:
            raise ArtifactVerificationError("artifact kind is unsupported")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,127}", self.name):
            raise ArtifactVerificationError("artifact name is invalid")
        if ".." in self.name or "//" in self.name:
            raise ArtifactVerificationError("artifact name contains an unsafe path")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,127}", self.version):
            raise ArtifactVerificationError("artifact version is invalid")
        _validate_https_url(self.source_url, "artifact source")
        _validate_https_url(self.license_url, "artifact license")
        if not re.fullmatch(r"[0-9a-f]{64}", self.sha256.lower()):
            raise ArtifactVerificationError("artifact sha256 is invalid")
        for value, field in (
            (self.license_id, "license id"),
            (self.license_version, "license version"),
            (self.license_summary, "license summary"),
        ):
            if not value.strip():
                raise ArtifactVerificationError(f"{field} is required")
        object.__setattr__(self, "sha256", self.sha256.lower())

    def as_mapping(self) -> dict[str, str]:
        return {
            "kind": self.kind,
            "name": self.name,
            "version": self.version,
            "source_url": self.source_url,
            "sha256": self.sha256,
            "license_id": self.license_id,
            "license_url": self.license_url,
            "license_version": self.license_version,
            "license_summary": self.license_summary,
        }

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> ArtifactManifest:
        fields = (
            "kind",
            "name",
            "version",
            "source_url",
            "sha256",
            "license_id",
            "license_url",
            "license_version",
            "license_summary",
        )
        values: dict[str, str] = {}
        for field in fields:
            value = payload.get(field)
            if not isinstance(value, str):
                raise ArtifactVerificationError(f"artifact manifest field is invalid: {field}")
            values[field] = value
        return cls(**values)

    def require_license_confirmation(
        self,
        *,
        accepted: bool,
        confirmation_version: str | None,
    ) -> None:
        if not accepted:
            raise ArtifactVerificationError("artifact license must be accepted before download")
        if confirmation_version != self.license_version:
            raise ArtifactVerificationError("artifact license confirmation does not match")


@dataclass(frozen=True)
class ArtifactVerificationResult:
    manifest: ArtifactManifest
    size_bytes: int


SourceFetcher = Callable[[str], bytes]


class ArtifactDownloader:
    def __init__(self, root: Path) -> None:
        self.root = root.expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def download(
        self,
        manifest: ArtifactManifest,
        *,
        destination: Path,
        fetch: SourceFetcher,
        license_accepted: bool,
        license_confirmation_version: str | None,
    ) -> ArtifactVerificationResult:
        manifest.require_license_confirmation(
            accepted=license_accepted,
            confirmation_version=license_confirmation_version,
        )
        target = destination.expanduser().resolve()
        self._within_root(target)
        if target.exists() and target.is_symlink():
            raise ArtifactDownloadError("artifact destination must not be a symlink")
        temporary = target.with_name(f".{target.name}.{uuid4().hex}.part")
        try:
            payload = fetch(manifest.source_url)
            if not isinstance(payload, bytes):
                raise ArtifactDownloadError("artifact fetcher must return bytes")
            temporary.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_bytes(payload)
            result = self.verify(
                manifest,
                temporary,
                license_accepted=license_accepted,
                license_confirmation_version=license_confirmation_version,
            )
            os.replace(temporary, target)
            return result
        except ArtifactVerificationError:
            _discard(temporary)
            raise
        except (OSError, TimeoutError, ArtifactDownloadError) as exc:
            _discard(temporary)
            if isinstance(exc, ArtifactDownloadError):
                raise
            raise ArtifactDownloadError(f"artifact download failed: {exc}") from exc

    def verify(
        self,
        manifest: ArtifactManifest,
        temporary: Path,
        *,
        license_accepted: bool,
        license_confirmation_version: str | None,
    ) -> ArtifactVerificationResult:
        try:
            manifest.require_license_confirmation(
                accepted=license_accepted,
                confirmation_version=license_confirmation_version,
            )
            if not temporary.is_file() or temporary.is_symlink():
                raise ArtifactVerificationError("artifact temporary file is missing or unsafe")
            actual = _sha256(temporary)
            if actual != manifest.sha256:
                raise ArtifactVerificationError("artifact sha256 does not match manifest")
            return ArtifactVerificationResult(manifest, temporary.stat().st_size)
        except Exception:
            _discard(temporary)
            raise

    def _within_root(self, path: Path) -> None:
        try:
            path.relative_to(self.root)
        except ValueError as exc:
            raise ArtifactDownloadError("artifact destination escapes downloader root") from exc


def _validate_https_url(value: str, field: str) -> None:
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ArtifactVerificationError(f"{field} must use HTTPS")
    if parsed.username or parsed.password:
        raise ArtifactVerificationError(f"{field} must not contain credentials")


def _discard(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
