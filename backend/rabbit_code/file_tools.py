from __future__ import annotations

import difflib
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from .permissions import CapabilityDomain, PermissionPolicy
from .sensitive_files import SensitiveFilePolicy

# RC ID: RC-090. Provide bounded, workspace-safe file tools with write diffs.


class FileToolError(RuntimeError):
    pass


class FileBoundaryError(FileToolError):
    pass


class FileBinaryError(FileToolError):
    pass


class ConcurrentFileChangeError(FileToolError):
    pass


@dataclass(frozen=True)
class FileEntry:
    path: Path
    is_dir: bool
    size_bytes: int


@dataclass(frozen=True)
class FileWriteResult:
    operation: str
    path: Path
    diff: str
    before_sha256: str
    after_sha256: str
    destination: Path | None = None


class FileTools:
    def __init__(
        self,
        workspace_root: Path,
        *,
        max_file_bytes: int = 1_000_000,
        permission_policy: PermissionPolicy | None = None,
        sensitive_policy: SensitiveFilePolicy | None = None,
    ) -> None:
        if max_file_bytes <= 0:
            raise ValueError("max_file_bytes must be positive")
        self.workspace_root = workspace_root.expanduser().resolve()
        if not self.workspace_root.is_dir():
            raise ValueError("workspace root must be a directory")
        self.max_file_bytes = max_file_bytes
        self.permission_policy = permission_policy or PermissionPolicy(self.workspace_root)
        self.sensitive_policy = sensitive_policy or SensitiveFilePolicy(self.workspace_root)

    def read(self, path: str | Path, *, approval: bool = False) -> str:
        resolved, relative = self._normalize(path)
        self._authorize("read", resolved)
        self._authorize_sensitive_read(resolved, approved=approval)
        content, _ = self._read_text(resolved, relative)
        return content

    def list(self, path: str | Path = ".") -> tuple[FileEntry, ...]:
        resolved, _ = self._normalize(path)
        if not resolved.is_dir():
            raise FileToolError(f"directory not found: {path}")
        self._authorize("list", resolved)
        entries: list[FileEntry] = []
        for child in sorted(resolved.iterdir()):
            if child.is_symlink():
                continue
            if self.sensitive_policy.classify(child).sensitive:
                continue
            relative = child.relative_to(self.workspace_root)
            size = child.stat().st_size if child.is_file() else 0
            entries.append(FileEntry(relative, child.is_dir(), size))
        return tuple(entries)

    def search(self, query: str, path: str | Path = ".") -> tuple[Path, ...]:
        if not query:
            return ()
        resolved, _ = self._normalize(path)
        if not resolved.is_dir():
            raise FileToolError(f"directory not found: {path}")
        self._authorize("search", resolved)
        if self.sensitive_policy.classify(resolved).sensitive:
            return ()
        needle = query.casefold()
        matches: list[Path] = []
        for candidate in sorted(resolved.rglob("*")):
            if candidate.is_symlink() or not candidate.is_file():
                continue
            if self.sensitive_policy.classify(candidate).sensitive:
                continue
            try:
                content, _ = self._read_text(candidate, candidate.relative_to(self.workspace_root))
            except (FileBinaryError, UnicodeError):
                continue
            if needle in content.casefold():
                matches.append(candidate.relative_to(self.workspace_root))
        return tuple(matches)

    def edit(
        self,
        path: str | Path,
        content: str,
        *,
        expected_sha256: str | None = None,
        approval: bool = False,
    ) -> FileWriteResult:
        resolved, relative = self._normalize(path)
        self._authorize("edit", resolved, approval=approval)
        before, _ = self._read_text(resolved, relative)
        self._require_expected(resolved, expected_sha256)
        self._validate_content(content)
        self._atomic_write(resolved, content.encode("utf-8"))
        return self._result("edit", relative, before, content)

    def patch(
        self,
        path: str | Path,
        old_text: str,
        new_text: str,
        *,
        expected_sha256: str | None = None,
        approval: bool = False,
    ) -> FileWriteResult:
        resolved, relative = self._normalize(path)
        self._authorize("patch", resolved, approval=approval)
        before, _ = self._read_text(resolved, relative)
        self._require_expected(resolved, expected_sha256)
        if before.count(old_text) != 1:
            raise FileToolError("patch context must match exactly once")
        updated = before.replace(old_text, new_text, 1)
        self._validate_content(updated)
        self._atomic_write(resolved, updated.encode("utf-8"))
        return self._result("patch", relative, before, updated)

    def create(
        self,
        path: str | Path,
        content: str,
        *,
        approval: bool = False,
    ) -> FileWriteResult:
        resolved, relative = self._normalize(path)
        self._authorize("create", resolved, approval=approval)
        if resolved.exists():
            raise FileToolError(f"file already exists: {relative}")
        self._validate_content(content)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        self._atomic_write(resolved, content.encode("utf-8"))
        return self._result("create", relative, "", content)

    def move(
        self,
        source: str | Path,
        destination: str | Path,
        *,
        expected_sha256: str | None = None,
        approval: bool = False,
    ) -> FileWriteResult:
        source_path, source_relative = self._normalize(source)
        destination_path, destination_relative = self._normalize(destination)
        self._authorize("move", source_path, approval=approval)
        before, _ = self._read_text(source_path, source_relative)
        self._require_expected(source_path, expected_sha256)
        if destination_path.exists():
            raise FileToolError(f"destination already exists: {destination_relative}")
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        os.replace(source_path, destination_path)
        diff = _unified_diff(source_relative, destination_relative, before, before)
        digest = _sha256(before.encode("utf-8"))
        return FileWriteResult("move", source_relative, diff, digest, digest, destination_relative)

    def delete(
        self,
        path: str | Path,
        *,
        expected_sha256: str | None = None,
        approval: bool = False,
    ) -> FileWriteResult:
        resolved, relative = self._normalize(path)
        self._authorize("delete", resolved, approval=approval)
        before, _ = self._read_text(resolved, relative)
        self._require_expected(resolved, expected_sha256)
        resolved.unlink()
        return self._result("delete", relative, before, "")

    def _result(
        self,
        operation: str,
        relative: Path,
        before: str,
        after: str,
    ) -> FileWriteResult:
        before_bytes = before.encode("utf-8")
        after_bytes = after.encode("utf-8")
        return FileWriteResult(
            operation,
            relative,
            _unified_diff(relative, relative, before, after),
            _sha256(before_bytes),
            _sha256(after_bytes),
        )

    def _normalize(self, path: str | Path) -> tuple[Path, Path]:
        raw = Path(path).expanduser()
        candidate = raw if raw.is_absolute() else self.workspace_root / raw
        lexical = Path(os.path.abspath(candidate))
        try:
            lexical.relative_to(self.workspace_root)
        except ValueError as exc:
            raise FileBoundaryError("path must remain within the workspace") from exc
        current = self.workspace_root
        for part in lexical.relative_to(self.workspace_root).parts:
            current /= part
            if current.is_symlink():
                raise FileBoundaryError("symlink paths are not allowed")
        resolved = lexical.resolve()
        try:
            relative = resolved.relative_to(self.workspace_root)
        except ValueError as exc:
            raise FileBoundaryError("path must remain within the workspace") from exc
        return resolved, relative

    def _read_text(self, path: Path, relative: Path) -> tuple[str, bytes]:
        if not path.is_file():
            raise FileToolError(f"file not found: {relative}")
        data = path.read_bytes()
        self._validate_size(len(data), relative)
        if b"\x00" in data:
            raise FileBinaryError(f"binary file is not supported: {relative}")
        try:
            return data.decode("utf-8"), data
        except UnicodeDecodeError as exc:
            raise FileBinaryError(f"file is not valid UTF-8: {relative}") from exc

    def _validate_content(self, content: str) -> None:
        if not isinstance(content, str):
            raise TypeError("file content must be text")
        self._validate_size(len(content.encode("utf-8")), Path("<content>"))

    def _validate_size(self, size: int, relative: Path) -> None:
        if size > self.max_file_bytes:
            raise FileToolError(f"file exceeds size limit: {relative}")

    def _require_expected(self, path: Path, expected_sha256: str | None) -> None:
        if expected_sha256 is None:
            raise ConcurrentFileChangeError("expected_sha256 is required for existing files")
        actual = _sha256(path.read_bytes())
        if actual != expected_sha256:
            raise ConcurrentFileChangeError("file changed since the expected snapshot")

    def _authorize(self, action: str, path: Path, *, approval: bool = False) -> None:
        capability_action = (
            action if action in {"read", "list", "search", "delete"} else "write"
        )
        decision = self.permission_policy.authorize_capability(
            CapabilityDomain.FILES,
            capability_action,
            {"path": path},
            approval=approval,
        )
        if not decision.allowed:
            raise PermissionError(decision.reason)

    def _authorize_sensitive_read(self, path: Path, *, approved: bool) -> None:
        decision = self.sensitive_policy.authorize_read(path, approved=approved)
        if not decision.allowed:
            raise PermissionError(decision.reason)

    @staticmethod
    def _atomic_write(path: Path, content: bytes) -> None:
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        try:
            with temporary.open("wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _unified_diff(path_a: Path, path_b: Path, before: str, after: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"a/{path_a.as_posix()}",
            tofile=f"b/{path_b.as_posix()}",
        )
    )
