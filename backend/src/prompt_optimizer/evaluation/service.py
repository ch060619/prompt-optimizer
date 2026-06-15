from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import yaml

from prompt_optimizer.core.models import ModelProviderName
from prompt_optimizer.services import AppServices


@dataclass(frozen=True)
class EvaluationCase:
    id: str
    category: str
    prompt: str
    expected_focus: str
    manual_label: str
    notes: str


class EvaluationService:
    def __init__(self, services: AppServices) -> None:
        self.services = services

    def load_cases(self, path: Path) -> list[EvaluationCase]:
        with path.open("r", encoding="utf-8") as stream:
            payload: dict[str, Any] = yaml.safe_load(stream)
        return [
            EvaluationCase(
                id=str(item["id"]),
                category=str(item["category"]),
                prompt=str(item["prompt"]),
                expected_focus=str(item["expected_focus"]),
                manual_label=str(item["manual_label"]),
                notes=str(item.get("notes", "")),
            )
            for item in payload["cases"]
        ]

    def run_markdown(self, dataset: Path, provider: ModelProviderName = "offline") -> str:
        rows: list[dict[str, object]] = []
        for case in self.load_cases(dataset):
            started = perf_counter()
            before = self.services.analyzer.analyze(case.prompt)
            result = self.services.optimize_and_save(
                original_prompt=case.prompt,
                prompt=case.prompt,
                template=None,
                provider_name=provider,
            )
            latency_ms = int((perf_counter() - started) * 1000)
            rows.append(
                {
                    "id": case.id,
                    "category": case.category,
                    "before_score": before.score.total_score,
                    "after_score": result.analysis.score.total_score,
                    "score_delta": round(
                        result.analysis.score.total_score - before.score.total_score,
                        2,
                    ),
                    "manual_label": case.manual_label,
                    "expected_focus": case.expected_focus,
                    "notes": case.notes,
                    "provider": result.metadata.provider_used,
                    "fallback": result.metadata.fallback_used,
                    "latency_ms": latency_ms,
                }
            )
        return self._render_report(dataset, rows)

    @staticmethod
    def _render_report(dataset: Path, rows: list[dict[str, object]]) -> str:
        if rows:
            score_deltas = [
                row["score_delta"]
                for row in rows
                if isinstance(row["score_delta"], int | float)
            ]
            average_delta = sum(score_deltas) / len(score_deltas) if score_deltas else 0.0
        else:
            average_delta = 0.0
        lines = [
            "# Prompt Optimizer 评测报告",
            "",
            f"数据集：`{dataset.as_posix()}`",
            f"样本数：{len(rows)}",
            f"平均分数变化：{average_delta:.2f}",
            "",
            "| ID | 分类 | 优化前 | 优化后 | 变化 | 人工标签 | Provider | 降级 | 耗时(ms) |",
            "| --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: |",
        ]
        for row in rows:
            lines.append(
                "| {id} | {category} | {before_score} | {after_score} | {score_delta} | "
                "{manual_label} | {provider} | {fallback} | {latency_ms} |".format(**row)
            )
        lines.extend(["", "## 误判与人工备注", ""])
        for row in rows:
            lines.append(f"- `{row['id']}` {row['expected_focus']}；备注：{row['notes']}")
        lines.append("")
        return "\n".join(lines)
