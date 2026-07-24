#!/usr/bin/env python3
"""RC ID: RC-287. Verify maintainer governance policies.

Checks:
    1. GOVERNANCE.md exists with all required sections
    2. SECURITY.md exists with vulnerability reporting policy
    3. CODEOWNERS exists for sensitive paths
    4. No signed commits requirement
    5. No signed tags requirement
    6. Release approval process documented
    7. Dependency update policy documented
    8. Security response timeline documented
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE = ROOT / "GOVERNANCE.md"
SECURITY = ROOT / "SECURITY.md"
CODEOWNERS = ROOT / ".github" / "CODEOWNERS"


def check_governance() -> list[str]:
    errors: list[str] = []
    if not GOVERNANCE.is_file():
        errors.append("GOVERNANCE.md not found")
        return errors
    text = GOVERNANCE.read_text(encoding="utf-8")
    required_sections = [
        "Maintainer Permissions",
        "Branch Protection",
        "Release Approval",
        "Dependency Updates",
        "Security Response",
        "CODEOWNERS",
    ]
    for section in required_sections:
        if section not in text:
            errors.append(f"GOVERNANCE.md missing section: {section}")
    # Check no signed commits
    if "NOT require signed commits" not in text and "not required" not in text.lower():
        if "signed" in text.lower():
            errors.append("GOVERNANCE.md should state signed commits are NOT required")
    if "NOT require signed tags" not in text and "signed tags" not in text.lower():
        # Make sure it explicitly says no signed tags
        if "signed tag" in text.lower():
            errors.append("GOVERNANCE.md should state signed tags are NOT required")
    return errors


def check_security() -> list[str]:
    errors: list[str] = []
    if not SECURITY.is_file():
        errors.append("SECURITY.md not found")
        return errors
    text = SECURITY.read_text(encoding="utf-8")
    if "Security Advisory" not in text and "security advisory" not in text.lower():
        errors.append("SECURITY.md must mention Security Advisory reporting")
    if "72 hours" not in text:
        errors.append("SECURITY.md must mention 72-hour acknowledgment")
    if "Critical" not in text or "High" not in text:
        errors.append("SECURITY.md must have severity levels")
    return errors


def check_codeowners() -> list[str]:
    errors: list[str] = []
    if not CODEOWNERS.is_file():
        errors.append(".github/CODEOWNERS not found")
        return errors
    text = CODEOWNERS.read_text(encoding="utf-8")
    required_paths = [
        "/docs/legal/",
        "/docs/adr/",
        "/.github/workflows/",
        "/scripts/",
        "/LICENSE",
        "/NOTICE",
        "/THIRD_PARTY_NOTICES.md",
    ]
    for path in required_paths:
        if path not in text:
            errors.append(f"CODEOWNERS missing path: {path}")
    return errors


def check_no_signed_commits_requirement() -> list[str]:
    """Verify that the project does NOT require signed commits or tags."""
    errors: list[str] = []
    # Check CI doesn't require GPG signing
    ci = ROOT / ".github" / "workflows" / "ci.yml"
    if ci.is_file():
        text = ci.read_text(encoding="utf-8")
        if "GPG" in text or "gpg" in text:
            errors.append("CI should not require GPG signing")
        if "require_signed_commits" in text:
            errors.append("CI should not require signed commits")
    # Check release workflow doesn't sign tags
    release = ROOT / ".github" / "workflows" / "release.yml"
    if release.is_file():
        text = release.read_text(encoding="utf-8")
        if "gpg" in text.lower() and "sign" in text.lower():
            errors.append("Release workflow should not use GPG signing")
    return errors


def main() -> int:
    all_errors: list[str] = []
    all_errors.extend(check_governance())
    all_errors.extend(check_security())
    all_errors.extend(check_codeowners())
    all_errors.extend(check_no_signed_commits_requirement())

    if all_errors:
        print("FAIL: RC-287 governance verification", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("PASS: RC-287 governance verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
