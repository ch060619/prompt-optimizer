"""RC ID: RC-287. Tests for maintainer governance policies."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE = ROOT / "GOVERNANCE.md"
SECURITY = ROOT / "SECURITY.md"
CODEOWNERS = ROOT / ".github" / "CODEOWNERS"
CHECK_SCRIPT = ROOT / "scripts" / "check_rc287_governance.py"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"


class TestGovernance:
    def test_exists(self) -> None:
        assert GOVERNANCE.is_file()

    def test_has_maintainer_permissions(self) -> None:
        text = GOVERNANCE.read_text(encoding="utf-8")
        assert "Maintainer Permissions" in text

    def test_has_branch_protection(self) -> None:
        text = GOVERNANCE.read_text(encoding="utf-8")
        assert "Branch Protection" in text

    def test_has_release_approval(self) -> None:
        text = GOVERNANCE.read_text(encoding="utf-8")
        assert "Release Approval" in text

    def test_has_dependency_updates(self) -> None:
        text = GOVERNANCE.read_text(encoding="utf-8")
        assert "Dependency Updates" in text

    def test_has_security_response(self) -> None:
        text = GOVERNANCE.read_text(encoding="utf-8")
        assert "Security Response" in text

    def test_has_codeowners_section(self) -> None:
        text = GOVERNANCE.read_text(encoding="utf-8")
        assert "CODEOWNERS" in text

    def test_no_signed_commits_required(self) -> None:
        text = GOVERNANCE.read_text(encoding="utf-8").lower()
        assert "not require signed commits" in text or "not required" in text

    def test_no_signed_tags_required(self) -> None:
        text = GOVERNANCE.read_text(encoding="utf-8").lower()
        assert "signed tag" in text and "not" in text

    def test_has_roles_table(self) -> None:
        text = GOVERNANCE.read_text(encoding="utf-8")
        assert "Contributor" in text
        assert "Maintain" in text or "Maintainer" in text
        assert "Admin" in text

    def test_has_release_checklist(self) -> None:
        text = GOVERNANCE.read_text(encoding="utf-8")
        assert "checklist" in text.lower() or "Checklist" in text


class TestSecurity:
    def test_exists(self) -> None:
        assert SECURITY.is_file()

    def test_has_advisory_reporting(self) -> None:
        text = SECURITY.read_text(encoding="utf-8")
        assert "advisory" in text.lower()

    def test_has_72h_acknowledgment(self) -> None:
        text = SECURITY.read_text(encoding="utf-8")
        assert "72 hours" in text

    def test_has_severity_levels(self) -> None:
        text = SECURITY.read_text(encoding="utf-8")
        assert "Critical" in text
        assert "High" in text

    def test_has_scope(self) -> None:
        text = SECURITY.read_text(encoding="utf-8")
        assert "Scope" in text


class TestCodeowners:
    def test_exists(self) -> None:
        assert CODEOWNERS.is_file()

    def test_covers_legal(self) -> None:
        text = CODEOWNERS.read_text(encoding="utf-8")
        assert "/docs/legal/" in text

    def test_covers_adr(self) -> None:
        text = CODEOWNERS.read_text(encoding="utf-8")
        assert "/docs/adr/" in text

    def test_covers_workflows(self) -> None:
        text = CODEOWNERS.read_text(encoding="utf-8")
        assert "/.github/workflows/" in text

    def test_covers_scripts(self) -> None:
        text = CODEOWNERS.read_text(encoding="utf-8")
        assert "/scripts/" in text

    def test_covers_license_files(self) -> None:
        text = CODEOWNERS.read_text(encoding="utf-8")
        assert "/LICENSE" in text
        assert "/NOTICE" in text
        assert "/THIRD_PARTY_NOTICES.md" in text


class TestNoSigningRequired:
    def test_ci_no_gpg(self) -> None:
        text = CI_WORKFLOW.read_text(encoding="utf-8")
        assert "GPG" not in text
        assert "gpg" not in text

    def test_release_no_signing(self) -> None:
        text = RELEASE_WORKFLOW.read_text(encoding="utf-8")
        # No GPG signing in release workflow
        assert "gpg --sign" not in text.lower()


class TestCheckScript:
    def test_exists(self) -> None:
        assert CHECK_SCRIPT.is_file()

    def test_has_all_checks(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "check_governance" in text
        assert "check_security" in text
        assert "check_codeowners" in text
        assert "check_no_signed_commits_requirement" in text
