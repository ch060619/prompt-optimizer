"""RC ID: RC-291. Tests for Claude Code source map clean-room verification."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
DENYLIST = ROOT / "docs" / "research" / "source-map-denylist.yml"
CLEAN_ROOM_DECISION = ROOT / "docs" / "legal" / "claude-source-map-clean-room.md"
ROLE_REGISTER = ROOT / "docs" / "legal" / "clean-room-role-register.yml"
INFO_BOUNDARY = ROOT / "docs" / "legal" / "clean-room-information-boundary.md"
BOUNDARY_CHECK = ROOT / "scripts" / "check_clean_room_boundary.py"
REWRITE_CHECK = ROOT / "scripts" / "check_clean_room_rewrite.py"
CHECK_SCRIPT = ROOT / "scripts" / "check_rc291_source_map.py"

REQUIRED_REPOS = [
    "ChinaSiro/claude-code-sourcemap",
    "oboard/claude-code-rev",
    "ghuntley/claude-code-source-code-deobfuscation",
    "ComeOnOliver/claude-code-analysis",
    "dadiaomengmeimei/claude-code-sourcemap-learning-notebook",
]


class TestDenylist:
    def test_exists(self) -> None:
        assert DENYLIST.is_file()

    def test_has_blocked_repositories(self) -> None:
        data = yaml.safe_load(DENYLIST.read_text(encoding="utf-8"))
        repos = data.get("blocked_repositories", [])
        assert len(repos) >= 5

    @pytest.mark.parametrize("repo", REQUIRED_REPOS)
    def test_repo_blocked(self, repo: str) -> None:
        data = yaml.safe_load(DENYLIST.read_text(encoding="utf-8"))
        assert repo in data.get("blocked_repositories", [])

    def test_has_blocked_urls(self) -> None:
        data = yaml.safe_load(DENYLIST.read_text(encoding="utf-8"))
        assert len(data.get("blocked_urls", [])) >= 5

    def test_has_blocked_hashes(self) -> None:
        data = yaml.safe_load(DENYLIST.read_text(encoding="utf-8"))
        assert len(data.get("blocked_hashes", [])) >= 5


class TestLegalAssessment:
    def test_exists(self) -> None:
        assert CLEAN_ROOM_DECISION.is_file()

    def test_has_risk_evaluation(self) -> None:
        text = CLEAN_ROOM_DECISION.read_text(encoding="utf-8")
        assert "风险" in text or "Risk" in text

    def test_addresses_copyright(self) -> None:
        text = CLEAN_ROOM_DECISION.read_text(encoding="utf-8")
        assert "版权" in text or "copyright" in text.lower()

    def test_addresses_trade_secret(self) -> None:
        text = CLEAN_ROOM_DECISION.read_text(encoding="utf-8")
        assert "商业秘密" in text or "trade secret" in text.lower()

    def test_has_usage_scope(self) -> None:
        text = CLEAN_ROOM_DECISION.read_text(encoding="utf-8")
        assert "临时允许范围" in text or "allow" in text.lower()

    def test_has_prohibited_scope(self) -> None:
        text = CLEAN_ROOM_DECISION.read_text(encoding="utf-8")
        assert "禁止" in text or "prohibit" in text.lower()


class TestRoleRegister:
    def test_exists(self) -> None:
        assert ROLE_REGISTER.is_file()

    def test_has_researcher_role(self) -> None:
        data = yaml.safe_load(ROLE_REGISTER.read_text(encoding="utf-8"))
        roles = [r.get("id") for r in data.get("roles", [])]
        assert "researcher" in roles

    def test_has_implementer_role(self) -> None:
        data = yaml.safe_load(ROLE_REGISTER.read_text(encoding="utf-8"))
        roles = [r.get("id") for r in data.get("roles", [])]
        assert "implementer" in roles

    def test_has_reviewer_role(self) -> None:
        data = yaml.safe_load(ROLE_REGISTER.read_text(encoding="utf-8"))
        roles = [r.get("id") for r in data.get("roles", [])]
        assert "reviewer" in roles

    def test_roles_have_allowed_inputs(self) -> None:
        data = yaml.safe_load(ROLE_REGISTER.read_text(encoding="utf-8"))
        for role in data.get("roles", []):
            assert "allowed_inputs" in role, f"Role {role.get('id')} missing allowed_inputs"

    def test_roles_have_prohibited(self) -> None:
        data = yaml.safe_load(ROLE_REGISTER.read_text(encoding="utf-8"))
        for role in data.get("roles", []):
            assert "prohibited" in role, f"Role {role.get('id')} missing prohibited"


class TestInfoBoundary:
    def test_exists(self) -> None:
        assert INFO_BOUNDARY.is_file()

    def test_references_roles(self) -> None:
        text = INFO_BOUNDARY.read_text(encoding="utf-8").lower()
        assert "researcher" in text
        assert "implementer" in text


class TestCheckScripts:
    def test_boundary_check_exists(self) -> None:
        assert BOUNDARY_CHECK.is_file()

    def test_rewrite_check_exists(self) -> None:
        assert REWRITE_CHECK.is_file()


class TestRC291CheckScript:
    def test_exists(self) -> None:
        assert CHECK_SCRIPT.is_file()

    def test_has_all_checks(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "check_denylist" in text
        assert "check_legal_assessment" in text
        assert "check_role_register" in text
        assert "check_info_boundary" in text
        assert "check_boundary_scripts" in text
