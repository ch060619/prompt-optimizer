from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from prompt_optimizer.paths import DATA_ROOT


@dataclass(frozen=True)
class ScoringRule:
    id: str
    label: str
    weight: float
    keywords: list[str]
    min_length: int
    suggestion_title: str
    suggestion_detail: str
    suggestion_example: str


def load_scoring_rules(path: Path | None = None) -> list[ScoringRule]:
    rules_path = path or DATA_ROOT / "rules" / "scoring.yml"
    with rules_path.open("r", encoding="utf-8") as file:
        payload: dict[str, Any] = yaml.safe_load(file)
    return [
        ScoringRule(
            id=item["id"],
            label=item["label"],
            weight=float(item["weight"]),
            keywords=list(item.get("keywords", [])),
            min_length=int(item.get("min_length", 0)),
            suggestion_title=item["suggestion"]["title"],
            suggestion_detail=item["suggestion"]["detail"],
            suggestion_example=item["suggestion"]["example"],
        )
        for item in payload["dimensions"]
    ]

