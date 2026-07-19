from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import IntEnum

# RC ID: RC-084. Allocate context tokens by importance and retain summary provenance.


class ContextTier(IntEnum):
    INSTRUCTION = 0
    TASK = 1
    RELATED = 2
    HISTORY = 3


@dataclass(frozen=True)
class ContextBlock:
    source: str
    content: str
    tier: ContextTier
    required: bool = False


@dataclass(frozen=True)
class CompressedBlock:
    source: str
    content: str
    tier: ContextTier
    is_summary: bool = False
    omitted_tokens: int = 0


@dataclass(frozen=True)
class CompressionResult:
    blocks: tuple[CompressedBlock, ...]
    estimated_tokens: int
    compressed: bool
    deduplicated: int
    warnings: tuple[str, ...]


def estimate_tokens(text: str) -> int:
    return max(1, (len(text.encode("utf-8")) + 3) // 4)


class ContextCompressor:
    def __init__(self, *, max_tokens: int) -> None:
        if max_tokens < 1:
            raise ValueError("max_tokens must be positive")
        self.max_tokens = max_tokens

    def compress(self, blocks: list[ContextBlock] | tuple[ContextBlock, ...]) -> CompressionResult:
        unique: list[ContextBlock] = []
        seen: set[str] = set()
        deduplicated = 0
        for block in blocks:
            fingerprint = hashlib.sha256(block.content.encode("utf-8")).hexdigest()
            if fingerprint in seen:
                deduplicated += 1
                continue
            seen.add(fingerprint)
            unique.append(block)
        ordered = sorted(unique, key=lambda block: block.tier)
        retained: list[CompressedBlock] = []
        remaining = self.max_tokens
        warnings: list[str] = []
        compressed = deduplicated > 0
        for block in ordered:
            tokens = estimate_tokens(block.content)
            if tokens <= remaining:
                retained.append(CompressedBlock(block.source, block.content, block.tier))
                remaining -= tokens
                continue
            if block.required and remaining > 0:
                content = _truncate_tokens(block.content, remaining)
                retained.append(CompressedBlock(block.source, content, block.tier))
                warnings.append(f"required context truncated: {block.source}")
                remaining = 0
                compressed = True
                continue
            if remaining <= 0:
                warnings.append(f"context omitted: {block.source}")
                compressed = True
                continue
            summary = _summary(block)
            summary_tokens = estimate_tokens(summary)
            if summary_tokens > remaining:
                summary = _truncate_tokens(summary, remaining)
                summary_tokens = estimate_tokens(summary)
            retained.append(
                CompressedBlock(
                    block.source,
                    summary,
                    block.tier,
                    is_summary=True,
                    omitted_tokens=max(0, tokens - summary_tokens),
                )
            )
            remaining -= summary_tokens
            warnings.append(f"context summarized: {block.source}")
            compressed = True
        return CompressionResult(
            tuple(retained),
            self.max_tokens - remaining,
            compressed,
            deduplicated,
            tuple(warnings),
        )


def _summary(block: ContextBlock) -> str:
    preview = " ".join(block.content.split())[:120]
    return f"[Summary source={block.source}] {preview}"


def _truncate_tokens(content: str, token_limit: int) -> str:
    byte_limit = max(1, token_limit * 4)
    return content.encode("utf-8")[:byte_limit].decode("utf-8", errors="ignore")
