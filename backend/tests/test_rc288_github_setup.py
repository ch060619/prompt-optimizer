"""RC ID: RC-288. Tests for GitHub repository structure and setup."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SETUP_DOC = ROOT / "docs" / "github-repository-setup.md"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
CODEOWNERS = ROOT / ".github" / "CODEOWNERS"
CHECK_SCRIPT = ROOT / "scripts" / "check_rc288_github_setup.py"


class TestSetupDoc:
    def test_exists(self) -> None:
        assert SETUP_DOC.is_file()

    def test_has_topics(self) -> None:
        text = SETUP_DOC.read_text(encoding="utf-8")
        assert "Repository Topics" in text

    def test_has_structure(self) -> None:
        text = SETUP_DOC.read_text(encoding="utf-8")
        assert "Repository Structure" in text

    def test_has_project_board(self) -> None:
        text = SETUP_DOC.read_text(encoding="utf-8")
        assert "Project Board" in text

    def test_has_milestones(self) -> None:
        text = SETUP_DOC.read_text(encoding="utf-8")
        assert "Milestones" in text
        assert "v3.0.0-stable" in text

    def test_has_roadmap(self) -> None:
        text = SETUP_DOC.read_text(encoding="utf-8")
        assert "Public Roadmap" in text
        assert "Completed" in text
        assert "Future" in text

    def test_has_topics_list(self) -> None:
        text = SETUP_DOC.read_text(encoding="utf-8")
        assert "prompt-engineering" in text
        assert "offline-first" in text

    def test_has_labels(self) -> None:
        text = SETUP_DOC.read_text(encoding="utf-8")
        assert "Labels" in text
        assert "good first issue" in text

    def test_has_release_process(self) -> None:
        text = SETUP_DOC.read_text(encoding="utf-8")
        assert "Release Process" in text or "Releases" in text


class TestReadme:
    def test_exists(self) -> None:
        assert README.is_file()

    def test_mentions_rabbit_code(self) -> None:
        text = README.read_text(encoding="utf-8")
        assert "Rabbit Code" in text

    def test_has_installation(self) -> None:
        text = README.read_text(encoding="utf-8")
        assert "安装" in text or "Install" in text

    def test_mentions_license(self) -> None:
        text = README.read_text(encoding="utf-8")
        assert "MIT" in text or "License" in text or "license" in text


class TestChangelog:
    def test_exists(self) -> None:
        assert CHANGELOG.is_file()

    def test_has_version(self) -> None:
        text = CHANGELOG.read_text(encoding="utf-8")
        assert "3.0.0" in text


class TestWorkflows:
    def test_release_workflow_exists(self) -> None:
        assert RELEASE_WORKFLOW.is_file()

    def test_ci_workflow_exists(self) -> None:
        assert CI_WORKFLOW.is_file()


class TestCodeowners:
    def test_exists(self) -> None:
        assert CODEOWNERS.is_file()


class TestCheckScript:
    def test_exists(self) -> None:
        assert CHECK_SCRIPT.is_file()

    def test_has_all_checks(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "check_setup_doc" in text
        assert "check_readme" in text
        assert "check_changelog" in text
        assert "check_workflows" in text
        assert "check_codeowners" in text
