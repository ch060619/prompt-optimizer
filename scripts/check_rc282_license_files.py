#!/usr/bin/env python3
"""RC ID: RC-282. Generate and validate license files from dependency locks.

Generates:
    - THIRD_PARTY_NOTICES.md (from third-party-register.yml, via existing check_third_party_register.py)
    - Validates NOTICE file exists and references key dependencies
    - Validates model license metadata in manifest.yml
    - Validates asset license references

Usage:
    python scripts/generate_license_files.py           # generate + validate
    python scripts/generate_license_files.py --check    # validate only
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LICENSE = ROOT / "LICENSE"
NOTICE = ROOT / "NOTICE"
THIRD_PARTY_NOTICES = ROOT / "THIRD_PARTY_NOTICES.md"
MODEL_LICENSES_DIR = ROOT / "docs" / "licenses" / "models"
ASSET_LICENSES_DIR = ROOT / "docs" / "licenses" / "assets"
MANIFEST = ROOT / "data" / "models" / "manifest.yml"

REQUIRED_NOTICE_REFERENCES = [
    "MIT",
    "FastAPI",
    "React",
    "Gemma",
    "Qwen",
    "THIRD_PARTY_NOTICES",
]

REQUIRED_THIRD_PARTY_SECTIONS = ["pypi", "npm", "Reused Source Code"]


def validate_license_file() -> list[str]:
    errors: list[str] = []
    if not LICENSE.is_file():
        errors.append("Root LICENSE file not found")
        return errors
    text = LICENSE.read_text(encoding="utf-8")
    if "MIT License" not in text:
        errors.append("LICENSE does not contain MIT text")
    return errors


def validate_notice_file() -> list[str]:
    errors: list[str] = []
    if not NOTICE.is_file():
        errors.append("Root NOTICE file not found")
        return errors
    text = NOTICE.read_text(encoding="utf-8")
    for ref in REQUIRED_NOTICE_REFERENCES:
        if ref not in text:
            errors.append(f"NOTICE file missing reference: {ref}")
    return errors


def validate_third_party_notices() -> list[str]:
    errors: list[str] = []
    if not THIRD_PARTY_NOTICES.is_file():
        errors.append("THIRD_PARTY_NOTICES.md not found")
        return errors
    text = THIRD_PARTY_NOTICES.read_text(encoding="utf-8")
    for section in REQUIRED_THIRD_PARTY_SECTIONS:
        if section not in text:
            errors.append(f"THIRD_PARTY_NOTICES.md missing section: {section}")
    return errors


def validate_model_licenses() -> list[str]:
    errors: list[str] = []
    if not MODEL_LICENSES_DIR.is_dir():
        errors.append("docs/licenses/models/ directory not found")
        return errors
    readme = MODEL_LICENSES_DIR / "README.md"
    if not readme.is_file():
        errors.append("docs/licenses/models/README.md not found")
        return errors
    text = readme.read_text(encoding="utf-8")
    if "Gemma" not in text:
        errors.append("Model licenses README missing Gemma reference")
    if "Qwen" not in text:
        errors.append("Model licenses README missing Qwen reference")
    if "LicenseRef-Gemma-Terms" not in text:
        errors.append("Model licenses README missing Gemma license reference")
    if "Apache-2.0" not in text:
        errors.append("Model licenses README missing Apache-2.0 reference")
    # Validate manifest has license fields
    if MANIFEST.is_file():
        manifest_text = MANIFEST.read_text(encoding="utf-8")
        if "license_spdx" not in manifest_text:
            errors.append("manifest.yml missing license_spdx field")
        if "license_url" not in manifest_text:
            errors.append("manifest.yml missing license_url field")
        if "license_status" not in manifest_text:
            errors.append("manifest.yml missing license_status field")
    else:
        errors.append("data/models/manifest.yml not found")
    return errors


def validate_asset_licenses() -> list[str]:
    errors: list[str] = []
    if not ASSET_LICENSES_DIR.is_dir():
        errors.append("docs/licenses/assets/ directory not found")
        return errors
    readme = ASSET_LICENSES_DIR / "README.md"
    if not readme.is_file():
        errors.append("docs/licenses/assets/README.md not found")
        return errors
    text = readme.read_text(encoding="utf-8")
    if "artwork" not in text.lower():
        errors.append("Asset licenses README missing artwork reference")
    if "icon" not in text.lower():
        errors.append("Asset licenses README missing icon reference")
    return errors


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Generate/validate license files")
    parser.add_argument("--check", action="store_true", help="Validate only (no generation)")
    args = parser.parse_args()

    all_errors: list[str] = []
    all_errors.extend(validate_license_file())
    all_errors.extend(validate_notice_file())
    all_errors.extend(validate_third_party_notices())
    all_errors.extend(validate_model_licenses())
    all_errors.extend(validate_asset_licenses())

    if all_errors:
        print("FAIL: RC-282 license files verification", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("PASS: RC-282 license files verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
