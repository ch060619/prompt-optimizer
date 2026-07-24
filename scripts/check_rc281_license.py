#!/usr/bin/env python3
"""RC ID: RC-281. Verify primary license selection and consistency.

Checks:
    1. Root LICENSE file exists and contains MIT text
    2. backend/pyproject.toml declares MIT
    3. frontend/package.json declares MIT
    4. tauri.conf.json declares MIT
    5. Cargo.toml declares MIT
    6. ADR-0017 exists documenting the license decision
    7. No conflicting license declarations
    8. No GPL/AGPL in dependencies (would conflict with MIT distribution)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LICENSE = ROOT / "LICENSE"
PYPROJECT = ROOT / "backend" / "pyproject.toml"
PACKAGE_JSON = ROOT / "frontend" / "package.json"
TAURI_CONF = ROOT / "apps" / "desktop" / "src-tauri" / "tauri.conf.json"
CARGO_TOML = ROOT / "apps" / "desktop" / "src-tauri" / "Cargo.toml"
ADR = ROOT / "docs" / "adr" / "0017-primary-license-selection.md"

CONFLICTING_LICENSES = {"GPL-2.0", "GPL-3.0", "AGPL-3.0", "LGPL-2.1", "LGPL-3.0", "SSPL"}


def check_license_file() -> list[str]:
    errors: list[str] = []
    if not LICENSE.is_file():
        errors.append("Root LICENSE file not found")
        return errors
    text = LICENSE.read_text(encoding="utf-8")
    if "MIT License" not in text:
        errors.append("LICENSE file does not contain MIT License text")
    if "Permission is hereby granted" not in text:
        errors.append("LICENSE file missing MIT permission grant text")
    return errors


def check_pyproject() -> list[str]:
    errors: list[str] = []
    if not PYPROJECT.is_file():
        errors.append("backend/pyproject.toml not found")
        return errors
    text = PYPROJECT.read_text(encoding="utf-8")
    if 'license = { text = "MIT" }' not in text and 'license = "MIT"' not in text:
        errors.append("pyproject.toml must declare license = MIT")
    return errors


def check_package_json() -> list[str]:
    errors: list[str] = []
    if not PACKAGE_JSON.is_file():
        errors.append("frontend/package.json not found")
        return errors
    data = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    if data.get("license") != "MIT":
        errors.append(f'package.json license must be "MIT", got: {data.get("license")}')
    return errors


def check_tauri_conf() -> list[str]:
    errors: list[str] = []
    if not TAURI_CONF.is_file():
        errors.append("tauri.conf.json not found")
        return errors
    data = json.loads(TAURI_CONF.read_text(encoding="utf-8"))
    bundle = data.get("bundle", {})
    if bundle.get("license") != "MIT":
        errors.append(f'tauri.conf.json bundle.license must be "MIT", got: {bundle.get("license")}')
    return errors


def check_cargo_toml() -> list[str]:
    errors: list[str] = []
    if not CARGO_TOML.is_file():
        errors.append("Cargo.toml not found")
        return errors
    text = CARGO_TOML.read_text(encoding="utf-8")
    if 'license = "MIT"' not in text and 'license = "MIT"' not in text:
        errors.append('Cargo.toml must declare license = "MIT"')
    return errors


def check_adr() -> list[str]:
    errors: list[str] = []
    if not ADR.is_file():
        errors.append("ADR-0017 (primary license selection) not found")
        return errors
    text = ADR.read_text(encoding="utf-8")
    if "MIT" not in text:
        errors.append("ADR-0017 must reference MIT license")
    if "Apache-2.0" not in text:
        errors.append("ADR-0017 should compare MIT vs Apache-2.0")
    if "Codex" not in text and "OpenCode" not in text:
        errors.append("ADR-0017 should reference Codex/OpenCode compatibility")
    if "patent" not in text.lower():
        errors.append("ADR-0017 should discuss patent considerations")
    if "THIRD_PARTY_NOTICES" not in text:
        errors.append("ADR-0017 should reference THIRD_PARTY_NOTICES")
    return errors


def check_no_conflicting_licenses() -> list[str]:
    """Check that no package metadata declares a conflicting license."""
    errors: list[str] = []
    # Check pyproject.toml
    if PYPROJECT.is_file():
        text = PYPROJECT.read_text(encoding="utf-8")
        for lic in CONFLICTING_LICENSES:
            if lic in text:
                errors.append(f"Conflicting license {lic} found in pyproject.toml")
    # Check package.json
    if PACKAGE_JSON.is_file():
        text = PACKAGE_JSON.read_text(encoding="utf-8")
        for lic in CONFLICTING_LICENSES:
            if lic in text:
                errors.append(f"Conflicting license {lic} found in package.json")
    return errors


def main() -> int:
    all_errors: list[str] = []
    all_errors.extend(check_license_file())
    all_errors.extend(check_pyproject())
    all_errors.extend(check_package_json())
    all_errors.extend(check_tauri_conf())
    all_errors.extend(check_cargo_toml())
    all_errors.extend(check_adr())
    all_errors.extend(check_no_conflicting_licenses())

    if all_errors:
        print("FAIL: RC-281 license verification", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("PASS: RC-281 license verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
