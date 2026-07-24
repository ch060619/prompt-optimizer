"""RC ID: RC-282. Tests for license file maintenance."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LICENSE = ROOT / "LICENSE"
NOTICE = ROOT / "NOTICE"
THIRD_PARTY_NOTICES = ROOT / "THIRD_PARTY_NOTICES.md"
MODEL_LICENSES_README = ROOT / "docs" / "licenses" / "models" / "README.md"
ASSET_LICENSES_README = ROOT / "docs" / "licenses" / "assets" / "README.md"
MANIFEST = ROOT / "data" / "models" / "manifest.yml"


class TestLicenseFile:
    def test_exists(self) -> None:
        assert LICENSE.is_file()

    def test_is_mit(self) -> None:
        assert "MIT License" in LICENSE.read_text(encoding="utf-8")


class TestNoticeFile:
    def test_exists(self) -> None:
        assert NOTICE.is_file()

    def test_references_mit(self) -> None:
        text = NOTICE.read_text(encoding="utf-8")
        assert "MIT" in text

    def test_references_fastapi(self) -> None:
        text = NOTICE.read_text(encoding="utf-8")
        assert "FastAPI" in text

    def test_references_react(self) -> None:
        text = NOTICE.read_text(encoding="utf-8")
        assert "React" in text

    def test_references_gemma(self) -> None:
        text = NOTICE.read_text(encoding="utf-8")
        assert "Gemma" in text

    def test_references_qwen(self) -> None:
        text = NOTICE.read_text(encoding="utf-8")
        assert "Qwen" in text

    def test_references_third_party_notices(self) -> None:
        text = NOTICE.read_text(encoding="utf-8")
        assert "THIRD_PARTY_NOTICES" in text

    def test_has_copyright(self) -> None:
        text = NOTICE.read_text(encoding="utf-8")
        assert "Copyright" in text


class TestThirdPartyNotices:
    def test_exists(self) -> None:
        assert THIRD_PARTY_NOTICES.is_file()

    def test_has_pypi_section(self) -> None:
        text = THIRD_PARTY_NOTICES.read_text(encoding="utf-8")
        assert "pypi" in text.lower() or "PyPI" in text

    def test_has_npm_section(self) -> None:
        text = THIRD_PARTY_NOTICES.read_text(encoding="utf-8")
        assert "npm" in text.lower()

    def test_has_reused_source_code_section(self) -> None:
        text = THIRD_PARTY_NOTICES.read_text(encoding="utf-8")
        assert "Reused Source Code" in text or "reused" in text.lower()

    def test_references_license_urls(self) -> None:
        text = THIRD_PARTY_NOTICES.read_text(encoding="utf-8")
        assert "https://" in text


class TestModelLicenses:
    def test_dir_exists(self) -> None:
        assert MODEL_LICENSES_README.is_file()

    def test_references_gemma(self) -> None:
        text = MODEL_LICENSES_README.read_text(encoding="utf-8")
        assert "Gemma" in text

    def test_references_qwen(self) -> None:
        text = MODEL_LICENSES_README.read_text(encoding="utf-8")
        assert "Qwen" in text

    def test_references_gemma_license(self) -> None:
        text = MODEL_LICENSES_README.read_text(encoding="utf-8")
        assert "LicenseRef-Gemma-Terms" in text

    def test_references_apache(self) -> None:
        text = MODEL_LICENSES_README.read_text(encoding="utf-8")
        assert "Apache-2.0" in text

    def test_manifest_has_license_fields(self) -> None:
        text = MANIFEST.read_text(encoding="utf-8")
        assert "license_spdx" in text
        assert "license_url" in text
        assert "license_status" in text


class TestAssetLicenses:
    def test_dir_exists(self) -> None:
        assert ASSET_LICENSES_README.is_file()

    def test_references_artwork(self) -> None:
        text = ASSET_LICENSES_README.read_text(encoding="utf-8")
        assert "artwork" in text.lower()

    def test_references_icon(self) -> None:
        text = ASSET_LICENSES_README.read_text(encoding="utf-8")
        assert "icon" in text.lower()


class TestReleaseArtifacts:
    """Verify release workflow includes license files."""

    def test_release_workflow_includes_license(self) -> None:
        release_yml = ROOT / ".github" / "workflows" / "release.yml"
        text = release_yml.read_text(encoding="utf-8")
        assert "LICENSE" in text
        assert "NOTICE" in text
        assert "THIRD_PARTY_NOTICES" in text
