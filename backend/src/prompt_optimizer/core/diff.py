from __future__ import annotations

import difflib

from prompt_optimizer.core.models import DiffResult, PromptVersion


class DiffService:
    def compare(self, old: PromptVersion, new: PromptVersion) -> DiffResult:
        old_lines = old.optimized_prompt.splitlines()
        new_lines = new.optimized_prompt.splitlines()
        diff_lines = list(
            difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"version-{old.id}",
                tofile=f"version-{new.id}",
                lineterm="",
            )
        )
        old_score = old.analysis.score.total_score
        new_score = new.analysis.score.total_score
        return DiffResult(
            old_id=old.id,
            new_id=new.id,
            old_score=old_score,
            new_score=new_score,
            score_delta=round(new_score - old_score, 2),
            diff_lines=diff_lines,
        )

