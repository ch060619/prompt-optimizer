from __future__ import annotations

import mimetypes
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any

# RC ID: RC-082. Collect bounded, workspace-safe context references for Agent requests.


IGNORED_DIRECTORIES = frozenset({".git", ".venv", "node_modules", "dist", "__pycache__"})


class ContextItemType(StrEnum):
    FILE = "file"
    DIRECTORY = "directory"
    SELECTION = "selection"
    IMAGE = "image"
    ATTACHMENT = "attachment"
    TERMINAL = "terminal"
    DIFF = "diff"
    DIAGNOSTIC = "diagnostic"


@dataclass(frozen=True)
class ContextItem:
    kind: ContextItemType
    path: Path | None = None
    content: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    truncated: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


class ContextCollector:
    def __init__(self, workspace_root: Path, *, max_text_bytes: int = 32_000) -> None:
        if max_text_bytes <= 0:
            raise ValueError("max_text_bytes must be positive")
        self.workspace_root = workspace_root.resolve()
        self.max_text_bytes = max_text_bytes
        self._items: list[ContextItem] = []

    @property
    def items(self) -> tuple[ContextItem, ...]:
        return tuple(self._items)

    def add_file(self, path: Path) -> ContextItem:
        resolved = self._safe_path(path)
        if not resolved.is_file():
            raise ValueError("context file is missing")
        content, truncated = self._read_text(resolved)
        return self._append(ContextItem(ContextItemType.FILE, resolved, content, {}, truncated))

    def add_directory(self, path: Path) -> tuple[ContextItem, ...]:
        resolved = self._safe_path(path)
        if not resolved.is_dir():
            raise ValueError("context directory is missing")
        added = []
        for file in sorted(resolved.rglob("*")):
            if file.is_file() and not self._ignored(file):
                added.append(self.add_file(file))
        return tuple(added)

    def add_selection(self, path: Path, *, start_line: int, end_line: int) -> ContextItem:
        if start_line < 1 or end_line < start_line:
            raise ValueError("invalid selection range")
        resolved = self._safe_path(path)
        if not resolved.is_file():
            raise ValueError("context selection file is missing")
        lines = resolved.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        content, truncated = self._bound_text("".join(lines[start_line - 1 : end_line]))
        return self._append(
            ContextItem(
                ContextItemType.SELECTION,
                resolved,
                content,
                {"start_line": start_line, "end_line": end_line},
                truncated,
            )
        )

    def add_attachment(self, path: Path) -> ContextItem:
        resolved = self._safe_path(path)
        if not resolved.is_file():
            raise ValueError("context attachment is missing")
        mime_type = mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
        kind = (
            ContextItemType.IMAGE
            if mime_type.startswith("image/")
            else ContextItemType.ATTACHMENT
        )
        return self._append(
            ContextItem(
                kind,
                resolved,
                metadata={"mime_type": mime_type, "size_bytes": resolved.stat().st_size},
            )
        )

    def add_terminal(self, output: str) -> ContextItem:
        content, truncated = self._bound_text(output)
        return self._append(
            ContextItem(ContextItemType.TERMINAL, content=content, truncated=truncated)
        )

    def add_diff(self, diff: str) -> ContextItem:
        content, truncated = self._bound_text(diff)
        return self._append(ContextItem(ContextItemType.DIFF, content=content, truncated=truncated))

    def add_diagnostic(self, diagnostic: str) -> ContextItem:
        content, truncated = self._bound_text(diagnostic)
        return self._append(
            ContextItem(ContextItemType.DIAGNOSTIC, content=content, truncated=truncated)
        )

    def _append(self, item: ContextItem) -> ContextItem:
        self._items.append(item)
        return item

    def _safe_path(self, path: Path) -> Path:
        resolved = path.expanduser().resolve()
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError as exc:
            raise ValueError("context path must remain within the workspace") from exc
        return resolved

    def _read_text(self, path: Path) -> tuple[str, bool]:
        return self._bound_text(path.read_text(encoding="utf-8", errors="replace"))

    def _bound_text(self, value: str) -> tuple[str, bool]:
        encoded = value.encode("utf-8")
        if len(encoded) <= self.max_text_bytes:
            return value, False
        return encoded[: self.max_text_bytes].decode("utf-8", errors="ignore"), True

    def _ignored(self, path: Path) -> bool:
        relative = path.relative_to(self.workspace_root)
        return any(part in IGNORED_DIRECTORIES for part in relative.parts)
