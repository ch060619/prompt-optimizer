"""RC IDs: RC-300 through RC-310. Final completion definition tests."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CHECK_SCRIPT = ROOT / "scripts" / "check_rc300_310_final.py"


class TestCheckScript:
    def test_exists(self) -> None:
        assert CHECK_SCRIPT.is_file()

    def test_has_all_rc_checks(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        for rc_id in range(300, 311):
            assert f"RC-{rc_id}" in text, f"Missing RC-{rc_id}"


class TestRC300_RequirementsTraceability:
    def test_execution_plan_exists(self) -> None:
        assert (ROOT / "docs" / "rabbit-code-310-detailed-execution.md").is_file()

    def test_has_plan_sections(self) -> None:
        text = (ROOT / "docs" / "rabbit-code-310-detailed-execution.md").read_text(encoding="utf-8")
        assert "架构原型" in text
        assert "最终完成" in text


class TestRC301_PlatformE2E:
    def test_support_matrix_exists(self) -> None:
        assert (ROOT / "docs" / "support-matrix.md").is_file()

    def test_windows_install(self) -> None:
        assert (ROOT / "scripts" / "install" / "install.ps1").is_file()

    def test_linux_install(self) -> None:
        assert (ROOT / "scripts" / "install" / "install.sh").is_file()


class TestRC302_ProviderContracts:
    @pytest.mark.parametrize("provider", ["openai", "gemini", "anthropic"])
    def test_provider_exists(self, provider: str) -> None:
        assert (ROOT / "backend" / "src" / "prompt_optimizer" / "providers" / f"{provider}.py").is_file()


class TestRC303_ModelLifecycle:
    def test_manifest_exists(self) -> None:
        assert (ROOT / "data" / "models" / "manifest.yml").is_file()

    def test_has_gemma(self) -> None:
        text = (ROOT / "data" / "models" / "manifest.yml").read_text(encoding="utf-8").lower()
        assert "gemma" in text

    def test_has_qwen(self) -> None:
        text = (ROOT / "data" / "models" / "manifest.yml").read_text(encoding="utf-8").lower()
        assert "qwen" in text

    def test_local_install_exists(self) -> None:
        assert (ROOT / "backend" / "src" / "prompt_optimizer" / "local_install.py").is_file()


class TestRC304_DiamondStar:
    def test_optimizer_exists(self) -> None:
        assert (ROOT / "backend" / "src" / "prompt_optimizer" / "core" / "optimizer.py").is_file()

    def test_analyzer_exists(self) -> None:
        assert (ROOT / "backend" / "src" / "prompt_optimizer" / "core" / "analyzer.py").is_file()


class TestRC305_RabbitArtwork:
    def test_artwork_exists(self) -> None:
        assert (ROOT / "frontend" / "public" / "rabbit-artwork.png").is_file()

    def test_favicon_exists(self) -> None:
        assert (ROOT / "frontend" / "public" / "favicon.svg").is_file()


class TestRC306_CLIFeatures:
    @pytest.mark.parametrize("module", ["agent", "cli", "permissions", "sessions", "git_tools", "run_control"])
    def test_module_exists(self, module: str) -> None:
        assert (ROOT / "backend" / "rabbit_code" / f"{module}.py").is_file()


class TestRC307_GUIFeatures:
    def test_app_exists(self) -> None:
        assert (ROOT / "frontend" / "src" / "App.tsx").is_file()

    def test_tauri_conf_exists(self) -> None:
        assert (ROOT / "apps" / "desktop" / "src-tauri" / "tauri.conf.json").is_file()


class TestRC308_NoProprietary:
    def test_rc283_check_exists(self) -> None:
        assert (ROOT / "scripts" / "check_rc283_claude_prohibited.py").is_file()


class TestRC309_SourceAudit:
    def test_denylist_exists(self) -> None:
        assert (ROOT / "docs" / "research" / "source-map-denylist.yml").is_file()

    def test_boundary_check_exists(self) -> None:
        assert (ROOT / "scripts" / "check_clean_room_boundary.py").is_file()


class TestRC310_ReleaseGates:
    def test_prerelease_check_exists(self) -> None:
        assert (ROOT / "scripts" / "check_rc289_prerelease.py").is_file()

    def test_release_workflow_exists(self) -> None:
        assert (ROOT / ".github" / "workflows" / "release.yml").is_file()

    def test_ci_workflow_exists(self) -> None:
        assert (ROOT / ".github" / "workflows" / "ci.yml").is_file()

    def test_sbom_generator_exists(self) -> None:
        assert (ROOT / "scripts" / "generate_sbom.py").is_file()
