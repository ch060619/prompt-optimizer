#!/usr/bin/env python3
"""RC ID: RC-288. Verify GitHub repository structure and setup.

Checks:
    1. github-repository-setup.md exists with required sections
    2. Repository structure documented
    3. Topics list defined
    4. Project board columns/labels documented
    5. Milestones defined
    6. Public roadmap exists
    7. README has required sections
    8. CHANGELOG exists (from RC-278)
    9. Release workflow exists (from RC-279)
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETUP_DOC = ROOT / "docs" / "github-repository-setup.md"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
CODEOWNERS = ROOT / ".github" / "CODEOWNERS"


def check_setup_doc() -> list[str]:
    errors: list[str] = []
    if not SETUP_DOC.is_file():
        errors.append("docs/github-repository-setup.md not found")
        return errors
    text = SETUP_DOC.read_text(encoding="utf-8")
    required_sections = [
        "Repository Topics",
        "Repository Structure",
        "Project Board",
        "Milestones",
        "Public Roadmap",
    ]
    for section in required_sections:
        if section not in text:
            errors.append(f"Setup doc missing section: {section}")
    # Check topics
    if "prompt-engineering" not in text:
        errors.append("Topics should include 'prompt-engineering'")
    if "offline-first" not in text:
        errors.append("Topics should include 'offline-first'")
    # Check milestones
    if "v3.0.0-stable" not in text:
        errors.append("Milestones should include v3.0.0-stable")
    # Check roadmap
    if "Completed" not in text or "Future" not in text:
        errors.append("Roadmap should have Completed and Future sections")
    return errors


def check_readme() -> list[str]:
    errors: list[str] = []
    if not README.is_file():
        errors.append("README.md not found")
        return errors
    text = README.read_text(encoding="utf-8")
    if "Rabbit Code" not in text:
        errors.append("README should mention Rabbit Code")
    if "安装" not in text and "Install" not in text:
        errors.append("README should have installation instructions")
    if "MIT" not in text:
        errors.append("README should mention MIT license")
    return errors


def check_changelog() -> list[str]:
    errors: list[str] = []
    if not CHANGELOG.is_file():
        errors.append("CHANGELOG.md not found")
        return errors
    text = CHANGELOG.read_text(encoding="utf-8")
    if "3.0.0" not in text:
        errors.append("CHANGELOG should have v3.0.0 entry")
    return errors


def check_workflows() -> list[str]:
    errors: list[str] = []
    if not RELEASE_WORKFLOW.is_file():
        errors.append("release.yml not found")
    if not CI_WORKFLOW.is_file():
        errors.append("ci.yml not found")
    return errors


def check_codeowners() -> list[str]:
    errors: list[str] = []
    if not CODEOWNERS.is_file():
        errors.append("CODEOWNERS not found")
    return errors


def main() -> int:
    all_errors: list[str] = []
    all_errors.extend(check_setup_doc())
    all_errors.extend(check_readme())
    all_errors.extend(check_changelog())
    all_errors.extend(check_workflows())
    all_errors.extend(check_codeowners())

    if all_errors:
        print("FAIL: RC-288 GitHub repository setup verification", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("PASS: RC-288 GitHub repository setup verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
