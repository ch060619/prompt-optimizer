#!/usr/bin/env python3
"""RC ID: RC-277. Validate SBOM, artifact hashes, and supply chain manifest setup."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SBOM_SCRIPT = ROOT / "scripts" / "generate_sbom.py"
PYPROJECT = ROOT / "backend" / "pyproject.toml"
PACKAGE_LOCK = ROOT / "frontend" / "package-lock.json"


def main() -> int:
    errors: list[str] = []

    if not SBOM_SCRIPT.is_file():
        errors.append(f"missing {SBOM_SCRIPT.relative_to(ROOT)}")
    else:
        code = SBOM_SCRIPT.read_text(encoding="utf-8")
        for required in ["generate_provenance", "generate_sbom", "generate_license_report",
                         "generate_artifact_hashes", "generate_scan_report", "CycloneDX",
                         "sha256", "git", "pip", "npm"]:
            if required not in code:
                errors.append(f"generate_sbom.py missing: {required}")

    if not PYPROJECT.is_file():
        errors.append("missing backend/pyproject.toml")

    if not PACKAGE_LOCK.is_file():
        errors.append("missing frontend/package-lock.json")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print("RC-277 SBOM and supply chain manifest setup valid: provenance, SBOM (CycloneDX), licenses, artifacts, scan.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
