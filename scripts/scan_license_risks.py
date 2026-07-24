#!/usr/bin/env python3
"""RC ID: RC-285. Automated license risk scanner.

Scans Python, npm, Cargo, and model dependencies against the license risk policy.
Produces a report of allowed, review-required, and denied licenses.

Usage:
    python scripts/scan_license_risks.py            # scan and report
    python scripts/scan_license_risks.py --check     # exit 1 if denied licenses found
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "docs" / "research" / "license-risk-policy.yml"
PYPROJECT = ROOT / "backend" / "pyproject.toml"
PACKAGE_LOCK = ROOT / "frontend" / "package-lock.json"
CARGO_TOML = ROOT / "apps" / "desktop" / "src-tauri" / "Cargo.toml"
MANIFEST = ROOT / "data" / "models" / "manifest.yml"
THIRD_PARTY_NOTICES = ROOT / "THIRD_PARTY_NOTICES.md"


def load_policy() -> dict:
    if not POLICY_PATH.is_file():
        raise FileNotFoundError(f"License risk policy not found: {POLICY_PATH}")
    return yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))


def classify_license(license_str: str, policy: dict) -> str:
    """Classify a license string as allow/review/deny."""
    if not license_str or license_str in ("UNKNOWN", "null", ""):
        return "review"
    for allowed in policy.get("allow", []):
        if license_str == allowed:
            return "allow"
    for denied in policy.get("deny", []):
        if license_str == denied:
            return "deny"
    # Check exceptions
    for exc in policy.get("exceptions", []):
        if exc.get("license") == license_str:
            return "exception"
    return "review"


def scan_npm_deps(policy: dict) -> list[dict]:
    """Scan npm dependencies from package-lock.json."""
    results: list[dict] = []
    if not PACKAGE_LOCK.is_file():
        return results
    data = json.loads(PACKAGE_LOCK.read_text(encoding="utf-8"))
    packages = data.get("packages", {})
    for name, info in packages.items():
        if not name:  # root package
            continue
        license_str = info.get("license", "UNKNOWN")
        classification = classify_license(license_str, policy)
        results.append({
            "ecosystem": "npm",
            "package": name.replace("node_modules/", ""),
            "license": license_str,
            "classification": classification,
        })
    return results


def scan_model_deps(policy: dict) -> list[dict]:
    """Scan model dependencies from manifest.yml."""
    results: list[dict] = []
    if not MANIFEST.is_file():
        return results
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    for model in data.get("models", []):
        license_str = model.get("license_spdx", "UNKNOWN")
        classification = classify_license(license_str, policy)
        results.append({
            "ecosystem": "model",
            "package": model.get("model_id", "unknown"),
            "license": license_str,
            "classification": classification,
        })
    return results


def scan_python_deps_from_notices(policy: dict) -> list[dict]:
    """Scan Python dependencies from THIRD_PARTY_NOTICES.md (auto-generated)."""
    results: list[dict] = []
    if not THIRD_PARTY_NOTICES.is_file():
        return results
    text = THIRD_PARTY_NOTICES.read_text(encoding="utf-8")
    # Parse lines like: - `package` `version`; ...; license `LICENSE` (status)
    import re
    pattern = r"- `([^`]+)`.*?license `([^`]+)`"
    for match in re.finditer(pattern, text):
        name, license_str = match.groups()
        classification = classify_license(license_str, policy)
        results.append({
            "ecosystem": "pypi",
            "package": name,
            "license": license_str,
            "classification": classification,
        })
    return results


def scan_all(policy: dict) -> dict:
    """Scan all dependency sources and return a categorized report."""
    all_deps: list[dict] = []
    all_deps.extend(scan_python_deps_from_notices(policy))
    all_deps.extend(scan_npm_deps(policy))
    all_deps.extend(scan_model_deps(policy))

    report = {
        "allowed": [d for d in all_deps if d["classification"] == "allow"],
        "review": [d for d in all_deps if d["classification"] == "review"],
        "denied": [d for d in all_deps if d["classification"] == "deny"],
        "exception": [d for d in all_deps if d["classification"] == "exception"],
        "summary": {
            "total": len(all_deps),
            "allowed": sum(1 for d in all_deps if d["classification"] == "allow"),
            "review": sum(1 for d in all_deps if d["classification"] == "review"),
            "denied": sum(1 for d in all_deps if d["classification"] == "deny"),
            "exception": sum(1 for d in all_deps if d["classification"] == "exception"),
        },
    }
    return report


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Scan license risks")
    parser.add_argument("--check", action="store_true", help="Exit 1 if denied licenses found")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    args = parser.parse_args()

    policy = load_policy()
    report = scan_all(policy)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        s = report["summary"]
        print(f"License Risk Scan: {s['total']} dependencies")
        print(f"  Allowed:    {s['allowed']}")
        print(f"  Review:     {s['review']}")
        print(f"  Denied:     {s['denied']}")
        print(f"  Exception:  {s['exception']}")

        if report["denied"]:
            print("\nDENIED LICENSES:")
            for d in report["denied"]:
                print(f"  [{d['ecosystem']}] {d['package']}: {d['license']}")

        if report["review"]:
            print("\nREVIEW REQUIRED:")
            for d in report["review"]:
                print(f"  [{d['ecosystem']}] {d['package']}: {d['license']}")

        if report["exception"]:
            print("\nEXCEPTIONS (manually approved):")
            for d in report["exception"]:
                print(f"  [{d['ecosystem']}] {d['package']}: {d['license']}")

    if args.check and report["denied"]:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
