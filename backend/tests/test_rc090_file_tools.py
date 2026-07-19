from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from backend.rabbit_code.file_tools import (
    ConcurrentFileChangeError,
    FileBinaryError,
    FileBoundaryError,
    FileToolError,
    FileTools,
)
from backend.rabbit_code.permissions import PermissionMode, PermissionPolicy

# RC ID: RC-090. Verify file operations, bounds, binary/symlink, concurrency, and permissions.


def _tools(tmp_path: Path) -> FileTools:
    policy = PermissionPolicy(tmp_path)
    policy.switch_mode(PermissionMode.EDIT, explicit_confirmation=True)
    return FileTools(tmp_path, permission_policy=policy, max_file_bytes=100)


def test_file_tools_cover_normal_operations_and_emit_diffs(tmp_path: Path) -> None:
    tools = _tools(tmp_path)
    created = tools.create(Path("notes.txt"), "alpha\nbeta\n")
    assert "+++" in created.diff
    assert tools.read("notes.txt") == "alpha\nbeta\n"
    assert tools.search("beta") == (Path("notes.txt"),)
    assert [entry.path for entry in tools.list()] == [Path("notes.txt")]
    assert tools.edit(
        "notes.txt",
        "alpha\ngamma\n",
        expected_sha256=created.after_sha256,
    ).operation == "edit"
    edited_sha = tools.read("notes.txt")
    patch = tools.patch(
        "notes.txt",
        "gamma",
        "delta",
        expected_sha256=hashlib.sha256(edited_sha.encode("utf-8")).hexdigest(),
    )
    assert patch.operation == "patch"
    moved = tools.move("notes.txt", "moved.txt", expected_sha256=patch.after_sha256)
    assert moved.destination == Path("moved.txt")
    assert tools.read("moved.txt") == "alpha\ndelta\n"

    tools.permission_policy.switch_mode(PermissionMode.HIGH, explicit_confirmation=True)
    deleted = tools.delete("moved.txt", expected_sha256=moved.after_sha256, approval=True)
    assert deleted.operation == "delete"


def test_file_tools_reject_bounds_binary_large_and_symlink(tmp_path: Path) -> None:
    tools = _tools(tmp_path)
    (tmp_path / "binary.bin").write_bytes(b"\x00binary")
    with pytest.raises(FileBinaryError):
        tools.read("binary.bin")
    with pytest.raises(FileToolError, match="size"):
        tools.create("large.txt", "x" * 101)
    with pytest.raises(FileBoundaryError, match="workspace"):
        tools.read(tmp_path.parent / "outside.txt")
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    try:
        (tmp_path / "escape.txt").symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation is unavailable")
    with pytest.raises(FileBoundaryError, match="symlink"):
        tools.read("escape.txt")


def test_file_tools_reject_concurrent_edit_and_permission_denial(tmp_path: Path) -> None:
    policy = PermissionPolicy(tmp_path)
    tools = FileTools(tmp_path, permission_policy=policy)
    with pytest.raises(PermissionError, match="read-only"):
        tools.create("notes.txt", "initial")
    policy.switch_mode(PermissionMode.EDIT, explicit_confirmation=True)
    created = tools.create("notes.txt", "initial")
    (tmp_path / "notes.txt").write_text("user edit", encoding="utf-8")
    with pytest.raises(ConcurrentFileChangeError, match="changed"):
        tools.edit("notes.txt", "agent overwrite", expected_sha256=created.after_sha256)


def test_list_returns_relative_entries_and_patch_requires_unique_context(tmp_path: Path) -> None:
    tools = _tools(tmp_path)
    tools.create("a.txt", "same\n")
    tools.create("b.txt", "same\n")
    entries = tools.list()
    assert [entry.path for entry in entries] == [Path("a.txt"), Path("b.txt")]
    digest = __import__("hashlib").sha256(b"same\n").hexdigest()
    with pytest.raises(FileToolError, match="exactly once"):
        tools.patch("a.txt", "missing", "new", expected_sha256=digest)
