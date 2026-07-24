#!/usr/bin/env python3
"""RC ID: RC-284. Verify Codex/OpenCode attribution and modification declarations.

Checks:
    1. ADR-0003 exists and documents OpenCode research boundary
    2. OpenCode research register has fixed upstream commit and MIT license
    3. NOTICE file references OpenCode
    4. No product source files contain OpenCode copyright without attribution
    5. Reuse policy is "concepts-only-no-upstream-code"
    6. THIRD_PARTY_NOTICES "Reused Source Code" section confirms no approved reuse
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADR_0003 = ROOT / "docs" / "adr" / "0003-opencode-research-boundary.md"
RESEARCH_REGISTER = ROOT / "docs" / "research" / "opencode-research-register.yml"
MODULE_MAP = ROOT / "docs" / "research" / "opencode-module-map.md"
NOTICE = ROOT / "NOTICE"
THIRD_PARTY_NOTICES = ROOT / "THIRD_PARTY_NOTICES.md"

# Product source paths to scan for unattributed OpenCode references
PRODUCT_PATHS = ["backend/src", "frontend/src"]
# Patterns that would indicate unattributed OpenCode code
OPENCODE_COPYRIGHT_PATTERNS = [
    "Copyright (c) anomalyco",
    "Copyright (c) OpenCode",
    "Licensed from OpenCode",
    "Based on OpenCode",
    "Derived from opencode",
]


def check_adr_0003() -> list[str]:
    errors: list[str] = []
    if not ADR_0003.is_file():
        errors.append("ADR-0003 (OpenCode research boundary) not found")
        return errors
    text = ADR_0003.read_text(encoding="utf-8")
    if "MIT" not in text:
        errors.append("ADR-0003 must reference MIT license")
    if "no upstream code" not in text.lower() and "concepts-only" not in text.lower():
        errors.append("ADR-0003 must state no upstream code is approved")
    if "NOTICE" not in text:
        errors.append("ADR-0003 must reference NOTICE obligations")
    return errors


def check_research_register() -> list[str]:
    errors: list[str] = []
    if not RESEARCH_REGISTER.is_file():
        errors.append("opencode-research-register.yml not found")
        return errors
    text = RESEARCH_REGISTER.read_text(encoding="utf-8")
    if "453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d" not in text:
        errors.append("Research register must have fixed upstream commit SHA")
    if "MIT" not in text:
        errors.append("Research register must declare MIT license")
    if "concepts-only-no-upstream-code" not in text:
        errors.append("Research register must have concepts-only-no-upstream-code policy")
    if "anomalyco/opencode" not in text:
        errors.append("Research register must reference anomalyco/opencode repository")
    return errors


def check_module_map() -> list[str]:
    errors: list[str] = []
    if not MODULE_MAP.is_file():
        errors.append("opencode-module-map.md not found")
        return errors
    text = MODULE_MAP.read_text(encoding="utf-8")
    if "agent" not in text.lower():
        errors.append("Module map should reference agent module")
    if "cli" not in text.lower():
        errors.append("Module map should reference CLI module")
    return errors


def check_notice_references() -> list[str]:
    errors: list[str] = []
    if not NOTICE.is_file():
        errors.append("NOTICE file not found")
        return errors
    text = NOTICE.read_text(encoding="utf-8")
    if "OpenCode" not in text and "opencode" not in text.lower():
        errors.append("NOTICE file must reference OpenCode")
    if "ADR-0003" not in text:
        errors.append("NOTICE file must reference ADR-0003")
    return errors


def check_no_unattributed_opencode_code() -> list[str]:
    """Scan product source for unattributed OpenCode copyright/import patterns."""
    errors: list[str] = []
    for product_path in PRODUCT_PATHS:
        base = ROOT / product_path
        if not base.is_dir():
            continue
        for file_path in base.rglob("*"):
            if not file_path.is_file():
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            rel = file_path.relative_to(ROOT).as_posix()
            for pattern in OPENCODE_COPYRIGHT_PATTERNS:
                if pattern in content:
                    errors.append(f"Unattributed OpenCode reference '{pattern}' in {rel}")
    return errors


def check_third_party_reuse_section() -> list[str]:
    errors: list[str] = []
    if not THIRD_PARTY_NOTICES.is_file():
        errors.append("THIRD_PARTY_NOTICES.md not found")
        return errors
    text = THIRD_PARTY_NOTICES.read_text(encoding="utf-8")
    if "Reused Source Code" not in text:
        errors.append("THIRD_PARTY_NOTICES.md must have 'Reused Source Code' section")
    # Should confirm no approved reuse
    if "No third-party source code is approved" not in text:
        errors.append("THIRD_PARTY_NOTICES.md should confirm no approved third-party reuse")
    return errors


def main() -> int:
    all_errors: list[str] = []
    all_errors.extend(check_adr_0003())
    all_errors.extend(check_research_register())
    all_errors.extend(check_module_map())
    all_errors.extend(check_notice_references())
    all_errors.extend(check_no_unattributed_opencode_code())
    all_errors.extend(check_third_party_reuse_section())

    if all_errors:
        print("FAIL: RC-284 OpenCode attribution verification", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("PASS: RC-284 OpenCode attribution verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
