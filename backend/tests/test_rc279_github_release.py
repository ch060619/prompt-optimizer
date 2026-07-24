"""RC ID: RC-279. Tests for GitHub Release workflow."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
RELEASE_NOTES_SCRIPT = ROOT / "scripts" / "generate_release_notes.py"
CHECK_SCRIPT = ROOT / "scripts" / "check_rc279_github_release.py"
CHANGELOG = ROOT / "CHANGELOG.md"


class TestWorkflowFile:
    """Verify release.yml structure."""

    def test_workflow_exists(self) -> None:
        assert WORKFLOW.is_file(), "release.yml must exist"

    def test_triggers_on_tags(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        assert "tags:" in text
        assert '"v*"' in text or "'v*'" in text or "v*" in text

    def test_has_all_required_jobs(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        required = ["resolve-channel", "build-cli", "build-desktop", "build-sbom", "publish"]
        for job in required:
            assert job in text, f"Missing job: {job}"

    def test_desktop_matrix_has_linux_and_windows(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        assert "ubuntu-latest" in text
        assert "windows-latest" in text

    def test_uses_sbom_generator(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        assert "generate_sbom.py" in text

    def test_uses_release_notes_generator(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        assert "generate_release_notes.py" in text

    def test_runs_check_script(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        assert "check_rc279_github_release.py" in text

    def test_creates_github_release(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        assert "softprops/action-gh-release" in text or "actions/create-release" in text

    def test_no_code_signing(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8").lower()
        assert "codesign" not in text
        assert "signtool" not in text

    def test_has_checksum_generation(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        assert "sha256sum" in text.lower()

    def test_upload_artifacts(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        assert "upload-artifact" in text
        assert "download-artifact" in text

    def test_channel_resolution(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        assert "channel" in text
        assert "nightly" in text or "beta" in text or "stable" in text


class TestReleaseNotesScript:
    """Verify generate_release_notes.py."""

    def test_script_exists(self) -> None:
        assert RELEASE_NOTES_SCRIPT.is_file()

    def test_has_version_arg(self) -> None:
        text = RELEASE_NOTES_SCRIPT.read_text(encoding="utf-8")
        assert "--version" in text

    def test_has_channel_arg(self) -> None:
        text = RELEASE_NOTES_SCRIPT.read_text(encoding="utf-8")
        assert "--channel" in text

    def test_reads_changelog(self) -> None:
        text = RELEASE_NOTES_SCRIPT.read_text(encoding="utf-8")
        assert "CHANGELOG" in text

    def test_has_all_required_sections(self) -> None:
        text = RELEASE_NOTES_SCRIPT.read_text(encoding="utf-8")
        required = [
            "Summary",
            "Installers and CLI",
            "Checksums",
            "SBOM and Supply Chain",
            "Licenses",
            "Known Issues",
            "Upgrade Instructions",
        ]
        for section in required:
            assert section in text, f"Missing section: {section}"

    def test_has_known_issues(self) -> None:
        text = RELEASE_NOTES_SCRIPT.read_text(encoding="utf-8")
        assert "Known Issues" in text
        assert "unsigned" in text.lower()

    def test_has_rollback_instructions(self) -> None:
        text = RELEASE_NOTES_SCRIPT.read_text(encoding="utf-8")
        assert "Rollback" in text or "rollback" in text.lower()

    def test_has_checksum_verification(self) -> None:
        text = RELEASE_NOTES_SCRIPT.read_text(encoding="utf-8")
        assert "sha256" in text.lower()

    def test_has_git_log(self) -> None:
        text = RELEASE_NOTES_SCRIPT.read_text(encoding="utf-8")
        assert "git" in text.lower()


class TestCheckScript:
    """Verify check_rc279_github_release.py."""

    def test_check_script_exists(self) -> None:
        assert CHECK_SCRIPT.is_file()

    def test_checks_workflow(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "release.yml" in text or "WORKFLOW" in text

    def test_checks_release_notes(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "generate_release_notes" in text

    def test_checks_required_files(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "RELEASE_NOTES.md" in text
        assert "sbom.json" in text
        assert "LICENSE" in text

    def test_checks_no_signing(self) -> None:
        text = CHECK_SCRIPT.read_text(encoding="utf-8")
        assert "codesign" in text.lower() or "signing" in text.lower()


class TestChangelogIntegration:
    """Verify CHANGELOG.md has release-ready entries."""

    def test_changelog_exists(self) -> None:
        assert CHANGELOG.is_file()

    def test_has_versioned_entries(self) -> None:
        text = CHANGELOG.read_text(encoding="utf-8")
        assert re.search(r"\[\d+\.\d+\.\d+\]", text)

    def test_has_channels(self) -> None:
        text = CHANGELOG.read_text(encoding="utf-8")
        # Should reference nightly/beta/stable
        assert "stable" in text.lower() or "beta" in text.lower() or "nightly" in text.lower()
