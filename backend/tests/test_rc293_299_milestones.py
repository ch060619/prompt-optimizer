"""RC IDs: RC-293 through RC-299. Milestone M2-M8 gate verification tests."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CHECK_SCRIPT = ROOT / "scripts" / "check_rc293_299_milestones.py"


class TestCheckScript:
    def test_exists(self) -> None:
        assert CHECK_SCRIPT.is_file()

    def test_has_all_milestones(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        for rc_id in ["RC-293", "RC-294", "RC-295", "RC-296", "RC-297", "RC-298", "RC-299"]:
            assert rc_id in text, f"Missing {rc_id}"


class TestRC293_M2_AgentCLI:
    """M2: Agent Core & CLI usability."""

    @pytest.mark.parametrize("rel_path", [
        "backend/rabbit_code/agent.py",
        "backend/rabbit_code/cli.py",
        "backend/rabbit_code/permissions.py",
        "backend/rabbit_code/sessions.py",
        "backend/rabbit_code/streaming.py",
        "backend/rabbit_code/git_tools.py",
        "backend/rabbit_code/tool_registry.py",
    ])
    def test_file_exists(self, rel_path: str) -> None:
        assert (ROOT / rel_path).is_file()


class TestRC294_M3_ProviderLocal:
    """M3: Provider & local model closed loop."""

    @pytest.mark.parametrize("rel_path", [
        "backend/src/prompt_optimizer/providers/openai.py",
        "backend/src/prompt_optimizer/providers/gemini.py",
        "backend/src/prompt_optimizer/providers/anthropic.py",
        "backend/src/prompt_optimizer/providers/presets.py",
        "backend/src/prompt_optimizer/local_install.py",
        "data/models/manifest.yml",
    ])
    def test_file_exists(self, rel_path: str) -> None:
        assert (ROOT / rel_path).is_file()


class TestRC295_M4_Desktop:
    """M4: Desktop main workflow."""

    @pytest.mark.parametrize("rel_path", [
        "frontend/src/App.tsx",
        "apps/desktop/src-tauri/tauri.conf.json",
        "apps/desktop/src-tauri/src/main.rs",
        "frontend/public/favicon.svg",
    ])
    def test_file_exists(self, rel_path: str) -> None:
        assert (ROOT / rel_path).is_file()


class TestRC296_M5_Optimization:
    """M5: Prompt optimization full integration."""

    @pytest.mark.parametrize("rel_path", [
        "backend/src/prompt_optimizer/core/optimizer.py",
        "backend/src/prompt_optimizer/core/analyzer.py",
        "backend/src/prompt_optimizer/core/scoring.py",
        "backend/src/prompt_optimizer/core/diff.py",
        "backend/src/prompt_optimizer/templates/manager.py",
        "backend/src/prompt_optimizer/evaluation/service.py",
        "backend/src/prompt_optimizer/api/app.py",
    ])
    def test_file_exists(self, rel_path: str) -> None:
        assert (ROOT / rel_path).is_file()


class TestRC297_M6_Hardening:
    """M6: Hardening & release candidate."""

    @pytest.mark.parametrize("rel_path", [
        "docs/support-matrix.md",
        "scripts/install/install.ps1",
        "scripts/install/install.sh",
        "backend/src/prompt_optimizer/privacy.py",
        "backend/src/prompt_optimizer/audit.py",
    ])
    def test_file_exists(self, rel_path: str) -> None:
        assert (ROOT / rel_path).is_file()


class TestRC298_M7_OpenSource:
    """M7: Open source stable release."""

    @pytest.mark.parametrize("rel_path", [
        "LICENSE",
        "NOTICE",
        "THIRD_PARTY_NOTICES.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "GOVERNANCE.md",
        "SECURITY.md",
        "scripts/generate_sbom.py",
        ".github/workflows/release.yml",
    ])
    def test_file_exists(self, rel_path: str) -> None:
        assert (ROOT / rel_path).is_file()


class TestRC299_M8_Iteration:
    """M8: Continuous optimization."""

    def test_maintenance_doc_exists(self) -> None:
        assert (ROOT / "docs" / "MAINTENANCE.md").is_file()

    def test_github_setup_doc_exists(self) -> None:
        assert (ROOT / "docs" / "github-repository-setup.md").is_file()
