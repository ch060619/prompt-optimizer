#!/usr/bin/env python3
"""RC ID: RC-274. Validate reproducible packaging setup."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIDECAR_SPEC = ROOT / "apps" / "desktop" / "sidecar.spec"
BUILD_SCRIPT = ROOT / "scripts" / "build_reproducible.py"
FRONTEND_LOCK = ROOT / "frontend" / "package-lock.json"


def main() -> int:
    errors: list[str] = []

    # Sidecar spec
    if not SIDECAR_SPEC.is_file():
        errors.append(f"missing sidecar spec: {SIDECAR_SPEC.relative_to(ROOT)}")
    else:
        content = SIDECAR_SPEC.read_text(encoding="utf-8")
        if "upx=False" not in content:
            errors.append("sidecar spec must disable UPX for reproducibility")
        if "strip=False" not in content:
            errors.append("sidecar spec must disable strip for reproducibility")
        if "rabbit-sidecar" not in content:
            errors.append("sidecar spec must name output 'rabbit-sidecar'")
        if "prompt_optimizer" not in content:
            errors.append("sidecar spec must reference prompt_optimizer package")
        if "uvicorn" not in content:
            errors.append("sidecar spec must include uvicorn as hidden import")

    # Build script
    if not BUILD_SCRIPT.is_file():
        errors.append(f"missing build script: {BUILD_SCRIPT.relative_to(ROOT)}")
    else:
        content = BUILD_SCRIPT.read_text(encoding="utf-8")
        if "SOURCE_DATE_EPOCH" not in content:
            errors.append("build script must set SOURCE_DATE_EPOCH for deterministic builds")
        if "build_manifest" not in content and "build-manifest" not in content and "write_manifest" not in content:
            errors.append("build script must generate a build manifest")
        if "_sha256" not in content:
            errors.append("build script must compute SHA-256 hashes")

    # Frontend lock file
    if not FRONTEND_LOCK.is_file():
        errors.append("missing frontend/package-lock.json for reproducible npm builds")

    # pyproject.toml has version pin
    pyproject = ROOT / "backend" / "pyproject.toml"
    if pyproject.is_file():
        content = pyproject.read_text(encoding="utf-8")
        if "version" not in content:
            errors.append("pyproject.toml must define a version")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print("RC-274 reproducible packaging setup valid: sidecar spec, build script, lock files, manifest generation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
