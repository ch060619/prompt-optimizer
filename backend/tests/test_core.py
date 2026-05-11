from __future__ import annotations

from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.core.optimizer import Optimizer
from prompt_optimizer.templates.manager import TemplateManager


def test_analyzer_scores_complete_prompt() -> None:
    prompt = (
        "你是一名资深 Python 工程师。目标：生成一个 FastAPI 接口。"
        "背景：用于本地工具。输出格式：Markdown 表格。限制：不要引入外部服务。"
        "请给出步骤、示例输入输出和测试用例。"
    )
    analysis = Analyzer().analyze(prompt)
    assert analysis.score.total_score > 60
    assert analysis.suggestions


def test_analyzer_rejects_empty_prompt() -> None:
    try:
        Analyzer().analyze("   ")
    except ValueError as exc:
        assert "不能为空" in str(exc)
    else:
        raise AssertionError("empty prompt should fail")


def test_optimizer_generates_improved_prompt() -> None:
    analysis = Optimizer().optimize("帮我写一封邮件")
    assert analysis.optimized_prompt is not None
    assert "输出要求" in analysis.optimized_prompt
    assert analysis.score.total_score > 0


def test_template_manager_loads_categories() -> None:
    manager = TemplateManager()
    templates = manager.list_templates("tech")
    assert templates
    assert manager.get("tech-code-generation").name == "代码生成"
    assert "tech" in manager.categories()

