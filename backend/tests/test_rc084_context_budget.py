from __future__ import annotations

from backend.rabbit_code.context_budget import (
    ContextBlock,
    ContextCompressor,
    ContextTier,
    estimate_tokens,
)

# RC ID: RC-084. Verify token estimation, tiered retention, deduplication, and source summaries.


def test_compressor_preserves_required_tiers_and_summarizes_overflow_with_sources() -> None:
    blocks = [
        ContextBlock("instructions/AGENTS.md", "必须遵循的项目规则", ContextTier.INSTRUCTION, True),
        ContextBlock("task", "当前任务必须完成安全压缩", ContextTier.TASK, True),
        ContextBlock("src/a.py", "相关文件内容 " * 20, ContextTier.RELATED),
        ContextBlock("history/1", "历史对话 " * 20, ContextTier.HISTORY),
    ]
    result = ContextCompressor(max_tokens=18).compress(blocks)

    assert [block.source for block in result.blocks[:2]] == ["instructions/AGENTS.md", "task"]
    assert result.estimated_tokens <= 18
    assert result.compressed
    summaries = [block for block in result.blocks if block.is_summary]
    assert summaries
    assert all(block.source for block in summaries)
    assert result.warnings


def test_compressor_deduplicates_content_before_allocating_budget() -> None:
    blocks = [
        ContextBlock("a.txt", "same content", ContextTier.RELATED),
        ContextBlock("b.txt", "same content", ContextTier.RELATED),
        ContextBlock("c.txt", "different", ContextTier.RELATED),
    ]

    result = ContextCompressor(max_tokens=20).compress(blocks)

    assert [block.source for block in result.blocks] == ["a.txt", "c.txt"]
    assert result.deduplicated == 1
    assert estimate_tokens("same content") > 0
