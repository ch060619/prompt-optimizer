from __future__ import annotations

import re
import sys
from pathlib import Path


def _run_fast_analyze(prompt: str) -> None:
    """Handle the common offline analyze path without importing the Pydantic graph."""
    clean_prompt = prompt.strip()
    if not clean_prompt:
        raise SystemExit("提示词不能为空。")
    if len(clean_prompt) > 12000:
        raise SystemExit("提示词长度不能超过 12000 个字符。")
    rules_path = Path(__file__).resolve().parents[4] / "data" / "rules" / "scoring.yml"
    rules: list[tuple[float, list[str], int]] = []
    current_weight: float | None = None
    current_keywords: list[str] = []
    current_minimum_length: int | None = None
    for line in rules_path.read_text(encoding="utf-8").splitlines():
        if re.match(r"\s*- id:\s*\S+", line):
            if current_weight is not None and current_minimum_length is not None:
                rules.append((current_weight, current_keywords, current_minimum_length))
            current_weight = None
            current_keywords = []
            current_minimum_length = None
        elif match := re.match(r"\s+weight:\s*([0-9.]+)", line):
            current_weight = float(match.group(1))
        elif match := re.match(r"\s+keywords:\s*\[(.*)\]", line):
            current_keywords = re.findall(r'"([^"]+)"', match.group(1))
        elif match := re.match(r"\s+min_length:\s*(\d+)", line):
            current_minimum_length = int(match.group(1))
    if current_weight is not None and current_minimum_length is not None:
        rules.append((current_weight, current_keywords, current_minimum_length))
    normalized = " ".join(clean_prompt.lower().split())
    weighted_total = 0.0
    weight_sum = 0.0
    for weight, keywords, minimum_length in rules:
        hits = sum(1 for keyword in keywords if keyword.lower() in normalized)
        keyword_score = min(70, hits * 18)
        length_score = min(30, int(len(clean_prompt) / max(minimum_length, 1) * 30))
        structure_bonus = (
            8
            if any(marker in clean_prompt for marker in (":", "：", "-", "1.", "一、"))
            else 0
        )
        if len(clean_prompt.split()) >= 20 or len(clean_prompt) >= 80:
            structure_bonus += 7
        weighted_total += min(100, keyword_score + length_score + structure_bonus) * weight
        weight_sum += weight
    total = round(weighted_total / weight_sum, 2) if weight_sum else 0
    print(f"总分：{total}/100")


def main() -> None:
    # The full Typer app imports the Agent Core and every optional surface. Keep
    # the default offline command responsive while preserving the full app for
    # all other commands and options.
    if len(sys.argv) == 3 and sys.argv[1] == "analyze":
        _run_fast_analyze(sys.argv[2])
        return

    from prompt_optimizer.cli.app import app

    app()


if __name__ == "__main__":
    main()
