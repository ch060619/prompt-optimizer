#!/usr/bin/env python3
"""RC ID: RC-273. Validate CLI installation channels and install scripts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "backend" / "pyproject.toml"
INSTALL_PS1 = ROOT / "scripts" / "install" / "install.ps1"
INSTALL_SH = ROOT / "scripts" / "install" / "install.sh"
WINGET_YML = ROOT / "scripts" / "install" / "winget.yml"
SCOOP_JSON = ROOT / "scripts" / "install" / "scoop.json"


def main() -> int:
    errors: list[str] = []

    # PyPI config in pyproject.toml
    pyproject = PYPROJECT.read_text(encoding="utf-8") if PYPROJECT.is_file() else ""
    if 'name = "rabbit-code"' not in pyproject:
        errors.append('pyproject.toml must define name = "rabbit-code"')
    if 'rabbit = ' not in pyproject:
        errors.append("pyproject.toml must define rabbit entry point")
    if 'prompt-opt = ' not in pyproject:
        errors.append("pyproject.toml must define prompt-opt entry point")

    # Install scripts
    for path, desc in [(INSTALL_PS1, "PowerShell"), (INSTALL_SH, "shell")]:
        if not path.is_file():
            errors.append(f"missing {desc} install script: {path.relative_to(ROOT)}")
            continue
        content = path.read_text(encoding="utf-8")
        if "rabbit-code" not in content:
            errors.append(f"{desc} install script must reference rabbit-code package")
        if "pip install" not in content:
            errors.append(f"{desc} install script must use pip install")

    # winget manifest
    if not WINGET_YML.is_file():
        errors.append("missing winget manifest")
    else:
        winget = WINGET_YML.read_text(encoding="utf-8")
        if "RabbitCode.RabbitCode" not in winget:
            errors.append("winget PackageIdentifier must be RabbitCode.RabbitCode")
        if "MIT" not in winget:
            errors.append("winget manifest must declare MIT license")

    # scoop manifest
    if not SCOOP_JSON.is_file():
        errors.append("missing scoop manifest")
    else:
        try:
            scoop = json.loads(SCOOP_JSON.read_text(encoding="utf-8"))
            if scoop.get("version") != "3.0.0":
                errors.append("scoop version must match project version")
            if "rabbit" not in scoop.get("bin", ""):
                errors.append("scoop bin must point to rabbit executable")
            if scoop.get("license") != "MIT":
                errors.append("scoop license must be MIT")
        except json.JSONDecodeError as e:
            errors.append(f"scoop manifest is not valid JSON: {e}")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print("RC-273 CLI installation channels valid: PyPI, PowerShell install, shell install, winget, scoop.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
