"""RC ID: RC-290. Tests for post-release maintenance policy and milestone tracking."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MAINTENANCE = ROOT / "docs" / "MAINTENANCE.md"
CHECK_SCRIPT = ROOT / "scripts" / "check_rc290_maintenance.py"
EXECUTION_PLAN = ROOT / "docs" / "rabbit-code-310-detailed-execution.md"
SUPPORT_MATRIX = ROOT / "docs" / "support-matrix.md"
CHANGELOG = ROOT / "CHANGELOG.md"
GOVERNANCE = ROOT / "GOVERNANCE.md"
ASSET_RIGHTS = ROOT / "docs" / "legal" / "asset-publication-rights.yml"
ADR_0003 = ROOT / "docs" / "adr" / "0003-opencode-research-boundary.md"
ADR_0017 = ROOT / "docs" / "adr" / "0017-primary-license-selection.md"
THIRD_PARTY_REGISTER = ROOT / "docs" / "research" / "third-party-register.yml"


class TestMaintenanceDoc:
    def test_exists(self) -> None:
        assert MAINTENANCE.is_file()

    def test_has_versioning(self) -> None:
        text = MAINTENANCE.read_text(encoding="utf-8")
        assert "Versioning" in text
        assert "Semantic Versioning" in text

    def test_has_release_cadence(self) -> None:
        text = MAINTENANCE.read_text(encoding="utf-8")
        assert "Release Cadence" in text
        assert "Stable" in text
        assert "Nightly" in text

    def test_has_compatibility(self) -> None:
        text = MAINTENANCE.read_text(encoding="utf-8")
        assert "Compatibility Policy" in text

    def test_has_security_patches(self) -> None:
        text = MAINTENANCE.read_text(encoding="utf-8")
        assert "Security Patch Policy" in text
        assert "Critical" in text
        assert "7 days" in text

    def test_has_deprecation(self) -> None:
        text = MAINTENANCE.read_text(encoding="utf-8")
        assert "Deprecation Policy" in text

    def test_has_eol(self) -> None:
        text = MAINTENANCE.read_text(encoding="utf-8")
        assert "End of Life" in text

    def test_has_dependency_updates(self) -> None:
        text = MAINTENANCE.read_text(encoding="utf-8")
        assert "Dependency Update" in text
        assert "Dependabot" in text


class TestR1Tracking:
    def test_execution_plan_exists(self) -> None:
        assert EXECUTION_PLAN.is_file()

    def test_has_progress_table(self) -> None:
        text = EXECUTION_PLAN.read_text(encoding="utf-8")
        assert "已完成项数" in text

    def test_has_completion_log(self) -> None:
        text = EXECUTION_PLAN.read_text(encoding="utf-8")
        assert "进度记录一致性检查" in text


class TestR2CompetitiveResearch:
    def test_third_party_register_exists(self) -> None:
        assert THIRD_PARTY_REGISTER.is_file()


class TestR3LicenseBoundary:
    def test_adr_0003_exists(self) -> None:
        assert ADR_0003.is_file()

    def test_adr_0017_exists(self) -> None:
        assert ADR_0017.is_file()


class TestR4AssetRights:
    def test_asset_rights_exists(self) -> None:
        assert ASSET_RIGHTS.is_file()


class TestR5PlatformScope:
    def test_support_matrix_exists(self) -> None:
        assert SUPPORT_MATRIX.is_file()

    def test_mentions_windows(self) -> None:
        text = SUPPORT_MATRIX.read_text(encoding="utf-8")
        assert "Windows" in text

    def test_mentions_linux(self) -> None:
        text = SUPPORT_MATRIX.read_text(encoding="utf-8")
        assert "Linux" in text


class TestR6StableAcceptance:
    def test_prerelease_checklist_exists(self) -> None:
        assert (ROOT / "scripts" / "check_rc289_prerelease.py").is_file()

    def test_changelog_exists(self) -> None:
        assert CHANGELOG.is_file()

    def test_governance_exists(self) -> None:
        assert GOVERNANCE.is_file()


class TestCheckScript:
    def test_exists(self) -> None:
        assert CHECK_SCRIPT.is_file()

    def test_has_all_milestone_checks(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "check_r1_tracking" in text
        assert "check_r2_competitive_research" in text
        assert "check_r3_license_boundary" in text
        assert "check_r4_asset_rights" in text
        assert "check_r5_platform_scope" in text
        assert "check_r6_stable_acceptance" in text
