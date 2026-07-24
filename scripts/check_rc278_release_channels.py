#!/usr/bin/env python3
"""RC ID: RC-278. Validate release channels, changelog, and migration gates."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = ROOT / "CHANGELOG.md"
RELEASE_CHANNELS = ROOT / "backend" / "src" / "prompt_optimizer" / "release_channels.py"
UPDATE_MANIFEST = ROOT / "scripts" / "install" / "update-manifest.json"
MIGRATIONS = ROOT / "backend" / "src" / "prompt_optimizer" / "storage" / "migrations.py"


def main() -> int:
    errors: list[str] = []

    # CHANGELOG.md
    if not CHANGELOG.is_file():
        errors.append("missing CHANGELOG.md")
    else:
        content = CHANGELOG.read_text(encoding="utf-8")
        if "Semantic Versioning" not in content:
            errors.append("CHANGELOG.md must reference Semantic Versioning")
        if "nightly" not in content or "beta" not in content or "stable" not in content:
            errors.append("CHANGELOG.md must document all three channels")
        if "[3.0.0]" not in content:
            errors.append("CHANGELOG.md must have a 3.0.0 release entry")

    # release_channels.py
    if not RELEASE_CHANNELS.is_file():
        errors.append(f"missing {RELEASE_CHANNELS.relative_to(ROOT)}")
    else:
        code = RELEASE_CHANNELS.read_text(encoding="utf-8")
        for required in ["ReleaseChannel", "ChannelConfig", "MigrationGate",
                         "parse_channel_from_version", "validate_version_for_channel",
                         "CHANNEL_PATTERNS", "nightly", "beta", "stable"]:
            if required not in code:
                errors.append(f"release_channels.py missing: {required}")

    # Update manifest has channels
    if UPDATE_MANIFEST.is_file():
        import json
        manifest = json.loads(UPDATE_MANIFEST.read_text(encoding="utf-8"))
        channels = manifest.get("channels", {})
        for ch in ("stable", "beta", "nightly"):
            if ch not in channels:
                errors.append(f"update-manifest.json missing channel: {ch}")

    # Migrations module
    if not MIGRATIONS.is_file():
        errors.append("missing migrations.py")
    else:
        code = MIGRATIONS.read_text(encoding="utf-8")
        if "TARGET_SCHEMA_VERSION" not in code:
            errors.append("migrations.py must define TARGET_SCHEMA_VERSION")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print("RC-278 release channels valid: nightly/beta/stable, semver changelog, migration gate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
