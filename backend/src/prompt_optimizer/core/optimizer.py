from __future__ import annotations

from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.core.models import PromptAnalysis, PromptTemplate


class Optimizer:
    def __init__(self, analyzer: Analyzer | None = None) -> None:
        self.analyzer = analyzer or Analyzer()

    def optimize(self, prompt: str, template: PromptTemplate | None = None) -> PromptAnalysis:
        analysis = self.analyzer.analyze(prompt)
        sections = [
            "请基于以下要求完成任务：",
            f"目标：{prompt.strip()}",
        ]
        if template:
            sections.append(f"可参考模板：\n{template.template}")
        sections.extend(
            [
                "上下文：说明任务背景、受众、使用场景和重要限制。",
                "输出要求：使用清晰标题、分点结构，并给出可执行结果。",
                "质量标准：内容准确、具体、可验证；必要时说明假设和风险。",
            ]
        )
        for suggestion in analysis.suggestions[:5]:
            sections.append(f"改进点 - {suggestion.title}：{suggestion.example}")
        optimized = "\n\n".join(sections)
        optimized_analysis = self.analyzer.analyze(optimized)
        optimized_analysis.optimized_prompt = optimized
        return optimized_analysis

