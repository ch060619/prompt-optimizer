#!/usr/bin/env python3
"""RC ID: RC-290. Verify post-release maintenance policy and milestone tracking.

Checks:
    1. MAINTENANCE.md exists with versioning, cadence, compatibility, security, deprecation
    2. R1-R6 milestone tracking is complete
    3. Competitive research documented (R2)
    4. License boundary confirmed (R3)
    5. Asset rights confirmed (R4)
    6. Platform scope defined (R5)
    7. Stable release acceptance criteria defined (R6)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAINTENANCE = ROOT / "docs" / "MAINTENANCE.md"
GOVERNANCE = ROOT / "GOVERNANCE.md"
SECURITY = ROOT / "SECURITY.md"
SUPPORT_MATRIX = ROOT / "docs" / "support-matrix.md"
CHANGELOG = ROOT / "CHANGELOG.md"


def check_maintenance_doc() -> list[str]:
    errors: list[str] = []
    if not MAINTENANCE.is_file():
        errors.append("docs/MAINTENANCE.md not found")
        return errors
    text = MAINTENANCE.read_text(encoding="utf-8")
    required = [
        "Versioning",
        "Release Cadence",
        "Compatibility Policy",
        "Security Patch Policy",
        "Dependency Update",
        "Deprecation Policy",
        "End of Life",
    ]
    for section in required:
        if section not in text:
            errors.append(f"MAINTENANCE.md missing section: {section}")
    # Check versioning follows SemVer
    if "Semantic Versioning" not in text:
        errors.append("MAINTENANCE.md must reference Semantic Versioning")
    # Check security patch timeline
    if "Critical" not in text or "7 days" not in text:
        errors.append("MAINTENANCE.md must have critical security patch timeline")
    return errors


def check_r1_tracking() -> list[str]:
    """R1: All RC items tracked in execution plan."""
    errors: list[str] = []
    plan = ROOT / "docs" / "rabbit-code-310-detailed-execution.md"
    if not plan.is_file():
        errors.append("Execution plan not found")
        return errors
    text = plan.read_text(encoding="utf-8")
    # Check progress table exists
    if "已完成项数" not in text:
        errors.append("Progress table missing from execution plan")
    # Check completion log exists
    if "进度记录一致性检查" not in text:
        errors.append("Completion log section missing from execution plan")
    return errors


def check_r2_competitive_research() -> list[str]:
    """R2: Competitive research documented."""
    errors: list[str] = []
    research_dir = ROOT / "docs" / "research"
    if not research_dir.is_dir():
        errors.append("docs/research/ directory not found")
        return errors
    # Check for competitive analysis or third-party register
    register = research_dir / "third-party-register.yml"
    if not register.is_file():
        errors.append("third-party-register.yml not found")
    return errors


def check_r3_license_boundary() -> list[str]:
    """R3: License boundary confirmed."""
    errors: list[str] = []
    adr_0003 = ROOT / "docs" / "adr" / "0003-opencode-research-boundary.md"
    adr_0017 = ROOT / "docs" / "adr" / "0017-primary-license-selection.md"
    if not adr_0003.is_file():
        errors.append("ADR-0003 (OpenCode boundary) not found")
    if not adr_0017.is_file():
        errors.append("ADR-0017 (license selection) not found")
    return errors


def check_r4_asset_rights() -> list[str]:
    """R4: Asset rights confirmed."""
    errors: list[str] = []
    asset_rights = ROOT / "docs" / "legal" / "asset-publication-rights.yml"
    if not asset_rights.is_file():
        errors.append("asset-publication-rights.yml not found")
    return errors


def check_r5_platform_scope() -> list[str]:
    """R5: Platform scope defined."""
    errors: list[str] = []
    if not SUPPORT_MATRIX.is_file():
        errors.append("docs/support-matrix.md not found")
        return errors
    text = SUPPORT_MATRIX.read_text(encoding="utf-8")
    if "Windows" not in text:
        errors.append("Support matrix must mention Windows")
    if "Linux" not in text:
        errors.append("Support matrix must mention Linux")
    return errors


def check_r6_stable_acceptance() -> list[str]:
    """R6: Stable release acceptance criteria defined."""
    errors: list[str] = []
    prerelease = ROOT / "scripts" / "check_rc289_prerelease.py"
    if not prerelease.is_file():
        errors.append("RC-289 pre-release checklist not found")
    if not CHANGELOG.is_file():
        errors.append("CHANGELOG.md not found")
    if not GOVERNANCE.is_file():
        errors.append("GOVERNANCE.md not found")
    return errors


def main() -> int:
    all_errors: list[str] = []
    all_errors.extend(check_maintenance_doc())
    all_errors.extend(check_r1_tracking())
    all_errors.extend(check_r2_competitive_research())
    all_errors.extend(check_r3_license_boundary())
    all_errors.extend(check_r4_asset_rights())
    all_errors.extend(check_r5_platform_scope())
    all_errors.extend(check_r6_stable_acceptance())

    if all_errors:
        print("FAIL: RC-290 maintenance policy and milestone verification", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("PASS: RC-290 maintenance policy and milestone verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
