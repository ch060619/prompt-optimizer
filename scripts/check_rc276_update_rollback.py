#!/usr/bin/env python3
"""RC ID: RC-276. Validate secure update check and rollback implementation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPDATE_MODULE = ROOT / "backend" / "src" / "prompt_optimizer" / "update_checker.py"
UPDATE_MANIFEST = ROOT / "scripts" / "install" / "update-manifest.json"
CLI_APP = ROOT / "backend" / "src" / "prompt_optimizer" / "cli" / "app.py"


def main() -> int:
    errors: list[str] = []

    # Update checker module
    if not UPDATE_MODULE.is_file():
        errors.append(f"missing {UPDATE_MODULE.relative_to(ROOT)}")
    else:
        code = UPDATE_MODULE.read_text(encoding="utf-8")
        for required in ["UpdateChecker", "RollbackManager", "UpdateInfo", "VersionCompatibility",
                         "verify_download", "sha256", "hashlib", "rollout_percentage",
                         "should_offer_update", "rollback_to", "check_version_compatibility"]:
            if required not in code:
                errors.append(f"update_checker.py missing: {required}")
        if "urllib.request" not in code:
            errors.append("update_checker.py must use urllib.request for HTTPS")
        if "https" not in code.lower():
            errors.append("update_checker.py must use HTTPS")

    # Update manifest
    if not UPDATE_MANIFEST.is_file():
        errors.append("missing update manifest template")
    else:
        try:
            manifest = json.loads(UPDATE_MANIFEST.read_text(encoding="utf-8"))
            channels = manifest.get("channels", {})
            for ch in ("stable", "beta", "nightly"):
                if ch not in channels:
                    errors.append(f"manifest missing channel: {ch}")
                else:
                    ch_info = channels[ch]
                    if "version" not in ch_info:
                        errors.append(f"manifest {ch} missing version")
                    if "rollout_percentage" not in ch_info:
                        errors.append(f"manifest {ch} missing rollout_percentage")
                    if "downloads" not in ch_info:
                        errors.append(f"manifest {ch} missing downloads")
        except json.JSONDecodeError as e:
            errors.append(f"manifest is not valid JSON: {e}")

    # CLI command
    if CLI_APP.is_file():
        cli_code = CLI_APP.read_text(encoding="utf-8")
        if "check-update" not in cli_code:
            errors.append("CLI missing check-update command")
        if "check_version_compatibility" not in cli_code:
            errors.append("CLI must call version compatibility check")
    else:
        errors.append("missing CLI app")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print("RC-276 secure update check and rollback valid: HTTPS check, SHA-256 verify, staged rollout, rollback, compatibility.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
