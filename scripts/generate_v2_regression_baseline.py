#!/usr/bin/env python3
"""RC ID: RC-047. Generate the approved Prompt Optimizer V2 regression baseline."""

# RC ID: RC-054. Use the canonical Rabbit Code environment during generation.

from __future__ import annotations

import argparse
import gc
import json
import os
import re
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterator

from prompt_optimizer.core.analyzer import Analyzer
from prompt_optimizer.core.optimizer import Optimizer
from prompt_optimizer.core.rules import load_scoring_rules
from prompt_optimizer.evaluation import EvaluationService
from prompt_optimizer.export.service import ExportService
from prompt_optimizer.services import AppServices
from prompt_optimizer.templates.manager import TemplateManager

GOLDEN_PATH = Path("backend/tests/golden/v2_regression.json")
EVALUATION_FIXTURE = Path("backend/tests/fixtures/v2_evaluation.yml")
RC_PATTERN = re.compile(r"RC-\d{3}")
WEAK_PROMPT = "帮我写一封邮件"
STRONG_PROMPT = (
    "你是一名资深 Python 工程师。目标：生成一个 FastAPI 接口。"
    "背景：用于本地工具。输出格式：Markdown 表格。限制：不要引入外部服务。"
    "请给出步骤、示例输入输出和测试用例。"
)


@contextmanager
def _temporary_environment(name: str, value: str) -> Iterator[None]:
    previous = os.environ.get(name)
    os.environ[name] = value
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = previous


def _analysis_payload(analysis: Any) -> dict[str, Any]:
    payload: dict[str, Any] = analysis.model_dump(mode="json")
    payload["created_at"] = "<generated-at>"
    return payload


def _normalized_json_export(rendered: str) -> dict[str, Any]:
    payload: dict[str, Any] = json.loads(rendered)
    payload["created_at"] = "<generated-at>"
    payload["analysis"]["created_at"] = "<generated-at>"
    return payload


def _normalized_evaluation_report(report: str, fixture_path: Path) -> str:
    normalized_lines: list[str] = []
    for line in report.replace(fixture_path.as_posix(), EVALUATION_FIXTURE.as_posix()).splitlines():
        if line.startswith("| regression-"):
            cells = line.split("|")
            cells[-2] = " <latency-ms> "
            line = "|".join(cells)
        normalized_lines.append(line)
    return "\n".join(normalized_lines)


def build_snapshot(repository_root: Path) -> dict[str, Any]:
    analyzer = Analyzer()
    optimizer = Optimizer(analyzer)
    templates = TemplateManager()
    weak_analysis = analyzer.analyze(WEAK_PROMPT)
    strong_analysis = analyzer.analyze(STRONG_PROMPT)
    optimized = optimizer.optimize(WEAK_PROMPT)
    template = templates.get("tech-code-generation")

    with tempfile.TemporaryDirectory(prefix="v2-regression-") as directory:
        with _temporary_environment("RABBIT_CODE_HOME", directory):
            services = AppServices()
            first_id = services.versions.create(
                WEAK_PROMPT,
                optimized.optimized_prompt or "",
                optimized,
            )
            second = optimizer.optimize(STRONG_PROMPT)
            second_id = services.versions.create(
                STRONG_PROMPT,
                second.optimized_prompt or "",
                second,
            )
            history = [
                {
                    "id": item.id,
                    "original_preview": item.original_preview,
                    "optimized_preview": item.optimized_preview,
                    "score": item.score,
                }
                for item in services.versions.list()
            ]
            diff = services.versions.diff(first_id, second_id).model_dump(mode="json")
            version = services.versions.get(first_id)
            exporter = ExportService()
            exports = {
                "csv": exporter.render(version, "csv"),
                "json": _normalized_json_export(exporter.render(version, "json")),
                "md": exporter.render(version, "md"),
                "txt": exporter.render(version, "txt"),
            }
            fixture_path = repository_root / EVALUATION_FIXTURE
            evaluation = _normalized_evaluation_report(
                EvaluationService(services).run_markdown(fixture_path, "offline"),
                fixture_path,
            )
            del services
            gc.collect()

    return {
        "analysis": {
            "strong": _analysis_payload(strong_analysis),
            "weak": _analysis_payload(weak_analysis),
        },
        "diff": diff,
        "evaluation": evaluation,
        "exports": exports,
        "history": history,
        "optimization": _analysis_payload(optimized),
        "rules": [asdict(rule) for rule in load_scoring_rules()],
        "templates": {
            "categories": templates.categories(),
            "rendered": templates.render(
                "tech-code-generation",
                {
                    "language": "Python",
                    "feature": "分页 API",
                    "constraints": "只使用标准库并提供测试",
                },
            ),
            "selected": template.model_dump(mode="json"),
        },
    }


def _git_head(repository_root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout.strip()


def _relative_migration_note(repository_root: Path, note: Path, rc_id: str) -> str:
    resolved_root = repository_root.resolve()
    resolved_note = (repository_root / note).resolve()
    if not resolved_note.is_relative_to(resolved_root) or not resolved_note.is_file():
        raise ValueError("migration note must be an existing file inside the repository")
    if f"RC ID: {rc_id}" not in resolved_note.read_text(encoding="utf-8"):
        raise ValueError("migration note must declare the approving RC ID")
    return resolved_note.relative_to(resolved_root).as_posix()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approve-rc", required=True, help="approving requirement, RC-xxx")
    parser.add_argument("--reason", required=True, help="why the baseline is being changed")
    parser.add_argument("--migration-note", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=GOLDEN_PATH)
    args = parser.parse_args(argv)

    rc_id = args.approve_rc.upper()
    if not RC_PATTERN.fullmatch(rc_id):
        parser.error("--approve-rc must use RC-xxx format")
    reason = args.reason.strip()
    if not reason:
        parser.error("--reason must not be empty")

    repository_root = Path(__file__).resolve().parents[1]
    note = _relative_migration_note(repository_root, args.migration_note, rc_id)
    payload = {
        "approval": {
            "migration_note": note,
            "rc_id": rc_id,
            "reason": reason,
            "source_commit": _git_head(repository_root),
        },
        "snapshot": build_snapshot(repository_root),
    }
    output = repository_root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(output.relative_to(repository_root).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
