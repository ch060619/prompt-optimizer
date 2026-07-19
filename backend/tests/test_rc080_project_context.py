from __future__ import annotations

from pathlib import Path

from backend.rabbit_code.project_context import ProjectContextDetector

# RC ID: RC-080. Verify read-only project, Git, language, build, and instruction discovery.


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_current_workspace_context_includes_git_and_build_signals() -> None:
    context = ProjectContextDetector(REPOSITORY_ROOT).detect()

    assert context.git_root == REPOSITORY_ROOT.resolve()
    assert context.branch
    assert "Python" in context.languages
    assert "TypeScript" in context.languages
    assert "pyproject.toml" in context.build_files
    assert "package.json" in context.build_files
    assert context.to_dict()["git_root"] == str(REPOSITORY_ROOT.resolve())


def test_detector_discovers_instructions_and_ignores_dependency_directories(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("project instructions", encoding="utf-8")
    (tmp_path / ".rabbit-code").mkdir()
    (tmp_path / ".rabbit-code" / "instructions.md").write_text("local", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('ok')", encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "ignored.ts").write_text("ignored", encoding="utf-8")

    context = ProjectContextDetector(tmp_path).detect()

    assert context.git_root is None
    assert context.languages == ("Python",)
    assert context.instruction_files == (
        tmp_path / ".rabbit-code" / "instructions.md",
        tmp_path / "AGENTS.md",
    )
