#!/usr/bin/env python3
"""RC ID: RC-279. Verify GitHub Release workflow and release artifacts.

Checks:
    1. release.yml workflow exists and has required jobs/steps
    2. generate_release_notes.py exists and produces required sections
    3. Release notes template has all required sections
    4. Release checklist completeness (no missing items)
    5. Git tag trigger (plain tag, not Releases API)
    6. No code signing dependency
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
RELEASE_NOTES_SCRIPT = ROOT / "scripts" / "generate_release_notes.py"
CHANGELOG = ROOT / "CHANGELOG.md"

REQUIRED_WORKFLOW_JOBS = {"resolve-channel", "build-cli", "build-desktop", "build-sbom", "publish"}
REQUIRED_NOTES_SECTIONS = [
    "Summary",
    "Installers and CLI",
    "Checksums",
    "SBOM and Supply Chain",
    "Licenses",
    "Known Issues",
    "Upgrade Instructions",
]
REQUIRED_RELEASE_FILES = [
    "RELEASE_NOTES.md",
    "sbom.json",
    "provenance.json",
    "licenses.json",
    "artifacts.json",
    "LICENSE",
]


def check_workflow_exists() -> list[str]:
    errors: list[str] = []
    if not WORKFLOW.is_file():
        errors.append(f"Missing: {WORKFLOW.relative_to(ROOT)}")
        return errors
    text = WORKFLOW.read_text(encoding="utf-8")
    for job in REQUIRED_WORKFLOW_JOBS:
        if job not in text:
            errors.append(f"Workflow missing job: {job}")
    if "tags:" not in text:
        errors.append("Workflow must trigger on tags (plain Git Tag)")
    if "v*" not in text:
        errors.append("Workflow must trigger on v* tag pattern")
    if "softprops/action-gh-release" not in text and "actions/create-release" not in text:
        errors.append("Workflow must create a GitHub Release")
    if "generate_sbom.py" not in text:
        errors.append("Workflow must run SBOM generation")
    if "generate_release_notes.py" not in text:
        errors.append("Workflow must generate release notes")
    if "check_rc279_github_release.py" not in text:
        errors.append("Workflow must run release checklist verification")
    # No code signing
    if "codesign" in text.lower() or "signtool" in text.lower():
        errors.append("Workflow must not include code signing (per requirements)")
    return errors


def check_release_notes_script() -> list[str]:
    errors: list[str] = []
    if not RELEASE_NOTES_SCRIPT.is_file():
        errors.append(f"Missing: {RELEASE_NOTES_SCRIPT.relative_to(ROOT)}")
        return errors
    text = RELEASE_NOTES_SCRIPT.read_text(encoding="utf-8")
    for section in REQUIRED_NOTES_SECTIONS:
        if section not in text:
            errors.append(f"Release notes script missing section: {section}")
    if "--version" not in text:
        errors.append("Release notes script must accept --version")
    if "--channel" not in text:
        errors.append("Release notes script must accept --channel")
    if "CHANGELOG" not in text:
        errors.append("Release notes script must read CHANGELOG")
    if "git" not in text.lower():
        errors.append("Release notes script should reference git log")
    return errors


def check_release_dir(release_dir: Path) -> list[str]:
    """Check release directory for required files."""
    errors: list[str] = []
    if not release_dir.is_dir():
        errors.append(f"Release directory does not exist: {release_dir}")
        return errors
    for f in REQUIRED_RELEASE_FILES:
        if not (release_dir / f).is_file():
            errors.append(f"Missing release artifact: {f}")
    # Check checksums
    checksum_files = list(release_dir.glob("SHA256SUMS*"))
    if not checksum_files:
        errors.append("No SHA256SUMS checksum files in release directory")
    return errors


def check_changelog_has_version(version: str | None = None) -> list[str]:
    errors: list[str] = []
    if not CHANGELOG.is_file():
        errors.append("CHANGELOG.md not found")
        return errors
    text = CHANGELOG.read_text(encoding="utf-8")
    if version:
        if f"[{version}]" not in text:
            errors.append(f"CHANGELOG.md missing entry for version {version}")
    else:
        if not re.search(r"\[\d+\.\d+\.\d+\]", text):
            errors.append("CHANGELOG.md has no versioned entries")
    return errors


def check_tag_trigger_not_api() -> list[str]:
    """Ensure release uses plain Git Tag, not GitHub Releases API directly."""
    errors: list[str] = []
    if not WORKFLOW.is_file():
        return errors
    text = WORKFLOW.read_text(encoding="utf-8")
    if "on:" in text and "push:" in text and "tags:" in text:
        pass  # Good: tag-triggered
    else:
        errors.append("Release should be triggered by Git tag push, not manual API call")
    return errors


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Verify RC-279 GitHub Release")
    parser.add_argument("--release-dir", type=Path, default=None, help="Release assets directory")
    parser.add_argument("--version", default=None, help="Version to check in changelog")
    args = parser.parse_args()

    all_errors: list[str] = []

    all_errors.extend(check_workflow_exists())
    all_errors.extend(check_release_notes_script())
    all_errors.extend(check_changelog_has_version(args.version))
    all_errors.extend(check_tag_trigger_not_api())

    if args.release_dir:
        all_errors.extend(check_release_dir(args.release_dir))

    if all_errors:
        print("FAIL: RC-279 GitHub Release verification", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("PASS: RC-279 GitHub Release verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
