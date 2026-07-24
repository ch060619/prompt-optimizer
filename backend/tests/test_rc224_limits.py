from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from backend.rabbit_code.context_items import ContextCollector
from backend.rabbit_code.tool_results import BoundedOutput

from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.core.diff import DiffService
from prompt_optimizer.core.models import PromptVersion
from prompt_optimizer.limits import DEFAULT_DATA_LIMITS

# RC ID: RC-224. Verify shared limits, truncation metadata, and diff cursors.


def _version(version_id: int, text: str) -> PromptVersion:
    return PromptVersion(
        id=version_id,
        original_prompt=text,
        optimized_prompt=text,
        analysis=Analyzer().analyze(text),
        created_at=datetime.now(UTC),
    )


def test_bounded_output_reports_original_size_and_continuation_cursor() -> None:
    output = BoundedOutput(4)
    output.append(b"abcdef")

    metadata = output.metadata()
    assert metadata.truncated
    assert metadata.bytes_seen == 6
    assert metadata.original_bytes == 6
    assert metadata.next_cursor == 4


def test_context_and_attachment_limits_are_explicit(tmp_path: Path) -> None:
    collector = ContextCollector(tmp_path, max_text_bytes=4, max_attachment_bytes=4)
    item = collector.add_terminal("abcdef")

    assert item.truncated
    assert item.metadata["original_bytes"] == 6
    assert item.metadata["next_cursor"] == 4
    attachment = tmp_path / "large.bin"
    attachment.write_bytes(b"12345")
    with pytest.raises(ValueError, match="max_attachment_bytes"):
        collector.add_attachment(attachment)
    with pytest.raises(ValueError, match="maximum"):
        ContextCollector(tmp_path, max_text_bytes=DEFAULT_DATA_LIMITS.max_context_bytes + 1)


def test_diff_is_bounded_and_can_continue_from_the_reported_cursor() -> None:
    old = _version(1, "\n".join(f"old line {index}" for index in range(100)))
    new = _version(2, "\n".join(f"new line {index}" for index in range(100)))
    service = DiffService()

    first = service.compare(old, new, max_bytes=64)
    second = service.compare(old, new, cursor=first.next_cursor, max_bytes=64)

    assert first.truncated
    assert first.original_bytes > first.next_cursor
    assert second.original_bytes == first.original_bytes
    assert second.next_cursor > first.next_cursor
    with pytest.raises(ValueError, match="maximum"):
        service.compare(old, new, max_bytes=DEFAULT_DATA_LIMITS.max_diff_bytes + 1)
