from __future__ import annotations

import hashlib
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

# RC ID: RC-088. Bind sessions to isolated workspaces and owned resources.


class WorkspaceAccessError(PermissionError):
    """Raised when a session accesses another workspace or resource."""


@dataclass(frozen=True)
class WorkspaceBinding:
    session_id: str
    workspace_id: str
    project_root: Path
    root: Path
    owns_root: bool


class WorkspaceManager:
    def __init__(self) -> None:
        self._bindings: dict[str, WorkspaceBinding] = {}
        self._processes: dict[str, str] = {}
        self._terminals: dict[str, str] = {}
        self._cache_roots: dict[str, Path] = {}

    def bind(
        self,
        session_id: str,
        project_root: Path,
        *,
        worktree_path: Path | None = None,
    ) -> WorkspaceBinding:
        session_id = _require_id(session_id, "session_id")
        if session_id in self._bindings:
            raise ValueError(f"session is already bound: {session_id}")
        project_root = self._safe_existing_directory(project_root, "project root")
        if worktree_path is None:
            root = project_root
            owns_root = False
        else:
            worktree_path = self._safe_path(worktree_path)
            if worktree_path.exists():
                if not worktree_path.is_dir():
                    raise ValueError("worktree path must be a directory")
                owns_root = False
            else:
                worktree_path.mkdir(parents=True)
                owns_root = True
            root = worktree_path
        digest = hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:16]
        binding = WorkspaceBinding(
            session_id,
            f"{session_id}:{digest}",
            project_root,
            root,
            owns_root,
        )
        self._bindings[session_id] = binding
        return binding

    def binding(self, session_id: str) -> WorkspaceBinding:
        try:
            return self._bindings[session_id]
        except KeyError as exc:
            raise WorkspaceAccessError(f"session is not bound: {session_id}") from exc

    def read_text(self, session_id: str, path: Path) -> str:
        resolved = self._resolve_owned_path(session_id, path)
        if not resolved.is_file():
            raise FileNotFoundError(resolved)
        return resolved.read_text(encoding="utf-8")

    def write_text(self, session_id: str, path: Path, content: str) -> Path:
        resolved = self._resolve_owned_path(session_id, path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")
        return resolved

    def cache_path(self, session_id: str, name: str) -> Path:
        binding = self.binding(session_id)
        cache_root = binding.root / ".rabbit-code" / "cache"
        if session_id not in self._cache_roots:
            cache_was_present = cache_root.exists()
            cache_root.mkdir(parents=True, exist_ok=True)
            if not cache_was_present:
                self._cache_roots[session_id] = cache_root
        return self._resolve_owned_path(session_id, Path(".rabbit-code") / "cache" / name)

    def register_process(self, session_id: str, process_id: str) -> None:
        self.binding(session_id)
        process_id = _require_id(process_id, "process_id")
        owner = self._processes.get(process_id)
        if owner is not None and owner != session_id:
            raise WorkspaceAccessError(f"process belongs to another session: {process_id}")
        self._processes[process_id] = session_id

    def register_terminal(self, session_id: str, terminal_id: str) -> None:
        self.binding(session_id)
        terminal_id = _require_id(terminal_id, "terminal_id")
        owner = self._terminals.get(terminal_id)
        if owner is not None and owner != session_id:
            raise WorkspaceAccessError(f"terminal belongs to another session: {terminal_id}")
        self._terminals[terminal_id] = session_id

    def assert_process_owner(self, session_id: str, process_id: str) -> None:
        self._assert_owner(self._processes, session_id, process_id, "process")

    def assert_terminal_owner(self, session_id: str, terminal_id: str) -> None:
        self._assert_owner(self._terminals, session_id, terminal_id, "terminal")

    def cleanup(self, session_id: str) -> None:
        binding = self.binding(session_id)
        self._processes = {
            resource: owner for resource, owner in self._processes.items() if owner != session_id
        }
        self._terminals = {
            resource: owner for resource, owner in self._terminals.items() if owner != session_id
        }
        cache_root = self._cache_roots.pop(session_id, None)
        if cache_root is not None and cache_root.is_dir() and not binding.owns_root:
            shutil.rmtree(cache_root)
        if binding.owns_root and binding.root.exists():
            shutil.rmtree(binding.root)
        del self._bindings[session_id]

    def _resolve_owned_path(self, session_id: str, path: Path) -> Path:
        binding = self.binding(session_id)
        candidate = path if path.is_absolute() else binding.root / path
        return self._safe_path(candidate, root=binding.root)

    def _safe_path(self, path: Path, *, root: Path | None = None) -> Path:
        if path.expanduser().is_symlink():
            raise WorkspaceAccessError("workspace path cannot be a symlink")
        resolved = path.expanduser().resolve()
        boundary = root or resolved.parent
        try:
            resolved.relative_to(boundary)
        except ValueError as exc:
            raise WorkspaceAccessError("path is outside the bound workspace") from exc
        return resolved

    @staticmethod
    def _safe_existing_directory(path: Path, name: str) -> Path:
        if path.expanduser().is_symlink():
            raise ValueError(f"{name} cannot be a symlink")
        resolved = path.expanduser().resolve()
        if not resolved.is_dir():
            raise ValueError(f"{name} must be a directory")
        return resolved

    @staticmethod
    def _assert_owner(
        resources: dict[str, str], session_id: str, resource_id: str, name: str
    ) -> None:
        if resources.get(resource_id) != session_id:
            raise WorkspaceAccessError(f"{name} belongs to another session or is unknown")


def _require_id(value: str, name: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9._:-]+", value):
        raise ValueError(f"invalid {name}")
    return value
