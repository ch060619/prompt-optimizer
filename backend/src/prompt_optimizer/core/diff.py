from __future__ import annotations

import difflib

from prompt_optimizer.core.models import DiffResult, PromptVersion
from prompt_optimizer.limits import DEFAULT_DATA_LIMITS, validate_limit


class DiffService:
    def compare(
        self,
        old: PromptVersion,
        new: PromptVersion,
        *,
        cursor: int = 0,
        max_bytes: int = DEFAULT_DATA_LIMITS.diff_bytes,
    ) -> DiffResult:
        if cursor < 0:
            raise ValueError("cursor must not be negative")
        validate_limit(
            max_bytes,
            name="max_bytes",
            maximum=DEFAULT_DATA_LIMITS.max_diff_bytes,
        )
        old_lines = old.optimized_prompt.splitlines()
        new_lines = new.optimized_prompt.splitlines()
        all_diff_lines = list(
            difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"version-{old.id}",
                tofile=f"version-{new.id}",
                lineterm="",
            )
        )
        encoded = "\n".join(all_diff_lines).encode("utf-8")
        if cursor > len(encoded):
            raise ValueError("cursor is beyond the end of the diff")
        chunk = encoded[cursor : cursor + max_bytes]
        next_cursor = cursor + len(chunk)
        old_score = old.analysis.score.total_score
        new_score = new.analysis.score.total_score
        return DiffResult(
            old_id=old.id,
            new_id=new.id,
            old_score=old_score,
            new_score=new_score,
            score_delta=round(new_score - old_score, 2),
            diff_lines=chunk.decode("utf-8", errors="ignore").splitlines(),
            truncated=next_cursor < len(encoded),
            original_bytes=len(encoded),
            next_cursor=next_cursor,
        )
