"""A bounded read-only workspace summary tool."""

from __future__ import annotations

from pathlib import Path


def workspace_summary(root: Path, *, limit: int = 20) -> dict[str, object]:
    if limit < 1:
        raise ValueError("limit must be positive")
    files = sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.parts
    )[:limit]
    return {"root": str(root.resolve()), "file_count": len(files), "files": files}
