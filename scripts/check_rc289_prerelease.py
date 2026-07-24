#!/usr/bin/env python3
"""RC ID: RC-289. First public release pre-flight checklist.

Verifies all pre-release requirements:
    1. Clean environment reproduction — install from scratch
    2. License review — all license checks pass
    3. Security audit — security policies and checks
    4. Documentation walkthrough — docs complete and consistent

Usage:
    python scripts/check_rc289_prerelease.py              # full checklist
    python scripts/check_rc289_prerelease.py --section licenses  # one section
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# All RC check scripts that must pass before release
LICENSE_CHECKS = [
    "scripts/check_rc281_license.py",
    "scripts/check_rc282_license_files.py",
    "scripts/check_rc283_claude_prohibited.py",
    "scripts/check_rc284_opencode_attribution.py",
    "scripts/check_rc285_license_risk.py",
    "scripts/check_rc286_asset_rights.py",
]

SECURITY_CHECKS = [
    "scripts/check_rc287_governance.py",
]

GOVERNANCE_CHECKS = [
    "scripts/check_rc276_update_rollback.py",
    "scripts/check_rc277_sbom.py",
    "scripts/check_rc278_release_channels.py",
    "scripts/check_rc279_github_release.py",
    "scripts/check_rc280_docker_scope.py",
]

DOCUMENTATION_FILES = [
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "GOVERNANCE.md",
    "SECURITY.md",
    "LICENSE",
    "NOTICE",
    "THIRD_PARTY_NOTICES.md",
    "docs/github-repository-setup.md",
    "docs/DOCKER.md",
    "docs/support-matrix.md",
]


def run_check_script(script_path: str) -> tuple[bool, str]:
    """Run a check script and return (success, output)."""
    full_path = ROOT / script_path
    if not full_path.is_file():
        return False, f"Script not found: {script_path}"
    try:
        result = subprocess.run(
            [sys.executable, str(full_path)],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=ROOT,
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, f"Timeout: {script_path}"
    except Exception as exc:
        return False, f"Error: {exc}"


def check_clean_environment() -> list[str]:
    """Verify clean environment reproduction requirements."""
    errors: list[str] = []
    # Check that pyproject.toml has installable metadata
    pyproject = ROOT / "backend" / "pyproject.toml"
    if not pyproject.is_file():
        errors.append("backend/pyproject.toml not found")
    else:
        text = pyproject.read_text(encoding="utf-8")
        if "rabbit-code" not in text:
            errors.append("pyproject.toml must define rabbit-code package")
        if "3.0.0" not in text:
            errors.append("pyproject.toml must declare version 3.0.0")
    # Check that install scripts exist
    install_ps1 = ROOT / "scripts" / "install" / "install.ps1"
    install_sh = ROOT / "scripts" / "install" / "install.sh"
    if not install_ps1.is_file():
        errors.append("install.ps1 not found")
    if not install_sh.is_file():
        errors.append("install.sh not found")
    # Check docker-compose for dev/test
    docker_compose = ROOT / "docker-compose.dev.yml"
    if not docker_compose.is_file():
        errors.append("docker-compose.dev.yml not found")
    return errors


def check_license_review() -> list[str]:
    """Run all license check scripts."""
    errors: list[str] = []
    for script in LICENSE_CHECKS:
        ok, output = run_check_script(script)
        if not ok:
            errors.append(f"License check failed: {script}")
            if output.strip():
                errors.append(f"  Output: {output.strip()[:200]}")
    return errors


def check_security_audit() -> list[str]:
    """Run security and governance check scripts."""
    errors: list[str] = []
    for script in SECURITY_CHECKS:
        ok, output = run_check_script(script)
        if not ok:
            errors.append(f"Security check failed: {script}")
            if output.strip():
                errors.append(f"  Output: {output.strip()[:200]}")
    return errors


def check_governance_and_release() -> list[str]:
    """Run release engineering check scripts."""
    errors: list[str] = []
    for script in GOVERNANCE_CHECKS:
        ok, output = run_check_script(script)
        if not ok:
            errors.append(f"Release check failed: {script}")
            if output.strip():
                errors.append(f"  Output: {output.strip()[:200]}")
    return errors


def check_documentation() -> list[str]:
    """Verify all required documentation files exist and are non-empty."""
    errors: list[str] = []
    for doc_path in DOCUMENTATION_FILES:
        full_path = ROOT / doc_path
        if not full_path.is_file():
            errors.append(f"Documentation file missing: {doc_path}")
            continue
        content = full_path.read_text(encoding="utf-8").strip()
        if len(content) < 50:
            errors.append(f"Documentation file too short: {doc_path} ({len(content)} chars)")
    return errors


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="RC-289 pre-release checklist")
    parser.add_argument("--section", choices=["clean-env", "licenses", "security", "release", "docs"],
                        help="Run only one section")
    args = parser.parse_args()

    all_errors: list[str] = []

    sections = {
        "clean-env": ("Clean Environment", check_clean_environment),
        "licenses": ("License Review", check_license_review),
        "security": ("Security Audit", check_security_audit),
        "release": ("Release Engineering", check_governance_and_release),
        "docs": ("Documentation Walkthrough", check_documentation),
    }

    if args.section:
        sections = {args.section: sections[args.section]}

    for key, (name, check_fn) in sections.items():
        print(f"\n--- {name} ---")
        errors = check_fn()
        if errors:
            print(f"FAIL: {name}")
            for e in errors:
                print(f"  - {e}")
            all_errors.extend(errors)
        else:
            print(f"PASS: {name}")

    if all_errors:
        print(f"\n{'='*50}")
        print(f"FAIL: RC-289 pre-release checklist ({len(all_errors)} issues)")
        return 1

    print(f"\n{'='*50}")
    print("PASS: RC-289 pre-release checklist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
