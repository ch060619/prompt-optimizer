from __future__ import annotations

from prompt_optimizer.core.models import PromptAnalysis
from prompt_optimizer.core.scoring import ScoringEngine
from prompt_optimizer.core.suggestions import SuggestionEngine

MAX_PROMPT_LENGTH = 12000


class Analyzer:
    def __init__(
        self,
        scoring_engine: ScoringEngine | None = None,
        suggestion_engine: SuggestionEngine | None = None,
    ) -> None:
        self.scoring_engine = scoring_engine or ScoringEngine()
        self.suggestion_engine = suggestion_engine or SuggestionEngine()

    def analyze(self, prompt: str) -> PromptAnalysis:
        clean_prompt = prompt.strip()
        if not clean_prompt:
            raise ValueError("提示词不能为空。")
        if len(clean_prompt) > MAX_PROMPT_LENGTH:
            raise ValueError(f"提示词长度不能超过 {MAX_PROMPT_LENGTH} 个字符。")
        score = self.scoring_engine.score(clean_prompt)
        suggestions = self.suggestion_engine.suggest(score)
        strengths = [
            dimension.label
            for dimension in score.dimensions
            if dimension.score >= 82
        ]
        return PromptAnalysis(
            prompt=clean_prompt,
            score=score,
            suggestions=suggestions,
            strengths=strengths,
        )

