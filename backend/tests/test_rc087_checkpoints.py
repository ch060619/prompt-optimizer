from __future__ import annotations

from pathlib import Path

import pytest
from backend.rabbit_code.checkpoints import CheckpointManager

# RC ID: RC-087. Verify baselines, grouped evidence, conflict safety, and partial rollback.


def test_checkpoint_records_group_tools_and_restores_proven_agent_changes(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("before", encoding="utf-8")
    checkpoint = CheckpointManager(tmp_path).create((source,))

    group_id = checkpoint.begin_group("rename source", (source,), tools=("edit",))
    source.write_text("after", encoding="utf-8")
    group = checkpoint.finish_group(group_id, verifications=("pytest",))

    assert group.tools == ("edit",)
    assert group.verifications == ("pytest",)
    assert group.changes[0].before_sha256 != group.changes[0].after_sha256

    report = checkpoint.rollback(group_id)
    assert report.scope == "rename source"
    assert report.restored == ("source.txt",)
    assert report.conflicts == ()
    assert source.read_text(encoding="utf-8") == "before"


def test_concurrent_user_edit_is_reported_and_never_overwritten(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("before", encoding="utf-8")
    checkpoint = CheckpointManager(tmp_path).create((source,))
    group_id = checkpoint.begin_group("agent edit", (source,), tools=("patch",))
    source.write_text("agent", encoding="utf-8")
    checkpoint.finish_group(group_id, verifications=("unit",))

    source.write_text("user concurrent edit", encoding="utf-8")
    report = checkpoint.rollback(group_id)

    assert report.restored == ()
    assert report.conflicts == ("source.txt",)
    assert source.read_text(encoding="utf-8") == "user concurrent edit"


def test_all_rollback_is_reverse_order_and_partial_conflicts_are_safe(tmp_path: Path) -> None:
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("first-0", encoding="utf-8")
    second.write_text("second-0", encoding="utf-8")
    checkpoint = CheckpointManager(tmp_path).create((first, second))

    group_one = checkpoint.begin_group("first group", (first,), tools=("write",))
    first.write_text("first-1", encoding="utf-8")
    checkpoint.finish_group(group_one, verifications=("check-1",))
    group_two = checkpoint.begin_group("second group", (second,), tools=("write",))
    second.write_text("second-1", encoding="utf-8")
    checkpoint.finish_group(group_two, verifications=("check-2",))

    second.write_text("user second", encoding="utf-8")
    report = checkpoint.rollback()

    assert report.scope == "all"
    assert report.restored == ("first.txt",)
    assert report.conflicts == ("second.txt",)
    assert first.read_text(encoding="utf-8") == "first-0"
    assert second.read_text(encoding="utf-8") == "user second"


def test_new_agent_file_is_removed_on_rollback_and_invalid_paths_are_rejected(
    tmp_path: Path,
) -> None:
    created = tmp_path / "created.txt"
    checkpoint = CheckpointManager(tmp_path).create((created,))
    group_id = checkpoint.begin_group("create file", (created,), tools=("create",))
    created.write_text("agent file", encoding="utf-8")
    checkpoint.finish_group(group_id, verifications=("test",))

    report = checkpoint.rollback()
    assert report.restored == ("created.txt",)
    assert not created.exists()

    with pytest.raises(ValueError, match="workspace"):
        CheckpointManager(tmp_path).create((tmp_path.parent / "outside.txt",))
