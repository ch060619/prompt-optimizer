#!/usr/bin/env python3
"""RC ID: RC-272. Validate desktop installer build configuration."""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAURI_CONF = ROOT / "apps" / "desktop" / "src-tauri" / "tauri.conf.json"
BUILD_SCRIPT = ROOT / "scripts" / "build_desktop.py"

EXPECTED_TARGETS = {
    "Windows": ["nsis", "msi"],
    "Linux": ["appimage", "deb", "rpm"],
}


def main() -> int:
    errors: list[str] = []

    if not TAURI_CONF.is_file():
        errors.append(f"missing {TAURI_CONF.relative_to(ROOT)}")
        print("\n".join(f"ERROR: {e}" for e in errors), file=sys.stderr)
        return 1

    conf = json.loads(TAURI_CONF.read_text(encoding="utf-8"))
    bundle = conf.get("bundle", {})

    if not bundle.get("active"):
        errors.append("bundle.active must be true for release builds")

    if bundle.get("targets") != "all":
        errors.append("bundle.targets must be 'all' to cover both platforms")

    icons = bundle.get("icon", [])
    if len(icons) < 2:
        errors.append("bundle.icon must include at least .ico and .png")
    for icon in icons:
        icon_path = ROOT / "apps" / "desktop" / "src-tauri" / icon
        if not icon_path.is_file():
            errors.append(f"missing icon: {icon}")

    if not bundle.get("publisher"):
        errors.append("bundle.publisher must be set")
    if not bundle.get("category"):
        errors.append("bundle.category must be set")
    if not bundle.get("shortDescription"):
        errors.append("bundle.shortDescription must be set")
    if not bundle.get("longDescription"):
        errors.append("bundle.longDescription must be set")

    # Windows config
    win = bundle.get("windows", {})
    if "nsis" not in win and "wix" not in win:
        errors.append("bundle.windows must configure nsis or wix")

    # Linux config
    linux = bundle.get("linux", {})
    if "deb" not in linux:
        errors.append("bundle.linux must configure deb")

    # No macOS (explicitly excluded)
    macos = bundle.get("macOS", {})
    if macos:
        errors.append("bundle.macOS must not be configured (macOS excluded from release)")

    # Build script exists
    if not BUILD_SCRIPT.is_file():
        errors.append(f"missing {BUILD_SCRIPT.relative_to(ROOT)}")

    # Identifier
    identifier = conf.get("identifier", "")
    if not identifier or "rabbitcode" not in identifier:
        errors.append("identifier must contain 'rabbitcode'")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    current_os = platform.system()
    expected = EXPECTED_TARGETS.get(current_os, [])
    print(f"RC-272 desktop build config valid. OS={current_os}, targets={expected}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
