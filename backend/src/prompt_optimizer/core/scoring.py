from __future__ import annotations

import re

from prompt_optimizer.core.models import ScoreBreakdown, ScoreDimension
from prompt_optimizer.core.rules import ScoringRule, load_scoring_rules


class ScoringEngine:
    def __init__(self, rules: list[ScoringRule] | None = None) -> None:
        self.rules = rules or load_scoring_rules()

    def score(self, prompt: str) -> ScoreBreakdown:
        normalized = self._normalize(prompt)
        dimensions = [self._score_dimension(normalized, rule) for rule in self.rules]
        weight_sum = sum(d.weight for d in dimensions)
        total = sum(d.score * d.weight for d in dimensions) / weight_sum if weight_sum else 0
        return ScoreBreakdown(total_score=round(total, 2), dimensions=dimensions)

    def _score_dimension(self, prompt: str, rule: ScoringRule) -> ScoreDimension:
        keyword_hits = sum(1 for keyword in rule.keywords if keyword.lower() in prompt)
        keyword_score = min(70, keyword_hits * 18)
        length_score = min(30, int((len(prompt) / max(rule.min_length, 1)) * 30))
        structure_bonus = self._structure_bonus(prompt)
        score = min(100, keyword_score + length_score + structure_bonus)
        reason = self._reason(score, keyword_hits, rule)
        return ScoreDimension(
            name=rule.id,
            label=rule.label,
            score=round(score, 2),
            weight=rule.weight,
            reason=reason,
        )

    @staticmethod
    def _normalize(prompt: str) -> str:
        return re.sub(r"\s+", " ", prompt.strip().lower())

    @staticmethod
    def _structure_bonus(prompt: str) -> int:
        bonus = 0
        if any(marker in prompt for marker in [":", "：", "-", "1.", "一、"]):
            bonus += 8
        if len(prompt.split()) >= 20 or len(prompt) >= 80:
            bonus += 7
        return bonus

    @staticmethod
    def _reason(score: float, keyword_hits: int, rule: ScoringRule) -> str:
        if score >= 80:
            return f"{rule.label}表现良好，已有明确线索。"
        if keyword_hits:
            return f"{rule.label}已有部分信息，但仍缺少可执行细节。"
        return f"未检测到足够的{rule.label}信息。"

