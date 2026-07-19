from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

# RC ID: RC-102. Provide Unicode-safe multiline input, history, completion,
# mentions, and paste guards.


class InputEditorError(ValueError):
    pass


class PasteConfirmationRequired(InputEditorError):
    pass


class AttachmentError(InputEditorError):
    pass


@dataclass(frozen=True)
class Attachment:
    path: Path
    kind: str


@dataclass(frozen=True)
class ShortcutConfig:
    values: Mapping[str, str] = field(
        default_factory=lambda: {
            "submit": "enter",
            "newline": "shift+enter",
            "history_up": "up",
            "history_down": "down",
        }
    )

    def __post_init__(self) -> None:
        normalized = {str(key): str(value) for key, value in self.values.items()}
        if any(not key or not value for key, value in normalized.items()):
            raise InputEditorError("shortcut names and values must be non-empty")
        object.__setattr__(self, "values", normalized)


class InputEditor:
    def __init__(
        self,
        *,
        workspace_root: Path | None = None,
        completion_candidates: Iterable[str] = (),
        shortcuts: ShortcutConfig | None = None,
        paste_limit_chars: int = 2000,
    ) -> None:
        if paste_limit_chars <= 0:
            raise ValueError("paste_limit_chars must be positive")
        self.workspace_root = workspace_root.expanduser().resolve() if workspace_root else None
        self.paste_limit_chars = paste_limit_chars
        self.shortcuts = shortcuts or ShortcutConfig()
        self._text = ""
        self._cursor = 0
        self._history: list[str] = []
        self._history_index: int | None = None
        self._completion_candidates = tuple(
            dict.fromkeys(str(item) for item in completion_candidates)
        )
        self._attachments: list[Attachment] = []

    @property
    def text(self) -> str:
        return self._text

    @property
    def cursor(self) -> int:
        return self._cursor

    @property
    def attachments(self) -> tuple[Attachment, ...]:
        return tuple(self._attachments)

    @property
    def history(self) -> tuple[str, ...]:
        return tuple(self._history)

    def set_text(self, text: str) -> None:
        self._require_text(text)
        self._text = text
        self._cursor = len(text)
        self._history_index = None

    def insert(self, text: str) -> None:
        self._require_text(text)
        self._text = self._text[: self._cursor] + text + self._text[self._cursor :]
        self._cursor += len(text)

    def newline(self) -> None:
        self.insert("\n")

    def backspace(self) -> None:
        if self._cursor == 0:
            return
        self._text = self._text[: self._cursor - 1] + self._text[self._cursor :]
        self._cursor -= 1

    def move_cursor(self, offset: int) -> None:
        self._cursor = max(0, min(len(self._text), self._cursor + offset))

    def paste(self, text: str, *, confirm: bool = False) -> None:
        self._require_text(text)
        if len(text) > self.paste_limit_chars and not confirm:
            raise PasteConfirmationRequired(
                f"paste has {len(text)} characters; explicit confirmation is required"
            )
        self.insert(text)

    def submit(self) -> str:
        if not self._text.strip():
            raise InputEditorError("cannot submit an empty prompt")
        submitted = self._text
        if not self._history or self._history[-1] != submitted:
            self._history.append(submitted)
        self._text = ""
        self._cursor = 0
        self._history_index = None
        return submitted

    def history_up(self) -> str:
        if not self._history:
            return self._text
        index = (
            len(self._history) - 1
            if self._history_index is None
            else max(0, self._history_index - 1)
        )
        self._history_index = index
        self.set_text(self._history[index])
        self._history_index = index
        return self._text

    def history_down(self) -> str:
        if self._history_index is None:
            return self._text
        if self._history_index >= len(self._history) - 1:
            self._history_index = None
            self.set_text("")
            return self._text
        next_index = self._history_index + 1
        self.set_text(self._history[next_index])
        self._history_index = next_index
        return self._text

    def search_history(self, query: str) -> tuple[str, ...]:
        needle = query.casefold()
        return tuple(item for item in reversed(self._history) if needle in item.casefold())

    def complete(self, prefix: str) -> tuple[str, ...]:
        return tuple(item for item in self._completion_candidates if item.startswith(prefix))

    def mention_paths(self, text: str | None = None) -> tuple[Path, ...]:
        source = self._text if text is None else text
        mentions: list[Path] = []
        for raw in re.findall(r"(?<![\w])@([A-Za-z0-9_./\\-]+)", source):
            path = Path(raw)
            resolved = self._resolve_workspace_path(path)
            if resolved is not None and resolved not in mentions:
                mentions.append(resolved)
        return tuple(mentions)

    def attach(self, path: str | Path, *, kind: str | None = None) -> Attachment:
        resolved = self._resolve_workspace_path(Path(path))
        if resolved is None or not resolved.is_file():
            raise AttachmentError("attachment must be an existing workspace file")
        attachment_kind = kind or _kind_for_path(resolved)
        if attachment_kind not in {"text", "image", "file"}:
            raise AttachmentError("unsupported attachment kind")
        attachment = Attachment(resolved, attachment_kind)
        if attachment not in self._attachments:
            self._attachments.append(attachment)
        return attachment

    def _resolve_workspace_path(self, path: Path) -> Path | None:
        if self.workspace_root is None:
            return path.expanduser().resolve()
        candidate = path.expanduser()
        candidate = candidate if candidate.is_absolute() else self.workspace_root / candidate
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError:
            return None
        return resolved

    def _require_text(self, text: str) -> None:
        if not isinstance(text, str):
            raise InputEditorError("editor input must be text")


def _kind_for_path(path: Path) -> str:
    if path.suffix.casefold() in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        return "image"
    if path.suffix.casefold() in {".txt", ".md", ".py", ".ts", ".tsx", ".json"}:
        return "text"
    return "file"
