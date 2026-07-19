from __future__ import annotations

from pathlib import Path

import pytest
from backend.rabbit_code.content_blocks import (
    ContentBlock,
    ContentBlockError,
    ContentBlockRenderer,
    ContentBlockType,
    content_blocks_from_event,
)
from rabbit_code_protocol import Message

# RC ID: RC-098. Verify canonical blocks, protocol validation, and safe unknown fallback.


def test_all_known_blocks_have_one_canonical_shape() -> None:
    blocks = tuple(
        ContentBlock.from_mapping(value)
        for value in (
            {"type": "text", "text": "hello"},
            {"type": "diagnostic", "diagnostics": [{"severity": "error"}]},
            {"type": "diff", "diff": "-old\n+new"},
            {"type": "file", "path": "src/main.py"},
            {"type": "image", "mime_type": "image/png", "data": "base64"},
            {"type": "progress", "message": "working", "fraction": 0.5},
            {"type": "error", "code": "failed", "message": "nope"},
        )
    )
    rendered = ContentBlockRenderer()
    api = rendered.render(blocks, surface="api")
    cli = rendered.render(blocks, surface="cli")
    gui = rendered.render(blocks, surface="gui")
    assert api == cli == gui
    assert [item["type"] for item in api] == [item.value for item in ContentBlockType]


def test_unknown_block_is_preserved_and_has_safe_text_fallback() -> None:
    block = ContentBlock.from_mapping(
        {"type": "future_block", "payload": {"message": "value"}}
    )
    renderer = ContentBlockRenderer()

    assert block.to_dict()["type"] == "future_block"
    fallback = renderer.render((block,), surface="gui")[0]
    assert fallback["type"] == "text"
    assert fallback["source_type"] == "future_block"
    assert "value" in fallback["text"]


def test_event_content_is_consumed_without_private_result_reinterpretation() -> None:
    event = {
        "type": "tool_result",
        "payload": {
            "content": [
                {"type": "text", "text": "done"},
                {"type": "error", "code": "warning", "message": "check"},
            ]
        },
    }
    blocks = content_blocks_from_event(event)
    assert ContentBlockRenderer().render_event(event, surface="cli") == (
        {"type": "text", "text": "done"},
        {"type": "error", "code": "warning", "message": "check"},
    )
    assert blocks[0].type == "text"


def test_protocol_message_accepts_the_same_content_block_fixture() -> None:
    message = Message(
        role="tool",
        content=[
            {"type": "text", "text": "done"},
            {"type": "progress", "message": "complete", "fraction": 1},
        ],
    )
    assert message.content[1].type == "progress"


def test_known_block_required_fields_are_rejected(tmp_path: Path) -> None:
    del tmp_path
    with pytest.raises(ContentBlockError, match="missing"):
        ContentBlock.from_mapping({"type": "file"})
    with pytest.raises(ContentBlockError, match="must be a string"):
        ContentBlock.from_mapping({"type": "text", "text": 1})
