from __future__ import annotations

from pathlib import Path
from threading import Event

import pytest
from backend.rabbit_code.search_index import SafeSearchIndexer, SearchCancelled

# RC ID: RC-223. Verify background bounded scanning and cancellation semantics.


def test_background_scan_reuses_filters_and_returns_incremental_entries(tmp_path: Path) -> None:
    for index in range(12):
        (tmp_path / f"module-{index}.py").write_text(f"needle = {index}", encoding="utf-8")
    (tmp_path / ".env").write_text("SECRET=not-indexed", encoding="utf-8")

    indexer = SafeSearchIndexer(tmp_path, max_queue_size=2)
    handle = indexer.start_background_scan()

    entries = handle.wait(timeout=5)

    assert handle.status == "completed"
    assert len(entries) == 12
    assert indexer.search("needle") == tuple(entry.path for entry in entries)
    assert all(entry.path.name != ".env" for entry in entries)


def test_background_scan_can_be_cancelled_before_consuming_paths(tmp_path: Path) -> None:
    (tmp_path / "module.py").write_text("content", encoding="utf-8")
    cancellation = Event()
    cancellation.set()
    indexer = SafeSearchIndexer(tmp_path, max_queue_size=1)
    handle = indexer.start_background_scan(cancellation=cancellation)

    with pytest.raises(SearchCancelled):
        handle.wait(timeout=5)
    assert handle.status == "cancelled"


def test_background_scan_queue_size_is_bounded() -> None:
    with pytest.raises(ValueError, match="max_queue_size"):
        SafeSearchIndexer(Path("."), max_queue_size=0)
