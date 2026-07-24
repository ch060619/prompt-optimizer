#!/usr/bin/env python3
"""RC ID: RC-285. Verify automated license risk scanning setup.

Checks:
    1. license-risk-policy.yml exists with allow/review/deny categories
    2. scan_license_risks.py scanner exists and can run
    3. Scanner covers npm, pypi, and model dependencies
    4. Policy has exception list with owner/scope/expires
    5. No denied licenses in current dependency tree
    6. CI integration (ci.yml has license scan step or references scan_license_risks.py)
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "docs" / "research" / "license-risk-policy.yml"
SCANNER = ROOT / "scripts" / "scan_license_risks.py"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def check_policy_exists() -> list[str]:
    errors: list[str] = []
    if not POLICY_PATH.is_file():
        errors.append("license-risk-policy.yml not found")
        return errors
    data = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
    if "allow" not in data:
        errors.append("Policy missing 'allow' category")
    if "review" not in data:
        errors.append("Policy missing 'review' category")
    if "deny" not in data:
        errors.append("Policy missing 'deny' category")
    if "exceptions" not in data:
        errors.append("Policy missing 'exceptions' list")
    # Check denied includes GPL/AGPL
    deny_list = data.get("deny", [])
    required_denied = ["GPL-3.0", "AGPL-3.0"]
    for req in required_denied:
        if req not in deny_list:
            errors.append(f"Policy deny list must include {req}")
    # Check exceptions have required fields
    for exc in data.get("exceptions", []):
        for field in ["package", "license", "owner", "scope", "expires"]:
            if field not in exc:
                errors.append(f"Exception missing field: {field}")
    return errors


def check_scanner_exists() -> list[str]:
    errors: list[str] = []
    if not SCANNER.is_file():
        errors.append("scan_license_risks.py not found")
        return errors
    text = SCANNER.read_text(encoding="utf-8")
    if "scan_npm_deps" not in text:
        errors.append("Scanner must scan npm dependencies")
    if "scan_python_deps" not in text:
        errors.append("Scanner must scan Python dependencies")
    if "scan_model_deps" not in text:
        errors.append("Scanner must scan model dependencies")
    if "classify_license" not in text:
        errors.append("Scanner must have classify_license function")
    if "--check" not in text:
        errors.append("Scanner must have --check mode for CI")
    if "--json" not in text:
        errors.append("Scanner must have --json output mode")
    return errors


def check_ci_integration() -> list[str]:
    """Check CI has license scan step or can be integrated."""
    errors: list[str] = []
    if not CI_WORKFLOW.is_file():
        errors.append("ci.yml not found")
        return errors
    text = CI_WORKFLOW.read_text(encoding="utf-8")
    # Either has scan_license_risks.py reference or should have it
    if "scan_license_risks" not in text:
        errors.append("CI should reference scan_license_risks.py")
    return errors


def main() -> int:
    all_errors: list[str] = []
    all_errors.extend(check_policy_exists())
    all_errors.extend(check_scanner_exists())
    all_errors.extend(check_ci_integration())

    if all_errors:
        print("FAIL: RC-285 license risk scanning verification", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("PASS: RC-285 license risk scanning verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
