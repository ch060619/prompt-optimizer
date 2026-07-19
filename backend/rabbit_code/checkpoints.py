from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

# RC ID: RC-087. Track Agent file groups and rollback only proven changes.


@dataclass(frozen=True)
class FileChange:
    path: str
    before: bytes | None
    after: bytes | None

    @property
    def before_sha256(self) -> str:
        return _digest(self.before)

    @property
    def after_sha256(self) -> str:
        return _digest(self.after)


@dataclass(frozen=True)
class ChangeGroup:
    id: str
    name: str
    changes: tuple[FileChange, ...]
    tools: tuple[str, ...]
    verifications: tuple[str, ...]


@dataclass(frozen=True)
class RollbackReport:
    scope: str
    restored: tuple[str, ...]
    skipped: tuple[str, ...]
    conflicts: tuple[str, ...]


@dataclass
class _GroupDraft:
    id: str
    name: str
    paths: tuple[str, ...]
    before: dict[str, bytes | None]
    tools: tuple[str, ...]


class WorktreeCheckpoint:
    def __init__(self, manager: CheckpointManager, baseline: dict[str, bytes | None]) -> None:
        self.manager = manager
        self.baseline = dict(baseline)
        self._drafts: dict[str, _GroupDraft] = {}
        self._groups: list[ChangeGroup] = []

    @property
    def groups(self) -> tuple[ChangeGroup, ...]:
        return tuple(self._groups)

    def begin_group(
        self,
        name: str,
        paths: tuple[Path, ...],
        *,
        tools: tuple[str, ...] = (),
    ) -> str:
        name = _require_text(name, "name")
        normalized = self.manager._normalize_paths(paths)
        for path in normalized:
            if path not in self.baseline:
                raise ValueError(f"path was not included in the checkpoint baseline: {path}")
        group_id = uuid4().hex
        self._drafts[group_id] = _GroupDraft(
            id=group_id,
            name=name,
            paths=normalized,
            before=self.manager._capture(normalized),
            tools=_text_tuple(tools, "tools"),
        )
        return group_id

    def finish_group(self, group_id: str, *, verifications: tuple[str, ...] = ()) -> ChangeGroup:
        try:
            draft = self._drafts.pop(group_id)
        except KeyError as exc:
            raise KeyError(f"change group not found: {group_id}") from exc
        after = self.manager._capture(draft.paths)
        changes = tuple(
            FileChange(path, draft.before[path], after[path])
            for path in draft.paths
            if draft.before[path] != after[path]
        )
        group = ChangeGroup(
            id=draft.id,
            name=draft.name,
            changes=changes,
            tools=draft.tools,
            verifications=_text_tuple(verifications, "verifications"),
        )
        self._groups.append(group)
        return group

    def rollback(self, group_id: str | None = None) -> RollbackReport:
        if self._drafts:
            raise RuntimeError("cannot rollback while a change group is open")
        if group_id is None:
            selected = tuple(reversed(self._groups))
            scope = "all"
        else:
            selected = tuple(group for group in self._groups if group.id == group_id)
            if not selected:
                raise KeyError(f"change group not found: {group_id}")
            scope = selected[0].name

        restored: list[str] = []
        skipped: list[str] = []
        conflicts: list[str] = []
        for group in selected:
            for change in group.changes:
                current = self.manager._read(change.path)
                if current == change.after:
                    self.manager._restore(change.path, change.before)
                    restored.append(change.path)
                elif current == change.before:
                    skipped.append(change.path)
                else:
                    conflicts.append(change.path)
        return RollbackReport(scope, tuple(restored), tuple(skipped), tuple(conflicts))


class CheckpointManager:
    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root.resolve()
        if not self.workspace_root.is_dir():
            raise ValueError("workspace root must be a directory")

    def create(self, paths: tuple[Path, ...]) -> WorktreeCheckpoint:
        normalized = self._normalize_paths(paths)
        if not normalized:
            raise ValueError("checkpoint requires at least one path")
        baseline = self._capture(normalized)
        return WorktreeCheckpoint(self, baseline)

    def _normalize_paths(self, paths: tuple[Path, ...]) -> tuple[str, ...]:
        normalized: list[str] = []
        for path in paths:
            resolved = self._safe_path(path)
            relative = resolved.relative_to(self.workspace_root).as_posix()
            if relative not in normalized:
                normalized.append(relative)
        return tuple(normalized)

    def _capture(self, paths: tuple[str, ...]) -> dict[str, bytes | None]:
        return {path: self._read(path) for path in paths}

    def _read(self, relative: str) -> bytes | None:
        path = self._safe_path(self.workspace_root / relative)
        if not path.exists():
            return None
        if not path.is_file():
            raise ValueError(f"checkpoint path is not a file: {relative}")
        return path.read_bytes()

    def _restore(self, relative: str, content: bytes | None) -> None:
        path = self._safe_path(self.workspace_root / relative)
        if content is None:
            path.unlink(missing_ok=True)
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.rollback.tmp")
        try:
            temporary.write_bytes(content)
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def _safe_path(self, path: Path) -> Path:
        if path.expanduser().is_symlink():
            raise ValueError("checkpoint path cannot be a symlink")
        resolved = path.expanduser().resolve()
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError as exc:
            raise ValueError("checkpoint path must remain within the workspace") from exc
        return resolved


def _digest(content: bytes | None) -> str:
    return hashlib.sha256(content or b"").hexdigest()


def _require_text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty")
    return value


def _text_tuple(values: tuple[str, ...], name: str) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{name} must be a tuple of strings")
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise ValueError(f"{name} must contain non-empty strings")
    return values
