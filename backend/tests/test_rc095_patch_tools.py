from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from backend.rabbit_code.patch_tools import (
    AtomicPatchTool,
    PatchApplyError,
    PatchConflict,
    PatchEdit,
    PatchParseError,
)
from backend.rabbit_code.permissions import PermissionMode, PermissionPolicy

# RC ID: RC-095. Verify structured, atomic, encoding-preserving patch application.


def _tool(tmp_path: Path) -> AtomicPatchTool:
    policy = PermissionPolicy(tmp_path)
    policy.switch_mode(PermissionMode.EDIT, explicit_confirmation=True)
    return AtomicPatchTool(tmp_path, permission_policy=policy)


def test_patch_preserves_unicode_and_crlf_and_checks_baseline(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    before = "标题\r\nold value\r\n"
    path.write_bytes(before.encode("utf-8"))
    digest = hashlib.sha256(before.encode("utf-8")).hexdigest()

    result = _tool(tmp_path).apply(
        {
            "edits": [
                {
                    "path": "notes.txt",
                    "old_text": "old value\n",
                    "new_text": "新 value\n",
                    "expected_sha256": digest,
                }
            ]
        }
    )

    assert result.atomic
    assert path.read_bytes() == "标题\r\n新 value\r\n".encode()
    assert result.files[0].before_sha256 == digest


def test_patch_preserves_utf16_big_endian_bom(tmp_path: Path) -> None:
    path = tmp_path / "utf16.txt"
    path.write_bytes(b"\xfe\xff" + "old\r\n".encode("utf-16-be"))

    _tool(tmp_path).apply(PatchEdit(path, "old", "new"))

    assert path.read_bytes() == b"\xfe\xff" + "new\r\n".encode("utf-16-be")


def test_multiple_files_are_applied_as_one_batch(tmp_path: Path) -> None:
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("one\n", encoding="utf-8")
    second.write_text("two\n", encoding="utf-8")

    result = _tool(tmp_path).apply(
        [
            PatchEdit(first, "one", "ONE"),
            {"path": "second.txt", "old_text": "two", "new_text": "TWO"},
        ]
    )

    assert len(result.files) == 2
    assert first.read_text(encoding="utf-8") == "ONE\n"
    assert second.read_text(encoding="utf-8") == "TWO\n"


def test_hash_or_context_conflict_writes_nothing(tmp_path: Path) -> None:
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("one\n", encoding="utf-8")
    second.write_text("two\n", encoding="utf-8")

    with pytest.raises(PatchConflict, match="context"):
        _tool(tmp_path).apply(
            [
                PatchEdit(first, "one", "ONE"),
                PatchEdit(second, "missing", "TWO"),
            ]
        )
    assert first.read_text(encoding="utf-8") == "one\n"
    assert second.read_text(encoding="utf-8") == "two\n"


def test_replacement_failure_rolls_back_all_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("one\n", encoding="utf-8")
    second.write_text("two\n", encoding="utf-8")
    tool = _tool(tmp_path)
    original_replace = tool._replace
    calls = 0

    def fail_on_second_file(source: Path, destination: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise OSError("simulated replacement failure")
        original_replace(source, destination)

    monkeypatch.setattr(tool, "_replace", fail_on_second_file)
    with pytest.raises(PatchApplyError, match="replacement"):
        tool.apply(
            [
                PatchEdit(first, "one", "ONE"),
                PatchEdit(second, "two", "TWO"),
            ]
        )
    assert first.read_text(encoding="utf-8") == "one\n"
    assert second.read_text(encoding="utf-8") == "two\n"
    assert not list(tmp_path.glob(".*.rabbit-patch-*"))


def test_structured_patch_validation_and_permission_are_explicit(tmp_path: Path) -> None:
    path = tmp_path / "file.txt"
    path.write_text("value", encoding="utf-8")
    tool = _tool(tmp_path)
    with pytest.raises(PatchParseError, match="old_text"):
        tool.apply({"path": "file.txt", "old_text": "", "new_text": "new"})
    with pytest.raises(PatchConflict, match="baseline"):
        tool.apply(
            {
                "path": "file.txt",
                "old_text": "value",
                "new_text": "new",
                "expected_sha256": "0" * 64,
            }
        )
    with pytest.raises(PermissionError, match="read-only"):
        AtomicPatchTool(tmp_path).apply(
            {"path": "file.txt", "old_text": "value", "new_text": "new"}
        )
