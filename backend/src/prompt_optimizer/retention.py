from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from prompt_optimizer.storage.service import StorageService

# RC ID: RC-218. Keep bounded local logs, cache, sessions, and prompt history.

RetentionLogLevel = Literal["error", "info", "debug"]


@dataclass(frozen=True)
class RetentionPolicy:
    log_level: RetentionLogLevel = "info"
    max_log_file_bytes: int = 5 * 1024 * 1024
    max_log_total_bytes: int = 50 * 1024 * 1024
    cache_max_bytes: int = 100 * 1024 * 1024
    session_retention_days: int = 30
    prompt_history_retention_days: int = 365
    prompt_history_max_entries: int = 500

    def __post_init__(self) -> None:
        for name in (
            "max_log_file_bytes",
            "max_log_total_bytes",
            "cache_max_bytes",
            "session_retention_days",
            "prompt_history_retention_days",
            "prompt_history_max_entries",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.max_log_file_bytes > self.max_log_total_bytes:
            raise ValueError("max_log_file_bytes cannot exceed max_log_total_bytes")

    def display(self) -> dict[str, object]:
        return {
            "log_level": self.log_level,
            "max_log_file_bytes": self.max_log_file_bytes,
            "max_log_total_bytes": self.max_log_total_bytes,
            "cache_max_bytes": self.cache_max_bytes,
            "session_retention_days": self.session_retention_days,
            "prompt_history_retention_days": self.prompt_history_retention_days,
            "prompt_history_max_entries": self.prompt_history_max_entries,
        }


DEFAULT_RETENTION_POLICY = RetentionPolicy()


@dataclass(frozen=True)
class RetentionPlan:
    policy: RetentionPolicy
    rotate_log_paths: tuple[Path, ...] = ()
    delete_log_paths: tuple[Path, ...] = ()
    delete_cache_paths: tuple[Path, ...] = ()
    delete_task_ids: tuple[str, ...] = ()
    delete_history_ids: tuple[int, ...] = ()
    estimated_bytes: int = 0

    def display(self) -> dict[str, object]:
        return {
            "policy": self.policy.display(),
            "rotate_log_paths": [str(path) for path in self.rotate_log_paths],
            "delete_log_paths": [str(path) for path in self.delete_log_paths],
            "delete_cache_paths": [str(path) for path in self.delete_cache_paths],
            "delete_task_ids": list(self.delete_task_ids),
            "delete_history_ids": list(self.delete_history_ids),
            "estimated_bytes": self.estimated_bytes,
            "retain": [
                "configuration",
                "model files",
                "attachments",
                "database file",
                "queued/running tasks",
            ],
        }


@dataclass(frozen=True)
class RetentionResult:
    cancelled: bool
    rotated_log_paths: tuple[str, ...] = ()
    deleted_paths: tuple[str, ...] = ()
    deleted_task_count: int = 0
    deleted_history_count: int = 0

    def display(self) -> dict[str, object]:
        return {
            "cancelled": self.cancelled,
            "rotated_log_paths": list(self.rotated_log_paths),
            "deleted_paths": list(self.deleted_paths),
            "deleted_task_count": self.deleted_task_count,
            "deleted_history_count": self.deleted_history_count,
        }


class RetentionError(RuntimeError):
    pass


class RetentionService:
    def __init__(
        self,
        storage: StorageService,
        *,
        process_guard: Callable[[], bool] | None = None,
    ) -> None:
        self.storage = storage
        self.process_guard = process_guard or (lambda: True)

    def preview(
        self,
        *,
        policy: RetentionPolicy = DEFAULT_RETENTION_POLICY,
        now: datetime | None = None,
        owner_id: int = 1,
    ) -> RetentionPlan:
        current = _utc(now or datetime.now(UTC))
        log_files = _files(self.storage.file_store.category_path("logs"))
        cache_files = _files(self.storage.file_store.category_path("cache"))
        rotate_logs = tuple(
            path for path in log_files if path.stat().st_size > policy.max_log_file_bytes
        )
        delete_logs = _over_budget(
            log_files,
            policy.max_log_total_bytes,
            protected=set(rotate_logs),
        )
        delete_cache = _over_budget(cache_files, policy.cache_max_bytes)
        task_ids, history_ids = self.storage.retention_candidates(
            owner_id=owner_id,
            session_cutoff=current - timedelta(days=policy.session_retention_days),
            history_cutoff=current - timedelta(days=policy.prompt_history_retention_days),
            max_history_entries=policy.prompt_history_max_entries,
        )
        deleted_paths = (*delete_logs, *delete_cache)
        return RetentionPlan(
            policy=policy,
            rotate_log_paths=rotate_logs,
            delete_log_paths=delete_logs,
            delete_cache_paths=delete_cache,
            delete_task_ids=task_ids,
            delete_history_ids=history_ids,
            estimated_bytes=sum(path.stat().st_size for path in deleted_paths if path.exists()),
        )

    def apply(
        self,
        *,
        confirm: bool,
        policy: RetentionPolicy = DEFAULT_RETENTION_POLICY,
        now: datetime | None = None,
        owner_id: int = 1,
    ) -> RetentionResult:
        if not confirm:
            return RetentionResult(cancelled=True)
        if not self.process_guard():
            raise RetentionError("无法确认相关进程已停止；未执行保留清理。")
        plan = self.preview(policy=policy, now=now, owner_id=owner_id)
        rotated: list[str] = []
        for source in plan.rotate_log_paths:
            if not source.exists():
                continue
            target = _rotation_target(source)
            source.rename(target)
            rotated.append(str(target))
        deleted: list[str] = []
        for path in (*plan.delete_log_paths, *plan.delete_cache_paths):
            if path.exists():
                path.unlink()
                deleted.append(str(path))
        task_count, history_count = self.storage.delete_retention_records(
            task_ids=plan.delete_task_ids,
            history_ids=plan.delete_history_ids,
            owner_id=owner_id,
        )
        return RetentionResult(
            cancelled=False,
            rotated_log_paths=tuple(rotated),
            deleted_paths=tuple(deleted),
            deleted_task_count=task_count,
            deleted_history_count=history_count,
        )


def _files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_file() and not _protected_name(path.name)
        ),
        key=lambda path: (path.stat().st_mtime_ns, str(path)),
    )


def _over_budget(
    files: list[Path],
    maximum: int,
    *,
    protected: set[Path] | None = None,
) -> tuple[Path, ...]:
    protected = protected or set()
    total = sum(path.stat().st_size for path in files)
    if total <= maximum:
        return ()
    candidates: list[Path] = []
    for path in files:
        if path in protected:
            continue
        if total <= maximum:
            break
        total -= path.stat().st_size
        candidates.append(path)
    return tuple(candidates)


def _rotation_target(source: Path) -> Path:
    for index in range(1, 101):
        target = source.with_name(f"{source.name}.{index}")
        if not target.exists():
            return target
    raise RetentionError(f"日志轮转目标过多：{source}")


def _protected_name(name: str) -> bool:
    return name.endswith((".tmp", ".lock", ".active"))


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
