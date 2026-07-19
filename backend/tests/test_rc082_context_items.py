from __future__ import annotations

from pathlib import Path

import pytest
from backend.rabbit_code.context_items import ContextCollector, ContextItemType

# RC ID: RC-082. Verify bounded file, selection, attachment, terminal, diff, and diagnostic context.


def test_collector_merges_supported_context_items_and_bounds_text(tmp_path: Path) -> None:
    source = tmp_path / "src.py"
    source.write_text("line 1\nline 2\nline 3\n", encoding="utf-8")
    image = tmp_path / "screen.png"
    image.write_bytes(b"png-bytes")

    collector = ContextCollector(tmp_path, max_text_bytes=15)
    collector.add_file(source)
    collector.add_selection(source, start_line=2, end_line=3)
    collector.add_attachment(image)
    collector.add_terminal("0123456789abcdef")
    collector.add_diff("diff --git a/src.py b/src.py")
    collector.add_diagnostic("src.py:2: error")

    assert [item.kind for item in collector.items] == [
        ContextItemType.FILE,
        ContextItemType.SELECTION,
        ContextItemType.IMAGE,
        ContextItemType.TERMINAL,
        ContextItemType.DIFF,
        ContextItemType.DIAGNOSTIC,
    ]
    assert collector.items[0].truncated
    assert collector.items[1].content == "line 2\nline 3\n"
    assert collector.items[2].metadata["mime_type"] == "image/png"
    assert collector.items[3].truncated


def test_directory_collection_is_workspace_bounded_and_ignores_dependencies(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "ignored.js").write_text("ignored", encoding="utf-8")
    collector = ContextCollector(tmp_path)

    collector.add_directory(tmp_path)

    assert [item.path.name for item in collector.items] == ["a.txt"]
    with pytest.raises(ValueError, match="workspace"):
        collector.add_file(tmp_path.parent / "outside.txt")
