"""RC ID: RC-283. Tests for prohibiting Claude Code proprietary components."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CHECK_SCRIPT = ROOT / "scripts" / "check_rc283_claude_prohibited.py"
DENYLIST = ROOT / "docs" / "research" / "source-map-denylist.yml"
ADR_0013 = ROOT / "docs" / "adr" / "0013-claude-code-provider-boundary.md"
ADR_0004 = ROOT / "docs" / "adr" / "0004-claude-agent-sdk-rights-boundary.md"
PYPROJECT = ROOT / "backend" / "pyproject.toml"
PACKAGE_JSON = ROOT / "frontend" / "package.json"
CARGO_TOML = ROOT / "apps" / "desktop" / "src-tauri" / "Cargo.toml"

CLAUDE_PROPRIETARY_MARKERS = [
    "claude-code-sourcemap",
    "claude-code-rev",
    "claude-code-source-code-deobfuscation",
    "@anthropic-ai/claude-code",
    "claude-code/cli",
    "claude-code/sdk",
]


class TestCheckScript:
    def test_exists(self) -> None:
        assert CHECK_SCRIPT.is_file()

    def test_scans_source_tree(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "scan_source_tree" in text

    def test_checks_dependency_manifests(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "check_dependency_manifests" in text

    def test_checks_documentation_mislabeling(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "check_documentation_mislabeling" in text

    def test_checks_denylist(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "check_denylist_covers_claude" in text

    def test_checks_sbom(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "check_sbom_zero_claude" in text

    def test_checks_external_marking(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "check_external_integration_marking" in text


class TestDenylist:
    def test_exists(self) -> None:
        assert DENYLIST.is_file()

    def test_covers_claude_sourcemap(self) -> None:
        text = DENYLIST.read_text(encoding="utf-8")
        assert "claude-code-sourcemap" in text

    def test_covers_claude_rev(self) -> None:
        text = DENYLIST.read_text(encoding="utf-8")
        assert "claude-code-rev" in text


class TestADRs:
    def test_adr_0013_exists(self) -> None:
        assert ADR_0013.is_file()

    def test_adr_0004_exists(self) -> None:
        assert ADR_0004.is_file()

    def test_adr_0013_marks_external(self) -> None:
        text = ADR_0013.read_text(encoding="utf-8")
        assert "external" in text.lower() or "官方" in text or "official" in text.lower()


class TestNoProprietaryInDependencies:
    """Ensure no Claude Code proprietary markers in dependency manifests."""

    @pytest.mark.parametrize("marker", CLAUDE_PROPRIETARY_MARKERS)
    def test_pyproject_clean(self, marker: str) -> None:
        text = PYPROJECT.read_text(encoding="utf-8")
        assert marker not in text

    @pytest.mark.parametrize("marker", CLAUDE_PROPRIETARY_MARKERS)
    def test_package_json_clean(self, marker: str) -> None:
        text = PACKAGE_JSON.read_text(encoding="utf-8")
        assert marker not in text

    @pytest.mark.parametrize("marker", CLAUDE_PROPRIETARY_MARKERS)
    def test_cargo_toml_clean(self, marker: str) -> None:
        if CARGO_TOML.is_file():
            text = CARGO_TOML.read_text(encoding="utf-8")
            assert marker not in text


class TestNoMislabeling:
    """Ensure documentation does not mislabel Claude Code as Rabbit Code."""

    MISLABELING = [
        "claude code is rabbit code",
        "claude code is open source",
        "claude code is part of rabbit code",
        "rabbit code includes claude code",
        "rabbit code bundles claude code",
    ]

    @pytest.mark.parametrize("pattern", MISLABELING)
    def test_readme_no_mislabeling(self, pattern: str) -> None:
        readme = ROOT / "README.md"
        if readme.is_file():
            text = readme.read_text(encoding="utf-8").lower()
            assert pattern not in text
