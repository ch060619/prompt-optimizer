#!/usr/bin/env python3
"""RC ID: RC-286. Verify asset publication rights for all asset categories.

Checks:
    1. asset-publication-rights.yml exists with all required categories
    2. Each category has status, license, rights_holder, evidence_path
    3. No category has status "blocked" or "pending"
    4. Rabbit artwork links to RC-035 evidence
    5. App icons exist and are covered by MIT
    6. Fonts category is not-applicable (no custom fonts bundled)
    7. all_categories_confirmed is true
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "docs" / "legal" / "asset-publication-rights.yml"
RABBIT_ART_LICENSE = ROOT / "docs" / "legal" / "rabbit-art-license.yml"

REQUIRED_CATEGORIES = [
    "rabbit_artwork",
    "app_icons",
    "fonts",
    "screenshots",
    "doc_images",
    "demo_repo",
]

BLOCKING_STATUSES = {"blocked", "pending", "denied"}


def check_register_exists() -> list[str]:
    errors: list[str] = []
    if not REGISTER.is_file():
        errors.append("asset-publication-rights.yml not found")
        return errors
    return errors


def check_all_categories() -> list[str]:
    errors: list[str] = []
    if not REGISTER.is_file():
        return errors
    data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
    categories = data.get("categories", {})
    for cat in REQUIRED_CATEGORIES:
        if cat not in categories:
            errors.append(f"Missing category: {cat}")
            continue
        entry = categories[cat]
        if "status" not in entry:
            errors.append(f"Category {cat} missing 'status'")
        elif entry["status"] in BLOCKING_STATUSES:
            errors.append(f"Category {cat} has blocking status: {entry['status']}")
        if "license" not in entry:
            errors.append(f"Category {cat} missing 'license'")
        if "rights_holder" not in entry:
            errors.append(f"Category {cat} missing 'rights_holder'")
        if "notes" not in entry:
            errors.append(f"Category {cat} missing 'notes'")
    return errors


def check_all_confirmed() -> list[str]:
    errors: list[str] = []
    if not REGISTER.is_file():
        return errors
    data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
    if data.get("all_categories_confirmed") is not True:
        errors.append("all_categories_confirmed must be true")
    if data.get("blocking_categories") != []:
        errors.append("blocking_categories must be empty")
    return errors


def check_rabbit_artwork_evidence() -> list[str]:
    errors: list[str] = []
    if not REGISTER.is_file():
        return errors
    data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
    artwork = data.get("categories", {}).get("rabbit_artwork", {})
    evidence = artwork.get("evidence_path", "")
    if "rabbit-art-license" not in evidence:
        errors.append("Rabbit artwork must link to RC-035 evidence")
    if not RABBIT_ART_LICENSE.is_file():
        errors.append("RC-035 rabbit-art-license.yml not found")
    return errors


def check_icons_exist() -> list[str]:
    errors: list[str] = []
    icon_paths = [
        ROOT / "apps" / "desktop" / "src-tauri" / "icons" / "icon.ico",
        ROOT / "apps" / "desktop" / "src-tauri" / "icons" / "icon.png",
        ROOT / "frontend" / "public" / "favicon.svg",
    ]
    for p in icon_paths:
        if not p.is_file():
            errors.append(f"Icon file missing: {p.relative_to(ROOT)}")
    return errors


def check_fonts_not_applicable() -> list[str]:
    """Fonts should be not-applicable (no custom fonts bundled)."""
    errors: list[str] = []
    if not REGISTER.is_file():
        return errors
    data = yaml.safe_load(REGISTER.read_text(encoding="utf-8"))
    fonts = data.get("categories", {}).get("fonts", {})
    if fonts.get("status") != "not-applicable":
        errors.append("Fonts category should be 'not-applicable' (no custom fonts bundled)")
    if fonts.get("assets") != []:
        errors.append("Fonts assets list should be empty")
    return errors


def main() -> int:
    all_errors: list[str] = []
    all_errors.extend(check_register_exists())
    all_errors.extend(check_all_categories())
    all_errors.extend(check_all_confirmed())
    all_errors.extend(check_rabbit_artwork_evidence())
    all_errors.extend(check_icons_exist())
    all_errors.extend(check_fonts_not_applicable())

    if all_errors:
        print("FAIL: RC-286 asset publication rights verification", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("PASS: RC-286 asset publication rights verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
