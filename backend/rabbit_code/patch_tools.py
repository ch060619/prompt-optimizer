from __future__ import annotations

import difflib
import hashlib
import json
import os
import shutil
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .permissions import PermissionPolicy

# RC ID: RC-095. Apply structured text edits as an all-or-nothing transaction.


class PatchError(RuntimeError):
    pass


class PatchParseError(PatchError):
    pass


class PatchConflict(PatchError):
    pass


class PatchBoundaryError(PatchError):
    pass


class PatchApplyError(PatchError):
    pass


@dataclass(frozen=True)
class PatchEdit:
    path: str | Path
    old_text: str
    new_text: str
    expected_sha256: str | None = None


@dataclass(frozen=True)
class PatchResult:
    path: Path
    before_sha256: str
    after_sha256: str
    diff: str


@dataclass(frozen=True)
class PatchBatchResult:
    files: tuple[PatchResult, ...]
    atomic: bool = True


@dataclass
class _PreparedEdit:
    edit: PatchEdit
    path: Path
    before: bytes
    after: bytes
    temp_path: Path | None = None
    backup_path: Path | None = None


class AtomicPatchTool:
    def __init__(
        self,
        workspace_root: Path,
        *,
        permission_policy: PermissionPolicy | None = None,
    ) -> None:
        self.workspace_root = workspace_root.expanduser().resolve()
        if not self.workspace_root.is_dir():
            raise ValueError("workspace root must be a directory")
        self.permission_policy = permission_policy or PermissionPolicy(self.workspace_root)

    def apply(
        self,
        payload: PatchEdit
        | str
        | Mapping[str, Any]
        | Sequence[PatchEdit | Mapping[str, Any]],
        *,
        approval: bool = False,
    ) -> PatchBatchResult:
        edits = parse_patch(payload)
        if not edits:
            raise PatchParseError("patch must contain at least one edit")
        prepared = self._prepare(edits, approval=approval)
        try:
            self._write_temporary(prepared)
            self._check_concurrent_changes(prepared)
            self._replace_all(prepared)
        except PatchError:
            self._cleanup(prepared)
            raise
        except Exception as exc:
            self._rollback(prepared)
            self._cleanup(prepared)
            raise PatchApplyError(f"atomic patch failed: {exc}") from exc
        self._cleanup(prepared)
        return PatchBatchResult(
            tuple(
                PatchResult(
                    item.path,
                    _sha256(item.before),
                    _sha256(item.after),
                    _diff(item.path, item.before, item.after),
                )
                for item in prepared
            )
        )

    def apply_patch(
        self,
        payload: PatchEdit
        | str
        | Mapping[str, Any]
        | Sequence[PatchEdit | Mapping[str, Any]],
        *,
        approval: bool = False,
    ) -> PatchBatchResult:
        return self.apply(payload, approval=approval)

    def _prepare(self, edits: tuple[PatchEdit, ...], *, approval: bool) -> list[_PreparedEdit]:
        prepared: list[_PreparedEdit] = []
        paths: set[Path] = set()
        try:
            for edit in edits:
                path = self._path(edit.path)
                if path in paths:
                    raise PatchParseError(f"duplicate patch path: {path}")
                paths.add(path)
                decision = self.permission_policy.authorize(
                    "edit", {"path": path}, approval=approval
                )
                if not decision.allowed:
                    raise PermissionError(decision.reason)
                before = path.read_bytes()
                expected = edit.expected_sha256
                actual = _sha256(before)
                if expected is not None and expected != actual:
                    raise PatchConflict(f"baseline hash mismatch: {path}")
                text, codec, bom = _decode(before, path)
                line_ending = _line_ending(text)
                old_text = _adapt_newlines(edit.old_text, line_ending)
                new_text = _adapt_newlines(edit.new_text, line_ending)
                occurrences = text.count(old_text)
                if occurrences != 1:
                    raise PatchConflict(
                        f"patch context must match exactly once: {path} ({occurrences})"
                    )
                updated = text.replace(old_text, new_text, 1)
                prepared.append(_PreparedEdit(edit, path, before, _encode(updated, codec, bom)))
        except PermissionError:
            raise
        except (OSError, UnicodeError) as exc:
            raise PatchConflict(f"cannot prepare patch: {exc}") from exc
        return prepared

    def _write_temporary(self, prepared: list[_PreparedEdit]) -> None:
        try:
            for item in prepared:
                descriptor, raw_path = tempfile.mkstemp(
                    prefix=f".{item.path.name}.rabbit-patch-",
                    suffix=".tmp",
                    dir=item.path.parent,
                )
                item.temp_path = Path(raw_path)
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(item.after)
                    handle.flush()
                    os.fsync(handle.fileno())
                shutil.copystat(item.path, item.temp_path, follow_symlinks=False)
        except OSError as exc:
            raise PatchApplyError(f"cannot stage patch: {exc}") from exc

    def _check_concurrent_changes(self, prepared: list[_PreparedEdit]) -> None:
        for item in prepared:
            try:
                current = item.path.read_bytes()
            except OSError as exc:
                raise PatchConflict(f"target changed or disappeared: {item.path}") from exc
            if current != item.before:
                raise PatchConflict(f"target changed during patch: {item.path}")

    def _replace_all(self, prepared: list[_PreparedEdit]) -> None:
        try:
            for item in prepared:
                backup_path = self._temporary_path(item.path, ".bak")
                try:
                    self._replace(item.path, backup_path)
                except Exception:
                    backup_path.unlink(missing_ok=True)
                    raise
                item.backup_path = backup_path
                if item.temp_path is None:
                    raise PatchApplyError("missing staged patch")
                self._replace(item.temp_path, item.path)
        except Exception as exc:
            self._rollback(prepared)
            if isinstance(exc, PatchApplyError):
                raise
            raise PatchApplyError(f"atomic replacement failed: {exc}") from exc

    def _rollback(self, prepared: list[_PreparedEdit]) -> None:
        for item in reversed(prepared):
            backup = item.backup_path
            if backup is None or not backup.exists():
                continue
            try:
                self._replace(backup, item.path)
            except OSError:
                pass

    def _cleanup(self, prepared: list[_PreparedEdit]) -> None:
        for item in prepared:
            for candidate in (item.temp_path, item.backup_path):
                if candidate is not None:
                    candidate.unlink(missing_ok=True)

    def _replace(self, source: Path, destination: Path) -> None:
        os.replace(source, destination)

    def _temporary_path(self, path: Path, suffix: str) -> Path:
        descriptor, raw_path = tempfile.mkstemp(
            prefix=f".{path.name}.rabbit-patch-",
            suffix=suffix,
            dir=path.parent,
        )
        os.close(descriptor)
        return Path(raw_path)

    def _path(self, path: str | Path) -> Path:
        raw = Path(path).expanduser()
        candidate = raw if raw.is_absolute() else self.workspace_root / raw
        lexical = Path(os.path.abspath(candidate))
        try:
            lexical.relative_to(self.workspace_root)
        except ValueError as exc:
            raise PatchBoundaryError("patch path must remain within the workspace") from exc
        current = self.workspace_root
        for part in lexical.relative_to(self.workspace_root).parts:
            current /= part
            if current.is_symlink():
                raise PatchBoundaryError("symlink patch paths are not allowed")
        resolved = lexical.resolve()
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError as exc:
            raise PatchBoundaryError("patch path must remain within the workspace") from exc
        if not resolved.is_file():
            raise PatchError(f"patch target is not a file: {resolved}")
        return resolved


