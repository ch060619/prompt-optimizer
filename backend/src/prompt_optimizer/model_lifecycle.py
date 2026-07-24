from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import shutil
import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

# RC ID: RC-197. Keep model directories, versions, migrations, and cleanup recoverable.

_SAFE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
ProgressCallback = Callable[[int, int], None]


class ModelDirectoryError(RuntimeError):
    """Raised when a model directory lifecycle operation cannot be completed."""

    code = "MODEL_DIRECTORY_ERROR"
    retryable = False
    recovery_action = "repair"


class DiskSpaceError(ModelDirectoryError):
    code = "DISK_FULL"
    recovery_action = "free_disk"


@dataclass(frozen=True)
class DirectoryReport:
    path: str
    writable: bool
    free_bytes: int
    required_bytes: int
    sufficient: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "writable": self.writable,
            "free_bytes": self.free_bytes,
            "required_bytes": self.required_bytes,
            "sufficient": self.sufficient,
        }


@dataclass(frozen=True)
class VersionOperation:
    model_id: str
    active_version: str
    retained_versions: tuple[str, ...]
    changed: bool = True
    repaired: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "model_id": self.model_id,
            "active_version": self.active_version,
            "retained_versions": list(self.retained_versions),
            "changed": self.changed,
            "repaired": self.repaired,
        }


@dataclass(frozen=True)
class MigrationResult:
    source_root: str
    destination_root: str
    switched: bool
    old_root_removed: bool
    copied_files: int

    def to_dict(self) -> dict[str, object]:
        return {
            "source_root": self.source_root,
            "destination_root": self.destination_root,
            "switched": self.switched,
            "old_root_removed": self.old_root_removed,
            "copied_files": self.copied_files,
        }


@dataclass(frozen=True)
class CleanupResult:
    deleted_versions: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {"deleted_versions": list(self.deleted_versions)}


@dataclass(frozen=True)
class UninstallResult:
    model_id: str
    deleted: bool
    deleted_files: int
    history_preserved: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "model_id": self.model_id,
            "deleted": self.deleted,
            "deleted_files": self.deleted_files,
            "history_preserved": self.history_preserved,
        }


