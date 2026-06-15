from __future__ import annotations

from prompt_optimizer.evaluation import EvaluationService
from prompt_optimizer.paths import DATA_ROOT
from prompt_optimizer.services import AppServices


def test_evaluation_report_contains_real_scores(tmp_path) -> None:  # type: ignore[no-untyped-def]
    services = AppServices()
    services.versions.storage.db_path = tmp_path / "evaluation.sqlite3"
    services.versions.storage._init_db()
    report = EvaluationService(services).run_markdown(
        DATA_ROOT / "evaluation" / "prompts.yml",
        "offline",
    )

    assert "# Prompt Optimizer 评测报告" in report
    assert "样本数：" in report
    assert "tech-001" in report
    assert "平均分数变化：" in report
