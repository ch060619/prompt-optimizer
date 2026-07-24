from __future__ import annotations

import mimetypes
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Any

from prompt_optimizer.limits import DEFAULT_DATA_LIMITS, validate_limit

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
    def __init__(
        self,
        workspace_root: Path,
        *,
        max_text_bytes: int = DEFAULT_DATA_LIMITS.context_bytes,
        max_attachment_bytes: int = DEFAULT_DATA_LIMITS.attachment_bytes,
    ) -> None:
        validate_limit(
            max_text_bytes,
            name="max_text_bytes",
            maximum=DEFAULT_DATA_LIMITS.max_context_bytes,
        )
        validate_limit(
            max_attachment_bytes,
            name="max_attachment_bytes",
            maximum=DEFAULT_DATA_LIMITS.max_attachment_bytes,
        )
        self.workspace_root = workspace_root.resolve()
        self.max_text_bytes = max_text_bytes
        self.max_attachment_bytes = max_attachment_bytes
        self._items: list[ContextItem] = []

    @property
    def items(self) -> tuple[ContextItem, ...]:
        return tuple(self._items)

    def add_file(self, path: Path) -> ContextItem:
        resolved = self._safe_path(path)
        if not resolved.is_file():
            raise ValueError("context file is missing")
        content, metadata = self._read_text(resolved)
        return self._append(
            ContextItem(
                ContextItemType.FILE,
                resolved,
                content,
                metadata,
                metadata["truncated"],
            )
        )

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
        content, metadata = self._bound_text("".join(lines[start_line - 1 : end_line]))
        metadata.update({"start_line": start_line, "end_line": end_line})
        return self._append(
            ContextItem(
                ContextItemType.SELECTION,
                resolved,
                content,
                metadata,
                metadata["truncated"],
            )
        )

    def add_attachment(self, path: Path) -> ContextItem:
        resolved = self._safe_path(path)
        if not resolved.is_file():
            raise ValueError("context attachment is missing")
        size_bytes = resolved.stat().st_size
        if size_bytes > self.max_attachment_bytes:
            raise ValueError("context attachment exceeds max_attachment_bytes")
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
                metadata={
                    "mime_type": mime_type,
                    "size_bytes": size_bytes,
                    "original_bytes": size_bytes,
                    "next_cursor": size_bytes,
                    "truncated": False,
                },
            )
        )

    def add_terminal(self, output: str) -> ContextItem:
        content, metadata = self._bound_text(output)
        return self._append(
            ContextItem(
                ContextItemType.TERMINAL,
                content=content,
                metadata=metadata,
                truncated=metadata["truncated"],
            )
        )

    def add_diff(self, diff: str) -> ContextItem:
        content, metadata = self._bound_text(diff)
        return self._append(
            ContextItem(
                ContextItemType.DIFF,
                content=content,
                metadata=metadata,
                truncated=metadata["truncated"],
            )
        )

    def add_diagnostic(self, diagnostic: str) -> ContextItem:
        content, metadata = self._bound_text(diagnostic)
        return self._append(
            ContextItem(
                ContextItemType.DIAGNOSTIC,
                content=content,
                metadata=metadata,
                truncated=metadata["truncated"],
            )
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

    def _read_text(self, path: Path) -> tuple[str, dict[str, Any]]:
        return self._bound_text(path.read_text(encoding="utf-8", errors="replace"))

    def _bound_text(self, value: str) -> tuple[str, dict[str, Any]]:
        encoded = value.encode("utf-8")
        if len(encoded) <= self.max_text_bytes:
            return value, {
                "original_bytes": len(encoded),
                "next_cursor": len(encoded),
                "truncated": False,
            }
        content = encoded[: self.max_text_bytes].decode("utf-8", errors="ignore")
        return content, {
            "original_bytes": len(encoded),
            "next_cursor": len(content.encode("utf-8")),
            "truncated": True,
        }

    def _ignored(self, path: Path) -> bool:
        relative = path.relative_to(self.workspace_root)
        return any(part in IGNORED_DIRECTORIES for part in relative.parts)
