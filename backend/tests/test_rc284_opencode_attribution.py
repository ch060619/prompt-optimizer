"""RC ID: RC-284. Tests for Codex/OpenCode attribution and modification declarations."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ADR_0003 = ROOT / "docs" / "adr" / "0003-opencode-research-boundary.md"
RESEARCH_REGISTER = ROOT / "docs" / "research" / "opencode-research-register.yml"
MODULE_MAP = ROOT / "docs" / "research" / "opencode-module-map.md"
NOTICE = ROOT / "NOTICE"
THIRD_PARTY_NOTICES = ROOT / "THIRD_PARTY_NOTICES.md"
CHECK_SCRIPT = ROOT / "scripts" / "check_rc284_opencode_attribution.py"


class TestADR:
    def test_exists(self) -> None:
        assert ADR_0003.is_file()

    def test_references_mit(self) -> None:
        text = ADR_0003.read_text(encoding="utf-8")
        assert "MIT" in text

    def test_states_no_upstream_code(self) -> None:
        text = ADR_0003.read_text(encoding="utf-8").lower()
        assert "no upstream code" in text or "concepts-only" in text

    def test_references_notice(self) -> None:
        text = ADR_0003.read_text(encoding="utf-8")
        assert "NOTICE" in text


class TestResearchRegister:
    def test_exists(self) -> None:
        assert RESEARCH_REGISTER.is_file()

    def test_has_fixed_commit(self) -> None:
        text = RESEARCH_REGISTER.read_text(encoding="utf-8")
        assert "453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d" in text

    def test_declares_mit(self) -> None:
        text = RESEARCH_REGISTER.read_text(encoding="utf-8")
        assert "MIT" in text

    def test_has_concepts_only_policy(self) -> None:
        text = RESEARCH_REGISTER.read_text(encoding="utf-8")
        assert "concepts-only-no-upstream-code" in text

    def test_references_repo(self) -> None:
        text = RESEARCH_REGISTER.read_text(encoding="utf-8")
        assert "anomalyco/opencode" in text


class TestModuleMap:
    def test_exists(self) -> None:
        assert MODULE_MAP.is_file()

    def test_references_agent(self) -> None:
        text = MODULE_MAP.read_text(encoding="utf-8").lower()
        assert "agent" in text

    def test_references_cli(self) -> None:
        text = MODULE_MAP.read_text(encoding="utf-8").lower()
        assert "cli" in text


class TestNotice:
    def test_exists(self) -> None:
        assert NOTICE.is_file()

    def test_references_opencode(self) -> None:
        text = NOTICE.read_text(encoding="utf-8")
        assert "OpenCode" in text or "opencode" in text.lower()

    def test_references_adr_0003(self) -> None:
        text = NOTICE.read_text(encoding="utf-8")
        assert "ADR-0003" in text


class TestThirdPartyNotices:
    def test_has_reused_source_code_section(self) -> None:
        text = THIRD_PARTY_NOTICES.read_text(encoding="utf-8")
        assert "Reused Source Code" in text

    def test_confirms_no_approved_reuse(self) -> None:
        text = THIRD_PARTY_NOTICES.read_text(encoding="utf-8")
        assert "No third-party source code is approved" in text


class TestNoUnattributedCode:
    """Ensure no product source files contain unattributed OpenCode code."""

    PATTERNS = [
        "Copyright (c) anomalyco",
        "Copyright (c) OpenCode",
        "Licensed from OpenCode",
        "Based on OpenCode",
        "Derived from opencode",
    ]

    @pytest.mark.parametrize("pattern", PATTERNS)
    def test_backend_src_clean(self, pattern: str) -> None:
        backend_src = ROOT / "backend" / "src"
        if backend_src.is_dir():
            for f in backend_src.rglob("*.py"):
                content = f.read_text(encoding="utf-8")
                assert pattern not in content, f"Pattern '{pattern}' found in {f}"

    @pytest.mark.parametrize("pattern", PATTERNS)
    def test_frontend_src_clean(self, pattern: str) -> None:
        frontend_src = ROOT / "frontend" / "src"
        if frontend_src.is_dir():
            for f in frontend_src.rglob("*"):
                if f.is_file():
                    try:
                        content = f.read_text(encoding="utf-8")
                    except (OSError, UnicodeDecodeError):
                        continue
                    assert pattern not in content, f"Pattern '{pattern}' found in {f}"


class TestCheckScript:
    def test_exists(self) -> None:
        assert CHECK_SCRIPT.is_file()

    def test_has_all_checks(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "check_adr_0003" in text
        assert "check_research_register" in text
        assert "check_module_map" in text
        assert "check_notice_references" in text
        assert "check_no_unattributed_opencode_code" in text
        assert "check_third_party_reuse_section" in text
