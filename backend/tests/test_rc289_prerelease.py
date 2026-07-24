"""RC ID: RC-289. Tests for first public release pre-flight checklist."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CHECK_SCRIPT = ROOT / "scripts" / "check_rc289_prerelease.py"

REQUIRED_DOCS = [
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "SECURITY.md",
    "LICENSE",
    "NOTICE",
    "THIRD_PARTY_NOTICES.md",
    "docs/github-repository-setup.md",
    "docs/DOCKER.md",
]

LICENSE_CHECK_SCRIPTS = [
    "scripts/check_rc281_license.py",
    "scripts/check_rc282_license_files.py",
    "scripts/check_rc283_claude_prohibited.py",
    "scripts/check_rc284_opencode_attribution.py",
    "scripts/check_rc285_license_risk.py",
    "scripts/check_rc286_asset_rights.py",
]

RELEASE_CHECK_SCRIPTS = [
    "scripts/check_rc276_update_rollback.py",
    "scripts/check_rc277_sbom.py",
    "scripts/check_rc278_release_channels.py",
    "scripts/check_rc279_github_release.py",
    "scripts/check_rc280_docker_scope.py",
]


class TestCheckScript:
    def test_exists(self) -> None:
        assert CHECK_SCRIPT.is_file()

    def test_has_clean_env_check(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "check_clean_environment" in text

    def test_has_license_review(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "check_license_review" in text

    def test_has_security_audit(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "check_security_audit" in text

    def test_has_doc_walkthrough(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "check_documentation" in text

    def test_has_section_flag(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "--section" in text

    def test_has_all_license_checks(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        for script in LICENSE_CHECK_SCRIPTS:
            assert script in text, f"Missing license check: {script}"

    def test_has_all_release_checks(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        for script in RELEASE_CHECK_SCRIPTS:
            assert script in text, f"Missing release check: {script}"


class TestRequiredDocs:
    @pytest.mark.parametrize("doc_path", REQUIRED_DOCS)
    def test_doc_exists(self, doc_path: str) -> None:
        full_path = ROOT / doc_path
        assert full_path.is_file(), f"Missing: {doc_path}"

    @pytest.mark.parametrize("doc_path", REQUIRED_DOCS)
    def test_doc_non_empty(self, doc_path: str) -> None:
        full_path = ROOT / doc_path
        content = full_path.read_text(encoding="utf-8").strip()
        assert len(content) >= 50, f"Too short: {doc_path}"


class TestInstallScripts:
    def test_install_ps1_exists(self) -> None:
        assert (ROOT / "scripts" / "install" / "install.ps1").is_file()

    def test_install_sh_exists(self) -> None:
        assert (ROOT / "scripts" / "install" / "install.sh").is_file()

    def test_winget_manifest_exists(self) -> None:
        assert (ROOT / "scripts" / "install" / "winget.yml").is_file()

    def test_scoop_manifest_exists(self) -> None:
        assert (ROOT / "scripts" / "install" / "scoop.json").is_file()


class TestPyproject:
    def test_exists(self) -> None:
        assert (ROOT / "backend" / "pyproject.toml").is_file()

    def test_has_package_name(self) -> None:
        text = (ROOT / "backend" / "pyproject.toml").read_text(encoding="utf-8")
        assert "rabbit-code" in text

    def test_has_version(self) -> None:
        text = (ROOT / "backend" / "pyproject.toml").read_text(encoding="utf-8")
        assert "3.0.0" in text


class TestDockerDev:
    def test_docker_compose_dev_exists(self) -> None:
        assert (ROOT / "docker-compose.dev.yml").is_file()

    def test_no_production_compose(self) -> None:
        assert not (ROOT / "docker-compose.yml").is_file()
