from __future__ import annotations

from pathlib import Path

import pytest
from backend.rabbit_code.instructions import InstructionLoader

# RC ID: RC-081. Verify global/project/directory instruction precedence and path bounds.


def test_instruction_loader_orders_global_root_and_nested_overrides(tmp_path: Path) -> None:
    global_file = tmp_path / "global.md"
    global_file.write_text("global", encoding="utf-8")
    project = tmp_path / "project"
    nested = project / "src" / "feature"
    nested.mkdir(parents=True)
    (project / "AGENTS.md").write_text("root", encoding="utf-8")
    (project / ".rabbit-code").mkdir()
    (project / ".rabbit-code" / "instructions.md").write_text("project-local", encoding="utf-8")
    (project / "src" / "AGENTS.md").write_text("src", encoding="utf-8")
    (nested / "RABBIT.md").write_text("feature", encoding="utf-8")

    loaded = InstructionLoader(project, nested, global_file=global_file).load()

    assert [document.content for document in loaded.documents] == [
        "global",
        "root",
        "project-local",
        "src",
        "feature",
    ]
    assert loaded.combined_text == "global\nroot\nproject-local\nsrc\nfeature"


def test_instruction_loader_rejects_working_directory_outside_project(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    with pytest.raises(ValueError, match="within project"):
        InstructionLoader(project, tmp_path / "outside").load()
