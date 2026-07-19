from __future__ import annotations

from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.core.language import LanguageProfile
from prompt_optimizer.core.models import OptimizationTargets, PromptAnalysis, PromptTemplate
from prompt_optimizer.core.structure import StructuredPrompt


# RC ID: RC-154. Apply explicit targets only in the offline rule implementation.
class Optimizer:
    def __init__(self, analyzer: Analyzer | None = None) -> None:
        self.analyzer = analyzer or Analyzer()

    def optimize(
        self,
        prompt: str,
        template: PromptTemplate | None = None,
        language_profile: LanguageProfile | None = None,
        targets: OptimizationTargets | None = None,
    ) -> PromptAnalysis:
        analysis = self.analyzer.analyze(prompt)
        profile = language_profile or LanguageProfile.detect(
            StructuredPrompt.parse(prompt).language_text()
        )
        selected = targets or OptimizationTargets()
        if profile.primary == "en":
            sections = [
                "Complete the following task based on the requirements:",
                f"Goal: {prompt.strip()}",
            ]
        else:
            sections = [
                "请基于以下要求完成任务：",
                f"目标：{prompt.strip()}",
            ]
        if template:
            sections.append(
                f"Reference template:\n{template.template}"
                if profile.primary == "en"
                else f"可参考模板：\n{template.template}"
            )
        if profile.primary == "en" and targets is None:
            sections.extend(
                [
                    "Context: explain the background, audience, usage, and important constraints.",
                    "Output requirements: use clear headings, structured points, "
                    "and an actionable result.",
                    "Quality criteria: be accurate, specific, and verifiable; "
                    "state assumptions and risks when needed.",
                ]
            )
        elif targets is None:
            sections.extend(
                [
                    "上下文：说明任务背景、受众、使用场景和重要限制。",
                    "输出要求：使用清晰标题、分点结构，并给出可执行结果。",
                    "质量标准：内容准确、具体、可验证；必要时说明假设和风险。",
                ]
            )
        if profile.primary == "en":
            target_sections = {
                "clarity": "Clarity: define terms, inputs, and expected outcomes.",
                "completeness": (
                    "Completeness: cover background, edge cases, and verification criteria."
                ),
                "constraints": (
                    "Constraints: state boundaries, exclusions, and non-negotiable rules."
                ),
                "format": (
                    "Output format: use clear headings, structured points, "
                    "and an actionable result."
                ),
                "role": "Role: specify the assistant role and the intended audience.",
                "examples": "Examples: include representative examples when they clarify the task.",
                "code_task": (
                    "Code task: identify the language, interfaces, tests, and implementation "
                    "constraints."
                ),
                "conciseness": "Conciseness: remove repetition and keep the result focused.",
            }
        else:
            target_sections = {
                "clarity": "清晰度：定义术语、输入和预期结果。",
                "completeness": "完整度：覆盖背景、边界情况和验证标准。",
                "constraints": "约束：说明边界、排除项和不可违反的规则。",
                "format": "输出格式：使用清晰标题、结构化要点并给出可执行结果。",
                "role": "角色：明确助手角色和目标受众。",
                "examples": "示例：在有助于理解任务时提供代表性示例。",
                "code_task": "代码任务：明确语言、接口、测试和实现约束。",
                "conciseness": "简洁度：删除重复内容并保持结果聚焦。",
            }
        if targets is not None:
            for name, section in target_sections.items():
                if getattr(selected, name):
                    sections.append(section)
            if selected.language_preservation:
                sections.append(profile.instruction)
        if profile.primary != "en":
            for suggestion in analysis.suggestions[:5]:
                sections.append(f"改进点 - {suggestion.title}：{suggestion.example}")
        optimized = "\n\n".join(sections)
        optimized_analysis = self.analyzer.analyze(optimized)
        optimized_analysis.optimized_prompt = optimized
        return optimized_analysis