def parse_patch(
    payload: PatchEdit
    | str
    | Mapping[str, Any]
    | Sequence[PatchEdit | Mapping[str, Any]],
) -> tuple[PatchEdit, ...]:
    if isinstance(payload, PatchEdit):
        return (_parse_edit(payload),)
    value: Any = payload
    if isinstance(payload, str):
        try:
            value = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise PatchParseError(f"invalid patch JSON: {exc.msg}") from exc
    if isinstance(value, Mapping):
        raw_edits = value.get("edits", value.get("files"))
        if raw_edits is None:
            raw_edits = [value]
    else:
        raw_edits = value
    if isinstance(raw_edits, (str, bytes)) or not isinstance(raw_edits, Sequence):
        raise PatchParseError("patch edits must be a sequence")
    return tuple(_parse_edit(item) for item in raw_edits)


def _parse_edit(value: PatchEdit | Mapping[str, Any]) -> PatchEdit:
    if isinstance(value, PatchEdit):
        edit = value
    elif isinstance(value, Mapping):
        path = value.get("path")
        old_text = value.get("old_text", value.get("old"))
        new_text = value.get("new_text", value.get("new"))
        if not isinstance(path, (str, Path)):
            raise PatchParseError("patch path is required")
        if not isinstance(old_text, str) or not isinstance(new_text, str):
            raise PatchParseError("patch old_text and new_text must be strings")
        expected = value.get("expected_sha256")
        if expected is not None and not isinstance(expected, str):
            raise PatchParseError("expected_sha256 must be a string")
        edit = PatchEdit(path, old_text, new_text, expected)
    else:
        raise PatchParseError("each patch edit must be an object")
    if not edit.old_text:
        raise PatchParseError("patch old_text must be non-empty")
    if edit.expected_sha256 is not None and len(edit.expected_sha256) != 64:
        raise PatchParseError("expected_sha256 must be a SHA-256 hex digest")
    return edit


def _decode(data: bytes, path: Path) -> tuple[str, str, bytes]:
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig"), "utf-8", b"\xef\xbb\xbf"
    if data.startswith(b"\xff\xfe"):
        codec = "utf-16-le"
        bom = b"\xff\xfe"
        return data[2:].decode(codec), codec, bom
    if data.startswith(b"\xfe\xff"):
        codec = "utf-16-be"
        bom = b"\xfe\xff"
        return data[2:].decode(codec), codec, bom
    codec = "utf-8"
    bom = b""
    try:
        return data.decode(codec), codec, bom
    except UnicodeDecodeError as exc:
        raise PatchError(f"patch target is not supported text: {path}") from exc


def _encode(text: str, codec: str, bom: bytes) -> bytes:
    if codec == "utf-8" and bom:
        return bom + text.encode(codec)
    if codec in {"utf-16-le", "utf-16-be"}:
        return bom + text.encode(codec)
    return text.encode(codec)


def _line_ending(text: str) -> str:
    if "\r\n" in text:
        return "\r\n"
    if "\r" in text:
        return "\r"
    return "\n"


def _adapt_newlines(text: str, line_ending: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.replace("\n", line_ending)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _diff(path: Path, before: bytes, after: bytes) -> str:
    before_text, _, _ = _decode(before, path)
    after_text, _, _ = _decode(after, path)
    return "".join(
        difflib.unified_diff(
            before_text.splitlines(keepends=True),
            after_text.splitlines(keepends=True),
            fromfile=str(path),
            tofile=str(path),
        )
    )


PatchTool = AtomicPatchTool
