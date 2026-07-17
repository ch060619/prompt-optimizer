from __future__ import annotations

import os
import shutil
from pathlib import Path, PurePosixPath
from threading import RLock
from typing import Literal
from uuid import uuid4

# RC ID: RC-064. Keep large files outside SQLite in a versioned, atomic layout.

FileCategory = Literal["logs", "attachments", "models", "cache"]
LAYOUT_VERSION = 1
FILE_CATEGORIES = frozenset({"logs", "attachments", "models", "cache"})


class FileStore:
    """Store large files outside SQLite with atomic replacement and scoped cleanup."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.version_root = root / f"v{LAYOUT_VERSION}"
        self.version_root.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()

    def category_path(self, category: FileCategory | str) -> Path:
        self._validate_category(category)
        return self.version_root / category

    def write_bytes(self, category: FileCategory | str, key: str, content: bytes) -> Path:
        target = self._target(category, key)
        with self._lock:
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
            try:
                with temporary.open("wb") as handle:
                    handle.write(content)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
        return target

    def write_text(
        self,
        category: FileCategory | str,
        key: str,
        content: str,
        *,
        encoding: str = "utf-8",
    ) -> Path:
        return self.write_bytes(category, key, content.encode(encoding))

    def read_bytes(self, category: FileCategory | str, key: str) -> bytes:
        target = self._target(category, key)
        with self._lock:
            return target.read_bytes()

    def read_text(
        self,
        category: FileCategory | str,
        key: str,
        *,
        encoding: str = "utf-8",
    ) -> str:
        return self.read_bytes(category, key).decode(encoding)

    def clear_cache(self) -> None:
        with self._lock:
            cache_path = self.category_path("cache")
            shutil.rmtree(cache_path, ignore_errors=True)

    def _target(self, category: FileCategory | str, key: str) -> Path:
        category_path = self.category_path(category)
        normalized_key = key.replace("\\", "/")
        relative = PurePosixPath(normalized_key)
        if (
            not key
            or relative.is_absolute()
            or any(part in {"", ".", ".."} for part in relative.parts)
        ):
            raise ValueError("文件键必须是分类目录内的相对路径。")
        target = category_path.joinpath(*relative.parts)
        if not target.parent.resolve().is_relative_to(category_path.resolve()):
            raise ValueError("文件键不能跳出分类目录。")
        return target

    @staticmethod
    def _validate_category(category: FileCategory | str) -> None:
        if category not in FILE_CATEGORIES:
            raise ValueError(f"不支持的文件分类：{category}")
