from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar


class StructuredInputError(ValueError):
    """Raised when an optimization result changes a protected input structure."""


@dataclass(frozen=True)
class ProtectedSegment:
    kind: str
    value: str
    start: int
    end: int


_FENCED_CODE = re.compile(r"(?ms)^[ \t]{0,3}```[^\n]*\n.*?^[ \t]{0,3}```[ \t]*$")
_OUTPUT_FORMAT = re.compile(
    r"(?im)^[ \t]*(?:输出格式|output format|response format|format)[ \t]*[:：].*$"
)
_ATTACHMENT = re.compile(
    r"(?:\[\[(?:attachment|附件):[^\]\n]+\]\]|"
    r"\[(?:attachment|附件):[^\]\n]+\]|"
    r"<(?:attachment|附件):[^>\n]+>|"
    r"(?:attachment|附件)://[^\s)\]]+)"
)
_PLACEHOLDER = re.compile(r"\{\{\s*[A-Za-z_][A-Za-z0-9_.-]*\s*\}\}")
_COMMAND_LINE = re.compile(r"(?m)^[ \t]*(?:\$\s+|>\s+)[^\n]+$")
_INLINE_CODE = re.compile(r"`[^`\n]+`")
_FILE_MENTION = re.compile(
    r"(?<![\w@])(?:@[A-Za-z0-9_.-]+(?:[\\/][A-Za-z0-9_.-]+)+|"
    r"@[A-Za-z0-9_.-]+\.[A-Za-z0-9_-]+)"
)
_SLASH_COMMAND = re.compile(r"(?<![\w/:])/[A-Za-z][A-Za-z0-9_.:-]*")
_MARKER = re.compile(r"\[\[RABBIT_CODE_PROTECTED_(\d+)\]\]")


@dataclass(frozen=True)
class StructuredPrompt:
    """Parse and protect user-authored prompt spans across Provider calls."""

    original: str
    segments: tuple[ProtectedSegment, ...]

    _recognizers: ClassVar[tuple[tuple[str, re.Pattern[str]], ...]] = (
        ("code_block", _FENCED_CODE),
        ("output_format", _OUTPUT_FORMAT),
        ("attachment", _ATTACHMENT),
        ("placeholder", _PLACEHOLDER),
        ("command", _COMMAND_LINE),
        ("inline_code", _INLINE_CODE),
        ("file_mention", _FILE_MENTION),
        ("command", _SLASH_COMMAND),
    )

    @classmethod
    def parse(cls, prompt: str) -> StructuredPrompt:
        if _MARKER.search(prompt):
            raise StructuredInputError("提示词包含保留结构标记，请移除后重试。")
        if len(re.findall(r"(?m)^[ \t]{0,3}```", prompt)) % 2:
            raise StructuredInputError("代码围栏未闭合，结果未采用，请修正后重试。")

        candidates: list[tuple[int, int, str]] = []
        for kind, recognizer in cls._recognizers:
            candidates.extend(
                (match.start(), match.end(), kind) for match in recognizer.finditer(prompt)
            )
        candidates.sort(key=lambda item: (item[0], item[1]))

        accepted: list[ProtectedSegment] = []
        for start, end, kind in candidates:
            if any(start < item.end and item.start < end for item in accepted):
                continue
            accepted.append(ProtectedSegment(kind, prompt[start:end], start, end))
        return cls(prompt, tuple(accepted))

    def protect(self) -> str:
        if not self.segments:
            return self.original
        pieces: list[str] = []
        cursor = 0
        for index, segment in enumerate(self.segments):
            pieces.append(self.original[cursor : segment.start])
            pieces.append(self._marker(index))
            cursor = segment.end
        pieces.append(self.original[cursor:])
        return "".join(pieces)

    def language_text(self) -> str:
        """Mask protected spans before counting language scripts."""
        if not self.segments:
            return self.original
        pieces: list[str] = []
        cursor = 0
        for segment in self.segments:
            pieces.append(self.original[cursor : segment.start])
            pieces.append(" " * (segment.end - segment.start))
            cursor = segment.end
        pieces.append(self.original[cursor:])
        return "".join(pieces)

    def validate(self, output: str) -> str:
        """Restore protected markers and reject missing, changed, or duplicated spans."""
        if not self.segments:
            if _MARKER.search(output):
                raise StructuredInputError("优化结果包含未知结构标记，结果未采用，请重试。")
            return output

        expected = {
            self._marker(index): segment.value for index, segment in enumerate(self.segments)
        }
        output_markers = [match.group(0) for match in _MARKER.finditer(output)]
        if output_markers:
            if set(output_markers) != set(expected) or any(
                output_markers.count(marker) != 1 for marker in expected
            ):
                raise StructuredInputError("优化结果破坏了结构化输入，结果未采用，请重试。")
            restored = output
            for marker, value in expected.items():
                restored = restored.replace(marker, value)
        else:
            restored = output

        try:
            observed = self.parse(restored)
        except StructuredInputError:
            raise
        if observed.signature() != self.signature():
            raise StructuredInputError("优化结果破坏了结构化输入，结果未采用，请重试。")
        return restored

    def signature(self) -> tuple[tuple[str, str], ...]:
        return tuple((segment.kind, segment.value) for segment in self.segments)

    @staticmethod
    def _marker(index: int) -> str:
        return f"[[RABBIT_CODE_PROTECTED_{index}]]"
