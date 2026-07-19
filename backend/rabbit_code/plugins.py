from __future__ import annotations

import hashlib
import json
import re
import shutil
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

# RC ID: RC-077. Keep plugin manifests and lifecycle operations behind a controlled registry.


class PluginValidationError(ValueError):
    pass


class PluginStateError(RuntimeError):
    pass


@dataclass(frozen=True)
class PluginManifest:
    name: str
    version: str
    entrypoint: str
    permissions: frozenset[str]
    source: str
    min_app_version: str
    max_app_version: str | None
    artifact: str
    sha256: str

    @classmethod
    def from_file(cls, path: Path) -> PluginManifest:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise PluginValidationError("manifest must be an object")
        try:
            permissions = payload["permissions"]
            if not isinstance(permissions, list) or not all(
                isinstance(item, str) for item in permissions
            ):
                raise TypeError
            return cls(
                name=str(payload["name"]),
                version=str(payload["version"]),
                entrypoint=str(payload["entrypoint"]),
                permissions=frozenset(permissions),
                source=str(payload["source"]),
                min_app_version=str(payload.get("min_app_version", "0.0.0")),
                max_app_version=(
                    str(payload["max_app_version"])
                    if payload.get("max_app_version") is not None
                    else None
                ),
                artifact=str(payload["artifact"]),
                sha256=str(payload["sha256"]).lower(),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise PluginValidationError("manifest fields are invalid") from exc

    def as_mapping(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "entrypoint": self.entrypoint,
            "permissions": sorted(self.permissions),
            "source": self.source,
            "min_app_version": self.min_app_version,
            "max_app_version": self.max_app_version,
            "artifact": self.artifact,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class PluginContext:
    plugin_name: str
    plugin_version: str
    payload: Mapping[str, Any]
    permissions: frozenset[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))


@dataclass(frozen=True)
class PluginRecord:
    manifest: PluginManifest
    directory: Path
    enabled: bool = False
    locked: bool = False


@dataclass(frozen=True)
class PluginAudit:
    sequence: int
    plugin_name: str
    action: str
    version: str


PluginHandler = Callable[[PluginContext], Any]


class PluginRegistry:
    def __init__(
        self,
        root: Path,
        *,
        handlers: Mapping[str, PluginHandler] | None = None,
        allowed_sources: set[str] | frozenset[str] | None = None,
        allowed_permissions: set[str] | frozenset[str] | None = None,
        app_version: str = "3.0.0",
    ) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.handlers = dict(handlers or {})
        self.allowed_sources = frozenset(allowed_sources or {"local"})
        self.allowed_permissions = frozenset(allowed_permissions or {"read"})
        self.app_version = app_version
        self._records: dict[str, PluginRecord] = {}
        self._audit: list[PluginAudit] = []
        self._load_state()

    @property
    def audit(self) -> tuple[PluginAudit, ...]:
        return tuple(self._audit)

    def list_plugins(self) -> tuple[PluginRecord, ...]:
        return tuple(self._records[name] for name in sorted(self._records))

    def get(self, name: str) -> PluginRecord:
        try:
            return self._records[name]
        except KeyError as exc:
            raise PluginStateError(f"plugin is not installed: {name}") from exc

    def install(self, package: Path) -> PluginRecord:
        manifest, source_dir, artifact = self._validate_package(package)
        if manifest.name in self._records:
            raise PluginStateError(f"plugin is already installed: {manifest.name}")
        destination = self._destination(manifest)
        if destination.exists():
            raise PluginStateError("plugin destination already exists")
        shutil.copytree(source_dir, destination)
        record = PluginRecord(manifest, destination, False)
        self._records[manifest.name] = record
        self._record(record, "installed")
        self._persist()
        del artifact
        return record

    def upgrade(self, package: Path) -> PluginRecord:
        manifest, source_dir, artifact = self._validate_package(package)
        current = self.get(manifest.name)
        if current.locked:
            raise PluginStateError("locked plugin requires explicit unlock before upgrade")
        if _version_key(manifest.version) <= _version_key(current.manifest.version):
            raise PluginValidationError("upgrade version must be newer")
        destination = self._destination(manifest)
        if destination.exists():
            raise PluginStateError("plugin upgrade destination already exists")
        shutil.copytree(source_dir, destination)
        shutil.rmtree(current.directory)
        record = PluginRecord(manifest, destination, current.enabled, False)
        self._records[manifest.name] = record
        self._record(record, "upgraded")
        self._persist()
        del artifact
        return record

    def enable(self, name: str) -> PluginRecord:
        record = self.get(name)
        self._verify_artifact(record)
        if record.manifest.entrypoint not in self.handlers:
            raise PluginStateError(
                f"plugin entrypoint is not registered: {record.manifest.entrypoint}"
            )
        updated = PluginRecord(record.manifest, record.directory, True, record.locked)
        self._records[name] = updated
        self._record(updated, "enabled")
        self._persist()
        return updated

    def disable(self, name: str) -> PluginRecord:
        record = self.get(name)
        updated = PluginRecord(record.manifest, record.directory, False, record.locked)
        self._records[name] = updated
        self._record(updated, "disabled")
        self._persist()
        return updated

    def lock(self, name: str) -> PluginRecord:
        record = self.get(name)
        updated = PluginRecord(record.manifest, record.directory, record.enabled, True)
        self._records[name] = updated
        self._record(updated, "locked")
        self._persist()
        return updated

    def unlock(self, name: str, *, explicit_confirmation: bool = False) -> PluginRecord:
        if not explicit_confirmation:
            raise PluginStateError("plugin unlock requires explicit confirmation")
        record = self.get(name)
        updated = PluginRecord(record.manifest, record.directory, record.enabled, False)
        self._records[name] = updated
        self._record(updated, "unlocked")
        self._persist()
        return updated

    def uninstall(self, name: str) -> None:
        record = self.get(name)
        self._within_root(record.directory)
        shutil.rmtree(record.directory)
        parent = record.directory.parent
        if parent != self.root and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
        del self._records[name]
        self._audit.append(
            PluginAudit(
                len(self._audit),
                record.manifest.name,
                "uninstalled",
                record.manifest.version,
            )
        )
        self._persist()

    def execute(self, name: str, payload: Mapping[str, Any]) -> Any:
        record = self.get(name)
        if not record.enabled:
            raise PluginStateError(f"plugin is disabled: {name}")
        self._verify_artifact(record)
        try:
            handler = self.handlers[record.manifest.entrypoint]
        except KeyError as exc:
            raise PluginStateError("plugin entrypoint is not registered") from exc
        context = PluginContext(
            record.manifest.name,
            record.manifest.version,
            payload,
            record.manifest.permissions,
        )
        return handler(context)

    def _validate_package(self, package: Path) -> tuple[PluginManifest, Path, Path]:
        source_dir = package.resolve()
        if not source_dir.is_dir():
            raise PluginValidationError("plugin package directory is required")
        manifest = PluginManifest.from_file(source_dir / "manifest.json")
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", manifest.name):
            raise PluginValidationError("plugin name is invalid")
        for value in (manifest.version, manifest.min_app_version, manifest.max_app_version):
            if value is not None and not re.fullmatch(r"\d+\.\d+\.\d+", value):
                raise PluginValidationError("plugin version is invalid")
        if manifest.source not in self.allowed_sources:
            raise PluginValidationError("plugin source is not allowed")
        if not manifest.permissions <= self.allowed_permissions:
            raise PluginValidationError("plugin permission is not allowed")
        app_version = _version_key(self.app_version)
        if app_version < _version_key(manifest.min_app_version) or (
            manifest.max_app_version is not None
            and app_version > _version_key(manifest.max_app_version)
        ):
            raise PluginValidationError("plugin is not compatible with this application")
        artifact = (source_dir / manifest.artifact).resolve()
        try:
            artifact.relative_to(source_dir)
        except ValueError as exc:
            raise PluginValidationError("plugin artifact escapes package") from exc
        if not artifact.is_file():
            raise PluginValidationError("plugin artifact is missing")
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if digest != manifest.sha256:
            raise PluginValidationError("plugin artifact hash does not match manifest")
        return manifest, source_dir, artifact

    def _destination(self, manifest: PluginManifest) -> Path:
        destination = (self.root / manifest.name / manifest.version).resolve()
        self._within_root(destination)
        return destination

    def _within_root(self, path: Path) -> None:
        try:
            path.relative_to(self.root)
        except ValueError as exc:
            raise PluginStateError("plugin path escapes registry root") from exc

    def _record(self, record: PluginRecord, action: str) -> None:
        self._audit.append(
            PluginAudit(len(self._audit), record.manifest.name, action, record.manifest.version)
        )

    def _verify_artifact(self, record: PluginRecord) -> None:
        artifact = (record.directory / record.manifest.artifact).resolve()
        try:
            artifact.relative_to(record.directory.resolve())
        except ValueError as exc:
            raise PluginStateError("plugin artifact escapes installed directory") from exc
        if not artifact.is_file():
            raise PluginStateError("plugin source artifact is missing; reapproval required")
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if digest != record.manifest.sha256:
            updated = PluginRecord(record.manifest, record.directory, False, record.locked)
            self._records[record.manifest.name] = updated
            self._persist()
            raise PluginStateError("plugin source changed; reapproval required")

    def _persist(self) -> None:
        payload = {
            "plugins": [
                {
                    "manifest": record.manifest.as_mapping(),
                    "directory": str(record.directory.relative_to(self.root)),
                    "enabled": record.enabled,
                    "locked": record.locked,
                }
                for record in self.list_plugins()
            ]
        }
        temporary = self.root / ".registry.json.tmp"
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(self.root / "registry.json")

    def _load_state(self) -> None:
        path = self.root / "registry.json"
        if not path.is_file():
            return
        payload = json.loads(path.read_text(encoding="utf-8"))
        for item in payload.get("plugins", []):
            manifest_payload = item["manifest"]
            permissions = frozenset(manifest_payload["permissions"])
            manifest = PluginManifest(
                name=manifest_payload["name"],
                version=manifest_payload["version"],
                entrypoint=manifest_payload["entrypoint"],
                permissions=permissions,
                source=manifest_payload["source"],
                min_app_version=manifest_payload["min_app_version"],
                max_app_version=manifest_payload.get("max_app_version"),
                artifact=manifest_payload["artifact"],
                sha256=manifest_payload["sha256"],
            )
            directory = (self.root / item["directory"]).resolve()
            self._within_root(directory)
            self._records[manifest.name] = PluginRecord(
                manifest,
                directory,
                bool(item.get("enabled", False)),
                bool(item.get("locked", False)),
            )


def _version_key(value: str) -> tuple[int, int, int]:
    try:
        return tuple(int(part) for part in value.split("."))  # type: ignore[return-value]
    except ValueError as exc:
        raise PluginValidationError("plugin version is invalid") from exc
