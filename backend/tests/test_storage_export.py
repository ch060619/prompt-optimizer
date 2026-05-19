from __future__ import annotations

import json

from prompt_optimizer.core.optimizer import Optimizer
from prompt_optimizer.export.service import ExportService
from prompt_optimizer.storage.service import StorageService
from prompt_optimizer.storage.version_service import VersionService


def test_version_storage_and_diff(tmp_path) -> None:  # type: ignore[no-untyped-def]
    storage = StorageService(tmp_path / "test.sqlite3")
    service = VersionService(storage)
    analysis_one = Optimizer().optimize("写一个总结")
    id_one = service.create("写一个总结", analysis_one.optimized_prompt or "", analysis_one)
    analysis_two = Optimizer().optimize("写一个面向管理层的项目总结，包含风险和行动项")
    id_two = service.create(
        "写一个面向管理层的项目总结，包含风险和行动项",
        analysis_two.optimized_prompt or "",
        analysis_two,
    )

    assert len(service.list()) == 2
    diff = service.diff(id_one, id_two)
    assert diff.new_id == id_two
    assert diff.diff_lines


def test_export_formats(tmp_path) -> None:  # type: ignore[no-untyped-def]
    storage = StorageService(tmp_path / "export.sqlite3")
    service = VersionService(storage)
    analysis = Optimizer().optimize("生成一个测试计划")
    version_id = service.create("生成一个测试计划", analysis.optimized_prompt or "", analysis)
    version = service.get(version_id)
    exporter = ExportService()

    assert "# 提示词优化结果" in exporter.render(version, "md")
    assert '"original_prompt"' in exporter.render(version, "json")
    assert "原始提示词" in exporter.render(version, "txt")
    assert "version_id,score" in exporter.render(version, "csv")


def test_export_formats_preserve_special_characters(tmp_path) -> None:  # type: ignore[no-untyped-def]
    storage = StorageService(tmp_path / "special.sqlite3")
    service = VersionService(storage)
    prompt = '生成 CSV 报告，包含逗号、"引号" 和\n换行'
    analysis = Optimizer().optimize(prompt)
    version_id = service.create(prompt, analysis.optimized_prompt or "", analysis)
    version = service.get(version_id)
    exporter = ExportService()

    json_output = json.loads(exporter.render(version, "json"))
    assert json_output["original_prompt"] == prompt
    assert "换行" in exporter.render(version, "md")
    csv_output = exporter.render(version, "csv")
    assert '""引号""' in csv_output
    assert "换行" in csv_output
