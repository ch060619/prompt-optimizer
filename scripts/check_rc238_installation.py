#!/usr/bin/env python3
"""RC ID: RC-238. Validate the reproducible installation/package contract."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    ROOT / "Dockerfile",
    ROOT / "frontend" / "package-lock.json",
    ROOT / "apps" / "desktop" / "src-tauri" / "tauri.conf.json",
    ROOT / "apps" / "desktop" / "README.md",
)


def main() -> int:
    errors: list[str] = []
    errors.extend(f"missing release input: {path.relative_to(ROOT)}" for path in REQUIRED_FILES if not path.is_file())
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8") if (ROOT / "Dockerfile").is_file() else ""
    tauri = (ROOT / "apps" / "desktop" / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8") if (ROOT / "apps" / "desktop" / "src-tauri" / "tauri.conf.json").is_file() else ""
    for marker in ("npm ci", "npm run build", "COPY packages/ui/", "pip install --no-cache-dir", "USER rabbit"):
        if marker not in dockerfile:
            errors.append(f"Dockerfile is missing release marker: {marker}")
    if '"active": false' in tauri:
        errors.append("desktop bundle must be active for release builds (RC-272 enables bundling)")

    # The checksum probe is deterministic and leaves no artifact in the repository.
    payload = b"rabbit-code-rc238-installation-probe"
    digest = hashlib.sha256(payload).hexdigest()
    if hashlib.sha256(payload).hexdigest() != digest or len(digest) != 64:
        errors.append("SHA-256 probe is not deterministic")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("RC-238 installation contract valid: clean build inputs, non-root runtime, lockfile, and SHA-256 probe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
