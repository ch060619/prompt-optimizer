"""RC ID: RC-281. Tests for primary license selection and consistency."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LICENSE = ROOT / "LICENSE"
PYPROJECT = ROOT / "backend" / "pyproject.toml"
PACKAGE_JSON = ROOT / "frontend" / "package.json"
TAURI_CONF = ROOT / "apps" / "desktop" / "src-tauri" / "tauri.conf.json"
CARGO_TOML = ROOT / "apps" / "desktop" / "src-tauri" / "Cargo.toml"
ADR = ROOT / "docs" / "adr" / "0017-primary-license-selection.md"


class TestLicenseFile:
    def test_exists(self) -> None:
        assert LICENSE.is_file()

    def test_is_mit(self) -> None:
        text = LICENSE.read_text(encoding="utf-8")
        assert "MIT License" in text

    def test_has_permission_grant(self) -> None:
        text = LICENSE.read_text(encoding="utf-8")
        assert "Permission is hereby granted" in text

    def test_has_copyright(self) -> None:
        text = LICENSE.read_text(encoding="utf-8")
        assert "Copyright" in text


class TestPyproject:
    def test_exists(self) -> None:
        assert PYPROJECT.is_file()

    def test_declares_mit(self) -> None:
        text = PYPROJECT.read_text(encoding="utf-8")
        assert "MIT" in text
        assert "license" in text.lower()


class TestPackageJson:
    def test_exists(self) -> None:
        assert PACKAGE_JSON.is_file()

    def test_declares_mit(self) -> None:
        data = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
        assert data.get("license") == "MIT"


class TestTauriConf:
    def test_exists(self) -> None:
        assert TAURI_CONF.is_file()

    def test_declares_mit(self) -> None:
        data = json.loads(TAURI_CONF.read_text(encoding="utf-8"))
        assert data.get("bundle", {}).get("license") == "MIT"


class TestCargoToml:
    def test_exists(self) -> None:
        assert CARGO_TOML.is_file()

    def test_declares_mit(self) -> None:
        text = CARGO_TOML.read_text(encoding="utf-8")
        assert 'license = "MIT"' in text


class TestADR:
    def test_exists(self) -> None:
        assert ADR.is_file()

    def test_references_mit(self) -> None:
        text = ADR.read_text(encoding="utf-8")
        assert "MIT" in text

    def test_compares_apache(self) -> None:
        text = ADR.read_text(encoding="utf-8")
        assert "Apache-2.0" in text

    def test_references_codex_opencode(self) -> None:
        text = ADR.read_text(encoding="utf-8")
        assert "Codex" in text or "OpenCode" in text

    def test_discusses_patents(self) -> None:
        text = ADR.read_text(encoding="utf-8")
        assert "patent" in text.lower()

    def test_references_third_party_notices(self) -> None:
        text = ADR.read_text(encoding="utf-8")
        assert "THIRD_PARTY_NOTICES" in text

    def test_has_decision(self) -> None:
        text = ADR.read_text(encoding="utf-8")
        assert "Decision" in text or "Accepted" in text


class TestNoConflictingLicenses:
    """Ensure no GPL/AGPL licenses in project metadata."""

    CONFLICTING = ["GPL-2.0", "GPL-3.0", "AGPL-3.0", "LGPL-2.1", "LGPL-3.0", "SSPL"]

    def test_pyproject_no_conflicting(self) -> None:
        text = PYPROJECT.read_text(encoding="utf-8")
        for lic in self.CONFLICTING:
            assert lic not in text, f"Conflicting license {lic} in pyproject.toml"

    def test_package_json_no_conflicting(self) -> None:
        text = PACKAGE_JSON.read_text(encoding="utf-8")
        for lic in self.CONFLICTING:
            assert lic not in text, f"Conflicting license {lic} in package.json"
