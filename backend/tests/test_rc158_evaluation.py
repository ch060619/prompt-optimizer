from __future__ import annotations

from pathlib import Path

from prompt_optimizer.evaluation import EvaluationService
from prompt_optimizer.services import AppServices

# RC ID: RC-158. Verify the dataset protocol and reproducible blind-review batches.

DATASET = Path(__file__).parents[2] / "data" / "evaluation" / "prompts.yml"


def test_rc158_dataset_protocol_covers_required_categories() -> None:
    dataset = EvaluationService(AppServices()).load_dataset(DATASET)
    categories = {case.category for case in dataset.cases}

    assert dataset.version == "rc-158-v1"
    assert dataset.random_seed == 158
    assert len(dataset.cases) >= 60
    assert {
        "tech",
        "business",
        "education",
        "creative",
        "long_text",
        "coding",
        "code_block",
        "variables",
        "chinese",
        "adversarial",
    } <= categories
    assert dataset.automatic_scoring["metric"] == "analyzer.total_score"
    assert dataset.blind_review["reviewers"] == 2


def test_rc158_report_contains_reproducibility_and_review_protocol() -> None:
    service = EvaluationService(AppServices())
    first = service.run_markdown(DATASET)
    second = service.run_markdown(DATASET)

    assert "数据集版本：`rc-158-v1`" in first
    assert "随机种子：158" in first
    assert "分类分布：" in first
    assert "自动评分：analyzer.total_score" in first
    assert "双人盲评：2 位评审" in first
    first_batches = [
        line.rstrip(" |").rsplit(" | ", 1)[-1]
        for line in first.splitlines()
        if "| BR-" in line
    ]
    second_batches = [
        line.rstrip(" |").rsplit(" | ", 1)[-1]
        for line in second.splitlines()
        if "| BR-" in line
    ]
    assert first_batches == second_batches
