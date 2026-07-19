from __future__ import annotations

from pathlib import Path
from threading import Event

import pytest
from backend.rabbit_code.search_index import SafeSearchIndexer, SearchCancelled

# RC ID: RC-083. Verify ignore merging, sensitive/symlink boundaries, incrementality, and cancel.


def test_index_omits_ignored_sensitive_binary_large_and_escaped_files(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
    (tmp_path / ".rabbitignore").write_text("rabbit-secret.txt\n", encoding="utf-8")
    (tmp_path / "keep.txt").write_text("needle here", encoding="utf-8")
    (tmp_path / "ignored.txt").write_text("do not index", encoding="utf-8")
    (tmp_path / "rabbit-secret.txt").write_text("do not index", encoding="utf-8")
    (tmp_path / ".env").write_text("SECRET=never-read", encoding="utf-8")
    (tmp_path / "binary.bin").write_bytes(b"\x00binary")
    (tmp_path / "large.txt").write_text("x" * 20, encoding="utf-8")
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    try:
        (tmp_path / "escape.txt").symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation is unavailable")

    indexer = SafeSearchIndexer(tmp_path, max_file_bytes=10)
    entries = indexer.scan()

    assert [entry.path.name for entry in entries] == ["keep.txt"]
    assert indexer.search("needle") == (tmp_path / "keep.txt",)


def test_index_reuses_unchanged_entries_and_cancels_scan(tmp_path: Path) -> None:
    for name in ("a.txt", "b.txt"):
        (tmp_path / name).write_text(name, encoding="utf-8")
    indexer = SafeSearchIndexer(tmp_path)
    first = indexer.scan()
    first_reads = indexer.read_count
    second = indexer.scan()

    assert second == first
    assert indexer.read_count == first_reads

    cancellation = Event()
    cancellation.set()
    with pytest.raises(SearchCancelled):
        indexer.scan(cancellation=cancellation)
