from __future__ import annotations

import json
import os
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from prompt_optimizer.config import parse_config_reference
from prompt_optimizer.secrets import SecretStore

# RC ID: RC-184. Preview and confirm credential/config/local-data cleanup safely.


class CleanupError(RuntimeError):
    """Base error for local data cleanup and opaque config migration."""


@dataclass(frozen=True)
class CleanupPlan:
    delete_paths: tuple[Path, ...]
    credential_refs: tuple[str, ...]
    retain_labels: tuple[str, ...] = ("Rabbit Code application files",)

    def display(self) -> dict[str, object]:
        return {
            "delete_paths": [str(path) for path in self.delete_paths],
            "credential_count": len(self.credential_refs),
            "retain": list(self.retain_labels),
        }


@dataclass(frozen=True)
class CleanupResult:
    cancelled: bool
    deleted_paths: tuple[str, ...] = ()
    deleted_credentials: int = 0

    def display(self) -> dict[str, object]:
        return {
            "cancelled": self.cancelled,
            "deleted_paths": list(self.deleted_paths),
            "deleted_credentials": self.deleted_credentials,
        }


class LocalDataCleanupService:
    def __init__(
        self,
        *,
        secret_store: SecretStore,
        paths: Iterable[Path],
        config_paths: Iterable[Path] = (),
        process_guard: Callable[[], bool] | None = None,
    ) -> None:
        self.secret_store = secret_store
        self.paths = tuple(dict.fromkeys(path for path in paths))
        self.config_paths = tuple(dict.fromkeys(path for path in config_paths))
        self.process_guard = process_guard or (lambda: True)

    def preview(self) -> CleanupPlan:
        existing_paths = tuple(path for path in self.paths if path.exists())
        refs = tuple(sorted(set(self._credential_refs())))
        return CleanupPlan(existing_paths, refs)

    def clear_all(self, *, confirm: bool) -> CleanupResult:
        if not confirm:
            return CleanupResult(cancelled=True)
        if not self.process_guard():
            raise CleanupError("无法确认相关进程已停止；未执行清理。")
        plan = self.preview()
        for reference in plan.credential_refs:
            self.secret_store.delete(reference)
        deleted_paths: list[str] = []
        for path in plan.delete_paths:
            _secure_delete(path)
            deleted_paths.append(str(path))
        return CleanupResult(
            cancelled=False,
            deleted_paths=tuple(deleted_paths),
            deleted_credentials=len(plan.credential_refs),
        )

    def delete_provider_credential(self, reference: str) -> None:
        self.secret_store.delete(reference)

    def _credential_refs(self) -> Iterable[str]:
        for path in self.config_paths:
            if not path.is_file():
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise CleanupError(f"无法读取清理配置：{path}") from exc
            yield from _iter_credential_refs(payload)


def migrate_opaque_config(source: Path, destination: Path) -> None:
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CleanupError(f"无法读取待迁移配置：{source}") from exc
    if not isinstance(payload, dict):
        raise CleanupError("待迁移配置必须是 JSON 对象。")
    _reject_plaintext_credentials(payload)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.migration.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def _iter_values(value: object) -> Iterable[object]:
    if isinstance(value, Mapping):
        for item in value.values():
            yield item
            yield from _iter_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield item
            yield from _iter_values(item)


def _iter_credential_refs(value: object) -> Iterable[str]:
    for item in _iter_values(value):
        if not isinstance(item, str):
            continue
        reference = parse_config_reference(item)
        if reference is not None and reference.kind == "keychain":
            yield reference.target


def _reject_plaintext_credentials(value: object) -> None:
    sensitive_names = {"api_key", "apikey", "access_token", "password", "secret"}
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = str(key).replace("-", "_").lower()
            if normalized_key in sensitive_names and isinstance(item, str):
                reference = parse_config_reference(item)
                if reference is None:
                    raise CleanupError("配置迁移拒绝包含明文 Provider 凭据。")
            _reject_plaintext_credentials(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_plaintext_credentials(item)


def _secure_delete(path: Path) -> None:
    if path.is_symlink():
        path.unlink(missing_ok=True)
        return
    if path.is_file():
        _overwrite_file(path)
        path.unlink(missing_ok=True)
        return
    if path.is_dir():
        for child in sorted(path.iterdir(), reverse=True):
            _secure_delete(child)
        path.rmdir()


def _overwrite_file(path: Path) -> None:
    try:
        size = path.stat().st_size
        with path.open("r+b") as handle:
            handle.write(b"\x00" * size)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise CleanupError(f"无法安全擦除文件：{path}") from exc
