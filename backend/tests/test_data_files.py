from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from prompt_optimizer.paths import DATA_ROOT
from prompt_optimizer.templates.manager import TemplateManager


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        payload = yaml.safe_load(stream)
    assert isinstance(payload, dict)
    return payload


def test_scoring_rules_are_complete_and_unique() -> None:
    payload = _load_yaml(DATA_ROOT / "rules" / "scoring.yml")
    dimensions = payload["dimensions"]
    ids = [item["id"] for item in dimensions]

    assert len(ids) == len(set(ids))
    assert dimensions
    for item in dimensions:
        assert item["id"]
        assert item["label"]
        assert float(item["weight"]) > 0
        assert isinstance(item["keywords"], list)
        assert item["keywords"]
        assert int(item["min_length"]) >= 0
        suggestion = item["suggestion"]
        assert suggestion["title"]
        assert suggestion["detail"]
        assert suggestion["example"]


def test_template_files_are_complete_unique_and_renderable() -> None:
    template_ids: set[str] = set()
    template_files = sorted((DATA_ROOT / "templates").glob("*.yml"))

    assert template_files
    for template_file in template_files:
        payload = _load_yaml(template_file)
        templates = payload["templates"]
        assert templates
        for item in templates:
            assert item["id"] not in template_ids
            template_ids.add(item["id"])
            assert item["name"]
            assert item["category"]
            assert item["description"]
            assert isinstance(item["tags"], list)
            assert item["tags"]
            assert item["template"]
            assert isinstance(item["variables"], list)
            assert isinstance(item["best_practices"], list)
            assert item["best_practices"]
            for variable in item["variables"]:
                assert "{" + variable + "}" in item["template"]


def test_template_render_replaces_known_variables_and_keeps_missing_placeholders() -> None:
    manager = TemplateManager()

    rendered = manager.render(
        "tech-code-generation",
        {"language": "Python", "feature": "版本导出", "constraints": "保持离线运行"},
    )
    assert "Python" in rendered
    assert "版本导出" in rendered
    assert "保持离线运行" in rendered

    rendered_with_missing = manager.render("tech-code-review", {"language": "TypeScript"})
    assert "TypeScript" in rendered_with_missing
    assert "{focus}" in rendered_with_missing
