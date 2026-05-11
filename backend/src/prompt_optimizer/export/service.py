from __future__ import annotations

import csv
import io
import json

from prompt_optimizer.core.models import ExportFormat, PromptVersion


class ExportService:
    def render(self, version: PromptVersion, format: ExportFormat) -> str:
        if format == "json":
            return json.dumps(version.model_dump(mode="json"), ensure_ascii=False, indent=2)
        if format == "md":
            return self._markdown(version)
        if format == "txt":
            return self._text(version)
        if format == "csv":
            return self._csv(version)
        raise ValueError(f"不支持的导出格式：{format}")

    @staticmethod
    def _markdown(version: PromptVersion) -> str:
        suggestions = "\n".join(
            f"- **{item.title}**（{item.priority}）：{item.detail}\n  示例：{item.example}"
            for item in version.analysis.suggestions
        )
        return f"""# 提示词优化结果

版本 ID：{version.id}

总分：{version.analysis.score.total_score}

## 原始提示词

{version.original_prompt}

## 优化后提示词

{version.optimized_prompt}

## 优化建议

{suggestions or "无"}
"""

    @staticmethod
    def _text(version: PromptVersion) -> str:
        return (
            f"版本 ID: {version.id}\n"
            f"总分: {version.analysis.score.total_score}\n\n"
            f"原始提示词:\n{version.original_prompt}\n\n"
            f"优化后提示词:\n{version.optimized_prompt}\n"
        )

    @staticmethod
    def _csv(version: PromptVersion) -> str:
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(["version_id", "score", "original_prompt", "optimized_prompt"])
        writer.writerow(
            [
                version.id,
                version.analysis.score.total_score,
                version.original_prompt,
                version.optimized_prompt,
            ]
        )
        writer.writerow([])
        writer.writerow(["dimension", "score", "reason"])
        for dimension in version.analysis.score.dimensions:
            writer.writerow([dimension.label, dimension.score, dimension.reason])
        return stream.getvalue()

