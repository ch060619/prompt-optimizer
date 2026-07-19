from __future__ import annotations

from pathlib import Path

import pytest
from backend.rabbit_code.input_editor import (
    AttachmentError,
    InputEditor,
    PasteConfirmationRequired,
)

# RC ID: RC-102. Verify multiline Unicode input, history, completion, mentions,
# attachments, and paste safety.


def test_multiline_unicode_ime_input_and_history_restore() -> None:
    editor = InputEditor(completion_candidates=("/help", "/history"))
    editor.insert("第一行")
    editor.newline()
    editor.insert("第二行 输入法")
    submitted = editor.submit()

    assert submitted == "第一行\n第二行 输入法"
    assert editor.history_up() == submitted
    assert editor.history_down() == ""


def test_history_search_and_completion_are_deterministic() -> None:
    editor = InputEditor(completion_candidates=("/help", "/history", "/model"))
    for value in ("alpha prompt", "beta prompt", "alpha again"):
        editor.set_text(value)
        editor.submit()

    assert editor.search_history("ALPHA") == ("alpha again", "alpha prompt")
    assert editor.complete("/h") == ("/help", "/history")


def test_mentions_and_attachments_are_workspace_bounded(tmp_path: Path) -> None:
    source = tmp_path / "src.py"
    image = tmp_path / "image.png"
    source.write_text("print(1)", encoding="utf-8")
    image.write_bytes(b"png")
    editor = InputEditor(workspace_root=tmp_path)

    mentions = editor.mention_paths("Please inspect @src.py")
    attachment = editor.attach(image)

    assert mentions == (source.resolve(),)
    assert attachment.kind == "image"
    with pytest.raises(AttachmentError, match="workspace"):
        editor.attach(tmp_path.parent / "outside.txt")


def test_large_paste_requires_confirmation_but_small_paste_is_direct() -> None:
    editor = InputEditor(paste_limit_chars=3)
    editor.paste("abc")
    with pytest.raises(PasteConfirmationRequired, match="explicit confirmation"):
        editor.paste("long paste")
    editor.paste("long paste", confirm=True)
    assert editor.text == "abclong paste"
