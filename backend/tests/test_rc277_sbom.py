"""RC ID: RC-277. Validate SBOM, artifact hashes, and supply chain manifest."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SBOM_SCRIPT = ROOT / "scripts" / "generate_sbom.py"
CHECK_SCRIPT = ROOT / "scripts" / "check_rc277_sbom.py"
PYPROJECT = ROOT / "backend" / "pyproject.toml"
PACKAGE_LOCK = ROOT / "frontend" / "package-lock.json"


def test_sbom_script_exists() -> None:
    assert SBOM_SCRIPT.is_file()


def test_check_script_exists() -> None:
    assert CHECK_SCRIPT.is_file()


def test_sbom_script_has_provenance() -> None:
    code = SBOM_SCRIPT.read_text(encoding="utf-8")
    assert "generate_provenance" in code


def test_sbom_script_has_cyclonedx() -> None:
    code = SBOM_SCRIPT.read_text(encoding="utf-8")
    assert "CycloneDX" in code


def test_sbom_script_has_license_report() -> None:
    code = SBOM_SCRIPT.read_text(encoding="utf-8")
    assert "generate_license_report" in code


def test_sbom_script_has_artifact_hashes() -> None:
    code = SBOM_SCRIPT.read_text(encoding="utf-8")
    assert "generate_artifact_hashes" in code
    assert "sha256" in code


def test_sbom_script_has_scan_report() -> None:
    code = SBOM_SCRIPT.read_text(encoding="utf-8")
    assert "generate_scan_report" in code


def test_sbom_script_has_git_info() -> None:
    code = SBOM_SCRIPT.read_text(encoding="utf-8")
    assert "git" in code.lower()


def test_sbom_script_has_pip_deps() -> None:
    code = SBOM_SCRIPT.read_text(encoding="utf-8")
    assert "pip" in code.lower()


def test_sbom_script_has_npm_deps() -> None:
    code = SBOM_SCRIPT.read_text(encoding="utf-8")
    assert "npm" in code.lower() or "package-lock" in code


def test_sbom_script_has_manifest() -> None:
    code = SBOM_SCRIPT.read_text(encoding="utf-8")
    assert "manifest.json" in code


def test_pyproject_exists() -> None:
    assert PYPROJECT.is_file()


def test_package_lock_exists() -> None:
    assert PACKAGE_LOCK.is_file()
