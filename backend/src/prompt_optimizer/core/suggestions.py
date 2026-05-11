from __future__ import annotations

from typing import Literal

from prompt_optimizer.core.models import OptimizationSuggestion, ScoreBreakdown
from prompt_optimizer.core.rules import ScoringRule, load_scoring_rules


class SuggestionEngine:
    def __init__(self, rules: list[ScoringRule] | None = None) -> None:
        self.rules = {rule.id: rule for rule in (rules or load_scoring_rules())}

    def suggest(self, score: ScoreBreakdown) -> list[OptimizationSuggestion]:
        suggestions: list[OptimizationSuggestion] = []
        for dimension in score.dimensions:
            if dimension.score >= 82:
                continue
            rule = self.rules[dimension.name]
            priority: Literal["high", "medium", "low"]
            if dimension.score < 45:
                priority = "high"
            elif dimension.score < 70:
                priority = "medium"
            else:
                priority = "low"
            suggestions.append(
                OptimizationSuggestion(
                    dimension=rule.id,
                    title=rule.suggestion_title,
                    detail=rule.suggestion_detail,
                    example=rule.suggestion_example,
                    priority=priority,
                )
            )
        priority_order = {"high": 0, "medium": 1, "low": 2}
        return sorted(suggestions, key=lambda item: priority_order[item.priority])
