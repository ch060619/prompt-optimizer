from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from prompt_optimizer.core.models import PromptTemplate
from prompt_optimizer.paths import DATA_ROOT


class TemplateManager:
    def __init__(self, templates_dir: Path | None = None) -> None:
        self.templates_dir = templates_dir or DATA_ROOT / "templates"
        self._templates: list[PromptTemplate] | None = None

    def list_templates(self, category: str | None = None) -> list[PromptTemplate]:
        templates = self._load()
        if category:
            return [item for item in templates if item.category == category]
        return templates

    def get(self, template_id: str) -> PromptTemplate:
        for template in self._load():
            if template.id == template_id:
                return template
        raise KeyError(f"未找到模板：{template_id}")

    def categories(self) -> list[str]:
        return sorted({template.category for template in self._load()})

    def render(self, template_id: str, variables: dict[str, str]) -> str:
        template = self.get(template_id)
        content = template.template
        for name in template.variables:
            content = content.replace("{" + name + "}", variables.get(name, f"{{{name}}}"))
        return content

    def _load(self) -> list[PromptTemplate]:
        if self._templates is not None:
            return self._templates
        templates: list[PromptTemplate] = []
        for file in sorted(self.templates_dir.glob("*.yml")):
            with file.open("r", encoding="utf-8") as stream:
                payload: dict[str, Any] = yaml.safe_load(stream)
            templates.extend(PromptTemplate(**item) for item in payload["templates"])
        self._templates = templates
        return templates