class ModelDirectoryService:
    """Manage only files registered in a small, atomically written model registry."""

    def __init__(self, registry_path: Path, root: Path) -> None:
        self.registry_path = registry_path
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.root = root.expanduser().resolve()
        self._registry = self._load_registry()
        stored_root = self._registry.get("root")
        if isinstance(stored_root, str) and stored_root.strip():
            self.root = Path(stored_root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def check_directory(self, path: Path, *, required_bytes: int = 0) -> DirectoryReport:
        if required_bytes < 0:
            raise ModelDirectoryError("required space must not be negative")
        candidate = path.expanduser().resolve()
        if candidate.exists() and not candidate.is_dir():
            raise ModelDirectoryError("model directory must be a directory")
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / f".rabbit-code-write-{uuid.uuid4().hex}"
            probe.write_bytes(b"")
            probe.unlink()
            writable = True
            free_bytes = shutil.disk_usage(candidate).free
        except OSError as exc:
            writable = False
            try:
                free_bytes = shutil.disk_usage(candidate).free
            except OSError:
                free_bytes = 0
            if not candidate.exists():
                raise ModelDirectoryError(f"cannot access model directory: {candidate}") from exc
        return DirectoryReport(
            path=str(candidate),
            writable=writable,
            free_bytes=free_bytes,
            required_bytes=required_bytes,
            sufficient=writable and free_bytes >= required_bytes,
        )

    def set_directory(self, path: Path, *, required_bytes: int = 0) -> DirectoryReport:
        report = self.check_directory(path, required_bytes=required_bytes)
        if not report.writable:
            raise ModelDirectoryError("model directory is not writable")
        if not report.sufficient:
            raise DiskSpaceError("model directory does not have enough free space")
        self.root = Path(report.path)
        self._registry["root"] = str(self.root)
        self._save_registry()
        return report

    def install_version(
        self,
        *,
        model_id: str,
        source: Path,
        version: str,
        checksum: str,
        retain_versions: int = 2,
    ) -> VersionOperation:
        self._validate_name(model_id, "model id")
        self._validate_name(version, "model version")
        if retain_versions < 1:
            raise ModelDirectoryError("retain_versions must be at least one")
        source = source.expanduser().resolve()
        if not source.is_file() or source.is_symlink():
            raise ModelDirectoryError("model source must be a regular file")
        expected = _normalize_checksum(checksum)
        if _sha256(source) != expected:
            raise ModelDirectoryError("model source checksum mismatch")
        target = self._version_path(model_id, version)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
        try:
            shutil.copy2(source, temporary)
            if _sha256(temporary) != expected:
                raise ModelDirectoryError("copied model checksum mismatch")
            os.replace(temporary, target)
        except OSError as exc:
            if _is_disk_full(exc):
                raise DiskSpaceError("model version install failed: disk is full") from exc
            raise ModelDirectoryError(f"model version install failed: {exc}") from exc
        finally:
            temporary.unlink(missing_ok=True)

        models = self._models()
        existing_record = models.get(model_id)
        if existing_record is None:
            record: dict[str, object] = {"active_version": version, "versions": []}
            models[model_id] = record
        elif isinstance(existing_record, dict):
            record = existing_record
        else:
            raise ModelDirectoryError("model registry record must be an object")
        versions = [item for item in self._version_records(record) if item["version"] != version]
        versions.append(
            {
                "version": version,
                "relative_path": self._relative_path(target),
                "sha256": expected,
                "size_bytes": target.stat().st_size,
            }
        )
        versions.sort(key=lambda item: str(item["version"]))
        keep = versions[-retain_versions:]
        retained_names = {str(item["version"]) for item in keep}
        for item in versions:
            if str(item["version"]) not in retained_names:
                self._remove_registered_file(item)
        record["active_version"] = version
        record["versions"] = keep
        self._save_registry()
        return VersionOperation(model_id, version, tuple(str(item["version"]) for item in keep))

    def active_version(self, model_id: str) -> str:
        record = self._record(model_id)
        active = record.get("active_version")
        if not isinstance(active, str):
            raise ModelDirectoryError("model has no active version")
        return active

    def active_path(self, model_id: str) -> Path:
        version = self.active_version(model_id)
        for item in self._version_records(self._record(model_id)):
            if item["version"] == version:
                return self._path_from_record(item)
        raise ModelDirectoryError("active model version is not registered")

    def rollback(self, model_id: str, version: str) -> VersionOperation:
        self._validate_name(version, "model version")
        record = self._record(model_id)
        item = self._find_version(record, version)
        path = self._path_from_record(item)
        if not self._valid_registered_file(item, path):
            raise ModelDirectoryError("cannot rollback to corrupt version")
        record["active_version"] = version
        self._save_registry()
        return VersionOperation(
            model_id,
            version,
            tuple(str(entry["version"]) for entry in self._version_records(record)),
        )

    def repair(self, model_id: str, *, source: Path | None = None) -> VersionOperation:
        record = self._record(model_id)
        active = self.active_version(model_id)
        active_item = self._find_version(record, active)
        active_path = self._path_from_record(active_item)
        if self._valid_registered_file(active_item, active_path):
            return VersionOperation(
                model_id,
                active,
                tuple(str(entry["version"]) for entry in self._version_records(record)),
                changed=False,
                repaired=False,
            )
        if source is not None:
            installed = self.install_version(
                model_id=model_id,
                source=source,
                version=active,
                checksum=_sha256(source),
                retain_versions=len(self._version_records(record)),
            )
            return VersionOperation(
                installed.model_id,
                installed.active_version,
                installed.retained_versions,
                changed=True,
                repaired=True,
            )
        valid = [
            item
            for item in self._version_records(record)
            if self._valid_registered_file(item, self._path_from_record(item))
        ]
        if not valid:
            raise ModelDirectoryError("no complete registered version is available for repair")
        replacement = max(valid, key=lambda item: str(item["version"]))
        replacement_version = str(replacement["version"])
        record["active_version"] = replacement_version
        self._save_registry()
        return VersionOperation(
            model_id,
            replacement_version,
            tuple(str(entry["version"]) for entry in self._version_records(record)),
            repaired=True,
        )

    def migrate_directory(
        self,
        destination: Path,
        *,
        progress: ProgressCallback | None = None,
    ) -> MigrationResult:
        destination = destination.expanduser().resolve()
        source_root = self.root
        if (
            destination == source_root
            or _is_relative_to(destination, source_root)
            or _is_relative_to(source_root, destination)
        ):
            raise ModelDirectoryError(
                "migration destination must be separate from the current model directory"
            )
        files = tuple(self._registered_files())
        required = sum(path.stat().st_size for _, path in files if path.is_file())
        report = self.check_directory(destination, required_bytes=required)
        if not report.sufficient:
            raise DiskSpaceError("migration destination does not have enough free space")
        if any(destination.iterdir()):
            raise ModelDirectoryError("migration destination must be empty")
        staging = destination.with_name(f".{destination.name}.rabbit-migration-{uuid.uuid4().hex}")
        copied = 0
        total = len(files)
        try:
            for relative, source in files:
                if not source.is_file() or source.is_symlink():
                    raise ModelDirectoryError("registered model file is missing or unsafe")
                target = staging / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
                if _sha256(target) != self._checksum_for(relative):
                    raise ModelDirectoryError("migration checksum mismatch")
                copied += 1
                if progress is not None:
                    progress(copied, total)
            destination.mkdir(parents=True, exist_ok=True)
            for relative, _source in files:
                target = staging / relative
                final = destination / relative
                final.parent.mkdir(parents=True, exist_ok=True)
                os.replace(target, final)
            _remove_tree(staging)
        except Exception as exc:
            _remove_tree(staging)
            if isinstance(exc, ModelDirectoryError):
                raise
            raise ModelDirectoryError(f"migration interrupted: {exc}") from exc

        old_root = source_root
        previous_root = self._registry.get("root")
        self._registry["root"] = str(destination)
        try:
            self._save_registry()
        except Exception:
            self._registry["root"] = previous_root or str(old_root)
            raise
        self.root = destination
        self._remove_registered_from_root(old_root, files)
        return MigrationResult(
            str(old_root),
            str(destination),
            switched=True,
            old_root_removed=not old_root.exists(),
            copied_files=copied,
        )

    def cleanup(self, model_id: str | None = None) -> CleanupResult:
        selected = (model_id,) if model_id is not None else tuple(self._models())
        deleted: list[str] = []
        for current_id in selected:
            record = self._record(current_id)
            active = self.active_version(current_id)
            retained = []
            for item in self._version_records(record):
                version = str(item["version"])
                if version == active:
                    retained.append(item)
                    continue
                self._remove_registered_file(item)
                deleted.append(version)
            record["versions"] = retained
        self._save_registry()
        return CleanupResult(tuple(deleted))

    def uninstall(self, model_id: str) -> UninstallResult:
        record = self._record(model_id)
        deleted_files = 0
        for item in self._version_records(record):
            path = self._path_from_record(item)
            if path.is_file() and not path.is_symlink():
                path.unlink()
                deleted_files += 1
            _remove_empty_parents(path.parent, self.root)
        self._models().pop(model_id, None)
        self._save_registry()
        return UninstallResult(model_id, True, deleted_files, history_preserved=True)

    def snapshot(self) -> dict[str, object]:
        return json.loads(json.dumps(self._registry))

    def _load_registry(self) -> dict[str, object]:
        if not self.registry_path.is_file():
            return {"schema_version": 1, "root": str(self.root), "models": {}}
        try:
            payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ModelDirectoryError(f"invalid model registry: {self.registry_path}") from exc
        if not isinstance(payload, dict) or payload.get("schema_version") != 1:
            raise ModelDirectoryError("model registry schema_version must be 1")
        if not isinstance(payload.get("models"), dict):
            raise ModelDirectoryError("model registry models must be an object")
        return payload

    def _save_registry(self) -> None:
        self._registry["schema_version"] = 1
        stored_root = self._registry.get("root")
        self._registry["root"] = str(self.root if stored_root is None else stored_root)
        temporary = self.registry_path.with_name(
            f".{self.registry_path.name}.{uuid.uuid4().hex}.tmp"
        )
        temporary.write_text(
            json.dumps(self._registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.registry_path)

    def _models(self) -> dict[str, object]:
        models = self._registry.get("models")
        if not isinstance(models, dict):
            raise ModelDirectoryError("model registry models must be an object")
        return models

    def _record(self, model_id: str) -> dict[str, object]:
        self._validate_name(model_id, "model id")
        record = self._models().get(model_id)
        if not isinstance(record, dict):
            raise ModelDirectoryError(f"unknown model: {model_id}")
        return record

    @staticmethod
    def _version_records(record: dict[str, object]) -> list[dict[str, object]]:
        versions = record.get("versions")
        if not isinstance(versions, list) or not all(isinstance(item, dict) for item in versions):
            raise ModelDirectoryError("model registry versions are invalid")
        return versions  # type: ignore[return-value]

    def _find_version(self, record: dict[str, object], version: str) -> dict[str, object]:
        for item in self._version_records(record):
            if item.get("version") == version:
                return item
        raise ModelDirectoryError(f"unknown version: {version}")

    def _version_path(self, model_id: str, version: str) -> Path:
        return self.root / model_id / "versions" / version / "model.bin"

    def _relative_path(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root).as_posix()
        except ValueError as exc:
            raise ModelDirectoryError("registered model path escapes model directory") from exc

    def _path_from_record(self, item: dict[str, object]) -> Path:
        relative = item.get("relative_path")
        if not isinstance(relative, str):
            raise ModelDirectoryError("registered model path is invalid")
        path = (self.root / relative).resolve()
        if not _is_relative_to(path, self.root) or path == self.root:
            raise ModelDirectoryError("registered model path escapes model directory")
        return path

    def _valid_registered_file(self, item: dict[str, object], path: Path) -> bool:
        checksum = item.get("sha256")
        return (
            isinstance(checksum, str)
            and path.is_file()
            and not path.is_symlink()
            and _sha256(path) == checksum
        )

    def _remove_registered_file(self, item: dict[str, object]) -> None:
        path = self._path_from_record(item)
        if path.is_file() and not path.is_symlink():
            path.unlink()
        _remove_empty_parents(path.parent, self.root)

    def _registered_files(self) -> Iterator[tuple[Path, Path]]:
        for record in self._models().values():
            if not isinstance(record, dict):
                raise ModelDirectoryError("model registry record is invalid")
            for item in self._version_records(record):
                path = self._path_from_record(item)
                yield Path(str(item["relative_path"])), path

    def _checksum_for(self, relative: Path) -> str:
        for _model_id, path in self._registered_files():
            if path.relative_to(self.root) == relative:
                for record in self._models().values():
                    if not isinstance(record, dict):
                        continue
                    for item in self._version_records(record):
                        if item.get("relative_path") == relative.as_posix():
                            checksum = item.get("sha256")
                            if isinstance(checksum, str):
                                return checksum
        raise ModelDirectoryError("migration checksum record is missing")

    @staticmethod
    def _validate_name(value: str, label: str) -> None:
        if not _SAFE_NAME.fullmatch(value):
            raise ModelDirectoryError(f"{label} must be a safe name")

    def _remove_registered_from_root(
        self,
        old_root: Path,
        files: tuple[tuple[Path, Path], ...],
    ) -> None:
        for relative, _source in files:
            old_path = old_root / relative
            if old_path.is_file() and not old_path.is_symlink():
                old_path.unlink()
            _remove_empty_parents(old_path.parent, old_root)
        _remove_empty_parents(old_root, old_root.parent)


def _normalize_checksum(value: str) -> str:
    normalized = value.removeprefix("sha256:").strip().lower()
    if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
        raise ModelDirectoryError("checksum must be a SHA-256 hex digest")
    return normalized


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _remove_empty_parents(path: Path, stop: Path) -> None:
    current = path
    while current != stop and _is_relative_to(current, stop):
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


def _remove_tree(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path, ignore_errors=True)
    elif path.exists() or path.is_symlink():
        path.unlink(missing_ok=True)


def _is_disk_full(error: OSError) -> bool:
    return error.errno == errno.ENOSPC or getattr(error, "winerror", None) == 112
