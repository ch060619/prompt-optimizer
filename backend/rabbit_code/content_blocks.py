from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from .public_output import safe_json_dumps, sanitize_public_payload

# RC ID: RC-098. Normalize tool results into one cross-surface content protocol.


class ContentBlockError(ValueError):
    pass


class ContentBlockType(StrEnum):
    TEXT = "text"
    DIAGNOSTIC = "diagnostic"
    DIFF = "diff"
    FILE = "file"
    IMAGE = "image"
    PROGRESS = "progress"
    ERROR = "error"


KNOWN_BLOCK_TYPES = frozenset(item.value for item in ContentBlockType)
REQUIRED_FIELDS: dict[str, frozenset[str]] = {
    ContentBlockType.TEXT: frozenset({"text"}),
    ContentBlockType.DIAGNOSTIC: frozenset({"diagnostics"}),
    ContentBlockType.DIFF: frozenset({"diff"}),
    ContentBlockType.FILE: frozenset({"path"}),
    ContentBlockType.IMAGE: frozenset({"mime_type", "data"}),
    ContentBlockType.PROGRESS: frozenset({"message"}),
    ContentBlockType.ERROR: frozenset({"code", "message"}),
}


@dataclass(frozen=True)
class ContentBlock:
    type: str
    payload: Mapping[str, Any]
    known: bool = True

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> ContentBlock:
        if not isinstance(value, Mapping):
            raise ContentBlockError("content block must be an object")
        block_type = value.get("type")
        if not isinstance(block_type, str) or not block_type:
            raise ContentBlockError("content block type is required")
        payload = {str(key): item for key, item in value.items() if key != "type"}
        return make_content_block(block_type, payload)

    def to_dict(self) -> dict[str, Any]:
        sanitized = sanitize_public_payload(dict(self.payload))
        if not isinstance(sanitized, dict):
            raise ContentBlockError("content block payload must remain an object")
        if self.known:
            return {"type": self.type, **sanitized}
        return {"type": self.type, "payload": sanitized}

    def fallback(self) -> dict[str, Any]:
        if self.known:
            return self.to_dict()
        return {
            "type": ContentBlockType.TEXT.value,
            "text": f"Unsupported content block '{self.type}': {safe_json_dumps(self.payload)}",
            "source_type": self.type,
        }


def make_content_block(block_type: str, payload: Mapping[str, Any]) -> ContentBlock:
    if not isinstance(block_type, str) or not block_type:
        raise ContentBlockError("content block type is required")
    if not isinstance(payload, Mapping):
        raise ContentBlockError("content block payload must be an object")
    normalized = {str(key): value for key, value in payload.items()}
    if block_type not in KNOWN_BLOCK_TYPES:
        return ContentBlock(block_type, normalized, known=False)
    required = REQUIRED_FIELDS[block_type]
    missing = required.difference(normalized)
    if missing:
        raise ContentBlockError(
            f"{block_type} content block is missing: {', '.join(sorted(missing))}"
        )
    if block_type in {ContentBlockType.TEXT, ContentBlockType.DIFF} and not isinstance(
        normalized[next(iter(required))], str
    ):
        raise ContentBlockError(f"{block_type} content block text must be a string")
    if block_type in {ContentBlockType.FILE, ContentBlockType.IMAGE}:
        for key in required:
            if not isinstance(normalized[key], str):
                raise ContentBlockError(f"{block_type} content block field must be a string")
    if block_type is ContentBlockType.ERROR:
        if not all(isinstance(normalized[key], str) for key in ("code", "message")):
            raise ContentBlockError("error content block code and message must be strings")
    if block_type is ContentBlockType.PROGRESS and not isinstance(normalized["message"], str):
        raise ContentBlockError("progress content block message must be a string")
    return ContentBlock(block_type, normalized)


def content_blocks_from_event(event: Mapping[str, Any]) -> tuple[ContentBlock, ...]:
    if not isinstance(event, Mapping):
        raise ContentBlockError("event must be an object")
    raw_content = event.get("content")
    if raw_content is None:
        payload = event.get("payload")
        if isinstance(payload, Mapping):
            raw_content = payload.get("content", [])
    if isinstance(raw_content, (str, bytes)) or not isinstance(raw_content, Sequence):
        raise ContentBlockError("event content must be a sequence")
    return tuple(
        ContentBlock.from_mapping(item)
        for item in raw_content
        if isinstance(item, Mapping)
    )


class ContentBlockRenderer:
    """Return the same canonical snapshot for every presentation surface."""

    def render(
        self,
        blocks: Sequence[ContentBlock],
        *,
        surface: str = "api",
    ) -> tuple[dict[str, Any], ...]:
        del surface
        return tuple(block.fallback() for block in blocks)

    def render_event(
        self,
        event: Mapping[str, Any],
        *,
        surface: str = "api",
    ) -> tuple[dict[str, Any], ...]:
        return self.render(content_blocks_from_event(event), surface=surface)
