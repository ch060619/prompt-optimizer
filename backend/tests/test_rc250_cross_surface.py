from __future__ import annotations

from pathlib import Path

from backend.rabbit_code.checkpoints import CheckpointManager

# RC ID: RC-250. Verify multi-file diff/checkpoint rollback and concurrent-edit protection.


def test_cli_and_gui_checkpoint_views_restore_only_agent_changes(tmp_path: Path) -> None:
    first = tmp_path / "first.py"
    second = tmp_path / "second.py"
    first.write_text("first-before", encoding="utf-8")
    second.write_text("second-before", encoding="utf-8")
    checkpoint = CheckpointManager(tmp_path).create((first, second))
    group_id = checkpoint.begin_group(
        "agent multi-file edit",
        (first, second),
        tools=("patch", "verification"),
    )
    first.write_text("first-agent", encoding="utf-8")
    second.write_text("second-agent", encoding="utf-8")
    group = checkpoint.finish_group(group_id, verifications=("pytest",))

    assert {change.path for change in group.changes} == {"first.py", "second.py"}
    assert group.verifications == ("pytest",)

    second.write_text("second-user-edit", encoding="utf-8")
    report = checkpoint.rollback(group_id)

    assert report.restored == ("first.py",)
    assert report.conflicts == ("second.py",)
    assert first.read_text(encoding="utf-8") == "first-before"
    assert second.read_text(encoding="utf-8") == "second-user-edit"
