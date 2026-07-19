from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import yaml

from prompt_optimizer.core.models import ModelProviderName
from prompt_optimizer.services import AppServices

# RC ID: RC-158. Keep evaluation protocol and fixed-seed reporting reproducible.


@dataclass(frozen=True)
class EvaluationCase:
    id: str
    category: str
    prompt: str
    expected_focus: str
    manual_label: str
    notes: str


@dataclass(frozen=True)
class EvaluationDataset:
    version: str
    random_seed: int
    automatic_scoring: dict[str, Any]
    blind_review: dict[str, Any]
    cases: list[EvaluationCase]


class EvaluationService:
    def __init__(self, services: AppServices) -> None:
        self.services = services

    def load_cases(self, path: Path) -> list[EvaluationCase]:
        return self.load_dataset(path).cases

    def load_dataset(self, path: Path) -> EvaluationDataset:
        with path.open("r", encoding="utf-8") as stream:
            payload: dict[str, Any] = yaml.safe_load(stream)
        if not isinstance(payload, dict):
            raise ValueError("评测集必须是 YAML 对象。")
        version = payload.get("dataset_version")
        random_seed = payload.get("random_seed")
        automatic_scoring = payload.get("automatic_scoring")
        blind_review = payload.get("blind_review")
        if not isinstance(version, str) or not version:
            raise ValueError("评测集缺少 dataset_version。")
        if not isinstance(random_seed, int):
            raise ValueError("评测集缺少整数 random_seed。")
        if not isinstance(automatic_scoring, dict) or not isinstance(blind_review, dict):
            raise ValueError("评测集必须定义 automatic_scoring 和 blind_review。")
        raw_cases = payload.get("cases")
        if not isinstance(raw_cases, list) or not raw_cases:
            raise ValueError("评测集至少需要一个样本。")
        cases = [
            EvaluationCase(
                id=str(item["id"]),
                category=str(item["category"]),
                prompt=str(item["prompt"]),
                expected_focus=str(item["expected_focus"]),
                manual_label=str(item["manual_label"]),
                notes=str(item.get("notes", "")),
            )
            for item in raw_cases
        ]
        return EvaluationDataset(
            version=version,
            random_seed=random_seed,
            automatic_scoring=automatic_scoring,
            blind_review=blind_review,
            cases=cases,
        )

    def run_markdown(self, dataset: Path, provider: ModelProviderName = "offline") -> str:
        evaluation_dataset = self.load_dataset(dataset)
        blind_review_ids = self._blind_review_ids(evaluation_dataset)
        rows: list[dict[str, object]] = []
        for case in evaluation_dataset.cases:
            started = perf_counter()
            before = self.services.analyzer.analyze(case.prompt)
            result = self.services.optimization.optimize(
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
                    "blind_review_id": blind_review_ids[case.id],
                }
            )
        return self._render_report(dataset, evaluation_dataset, rows)

    @staticmethod
    def _blind_review_ids(dataset: EvaluationDataset) -> dict[str, str]:
        case_ids = [case.id for case in dataset.cases]
        random.Random(dataset.random_seed).shuffle(case_ids)
        return {case_id: f"BR-{index:03d}" for index, case_id in enumerate(case_ids, start=1)}

    @staticmethod
    def _render_report(
        dataset: Path,
        evaluation_dataset: EvaluationDataset,
        rows: list[dict[str, object]],
    ) -> str:
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
            f"数据集版本：`{evaluation_dataset.version}`",
            f"随机种子：{evaluation_dataset.random_seed}",
            f"样本数：{len(rows)}",
            "分类分布："
            + ", ".join(
                f"{category}={count}"
                for category, count in sorted(Counter(row["category"] for row in rows).items())
            ),
            f"平均分数变化：{average_delta:.2f}",
            "",
            "自动评分："
            f"{evaluation_dataset.automatic_scoring['metric']}，"
            f"范围 {evaluation_dataset.automatic_scoring['range']}，"
            f"聚合 {evaluation_dataset.automatic_scoring['aggregate']}。",
            "双人盲评："
            f"{evaluation_dataset.blind_review['reviewers']} 位评审，"
            f"{evaluation_dataset.blind_review['assignment']}，"
            f"量表 {evaluation_dataset.blind_review['scale']}。",
            "",
            "| ID | 分类 | 优化前 | 优化后 | 变化 | 人工标签 | Provider | "
            "降级 | 耗时(ms) | 盲评批次 |",
            "| --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | --- |",
        ]
        for row in rows:
            lines.append(
                "| {id} | {category} | {before_score} | {after_score} | {score_delta} | "
                "{manual_label} | {provider} | {fallback} | {latency_ms} | "
                "{blind_review_id} |".format(**row)
            )
        lines.extend(["", "## 误判与人工备注", ""])
        for row in rows:
            lines.append(f"- `{row['id']}` {row['expected_focus']}；备注：{row['notes']}")
        lines.append("")
        return "\n".join(lines)
