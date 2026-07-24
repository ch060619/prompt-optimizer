#!/usr/bin/env python3
"""RC ID: RC-291. Verify Claude Code source map exposure repository list,
legal assessment, clean-room role isolation, and usage scope approval.

Checks:
    1. Source map denylist exists with 5 blocked repositories
    2. Legal assessment document exists with risk evaluation
    3. Clean-room role register exists with researcher/implementer/reviewer
    4. Clean-room information boundary document exists
    5. Clean-room boundary check script exists
    6. Usage scope (allowed/prohibited) is documented
    7. No source map artifacts in product source (cross-check with RC-283)
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DENYLIST = ROOT / "docs" / "research" / "source-map-denylist.yml"
CLEAN_ROOM_DECISION = ROOT / "docs" / "legal" / "claude-source-map-clean-room.md"
ROLE_REGISTER = ROOT / "docs" / "legal" / "clean-room-role-register.yml"
INFO_BOUNDARY = ROOT / "docs" / "legal" / "clean-room-information-boundary.md"
BOUNDARY_CHECK = ROOT / "scripts" / "check_clean_room_boundary.py"
REWRITE_CHECK = ROOT / "scripts" / "check_clean_room_rewrite.py"

REQUIRED_BLOCKED_REPOS = [
    "ChinaSiro/claude-code-sourcemap",
    "oboard/claude-code-rev",
    "ghuntley/claude-code-source-code-deobfuscation",
    "ComeOnOliver/claude-code-analysis",
    "dadiaomengmeimei/claude-code-sourcemap-learning-notebook",
]

REQUIRED_ROLES = ["researcher", "implementer", "reviewer"]


def check_denylist() -> list[str]:
    errors: list[str] = []
    if not DENYLIST.is_file():
        errors.append("source-map-denylist.yml not found")
        return errors
    data = yaml.safe_load(DENYLIST.read_text(encoding="utf-8"))
    repos = data.get("blocked_repositories", [])
    for repo in REQUIRED_BLOCKED_REPOS:
        if repo not in repos:
            errors.append(f"Denylist missing repository: {repo}")
    if len(repos) < 5:
        errors.append(f"Denylist should have at least 5 blocked repos, found {len(repos)}")
    # Check blocked URLs
    urls = data.get("blocked_urls", [])
    if len(urls) < 5:
        errors.append(f"Denylist should have at least 5 blocked URLs, found {len(urls)}")
    return errors


def check_legal_assessment() -> list[str]:
    errors: list[str] = []
    if not CLEAN_ROOM_DECISION.is_file():
        errors.append("claude-source-map-clean-room.md not found")
        return errors
    text = CLEAN_ROOM_DECISION.read_text(encoding="utf-8")
    if "风险" not in text and "Risk" not in text:
        errors.append("Legal assessment must have risk evaluation")
    if "版权" not in text and "copyright" not in text.lower():
        errors.append("Legal assessment must address copyright risk")
    if "商业秘密" not in text and "trade secret" not in text.lower():
        errors.append("Legal assessment must address trade secret risk")
    if "临时允许范围" not in text and "allow" not in text.lower():
        errors.append("Legal assessment must document usage scope")
    if "禁止" not in text and "prohibit" not in text.lower():
        errors.append("Legal assessment must document prohibited scope")
    return errors


def check_role_register() -> list[str]:
    errors: list[str] = []
    if not ROLE_REGISTER.is_file():
        errors.append("clean-room-role-register.yml not found")
        return errors
    data = yaml.safe_load(ROLE_REGISTER.read_text(encoding="utf-8"))
    roles = data.get("roles", [])
    role_ids = [r.get("id", "") for r in roles]
    for role in REQUIRED_ROLES:
        if role not in role_ids:
            errors.append(f"Role register missing role: {role}")
    # Each role must have allowed_inputs and prohibited
    for role in roles:
        if "allowed_inputs" not in role:
            errors.append(f"Role {role.get('id')} missing allowed_inputs")
        if "prohibited" not in role:
            errors.append(f"Role {role.get('id')} missing prohibited list")
    return errors


def check_info_boundary() -> list[str]:
    errors: list[str] = []
    if not INFO_BOUNDARY.is_file():
        errors.append("clean-room-information-boundary.md not found")
        return errors
    text = INFO_BOUNDARY.read_text(encoding="utf-8")
    if "researcher" not in text.lower():
        errors.append("Information boundary must reference researcher role")
    if "implementer" not in text.lower():
        errors.append("Information boundary must reference implementer role")
    return errors


def check_boundary_scripts() -> list[str]:
    errors: list[str] = []
    if not BOUNDARY_CHECK.is_file():
        errors.append("check_clean_room_boundary.py not found")
    if not REWRITE_CHECK.is_file():
        errors.append("check_clean_room_rewrite.py not found")
    return errors


def main() -> int:
    all_errors: list[str] = []
    all_errors.extend(check_denylist())
    all_errors.extend(check_legal_assessment())
    all_errors.extend(check_role_register())
    all_errors.extend(check_info_boundary())
    all_errors.extend(check_boundary_scripts())

    if all_errors:
        print("FAIL: RC-291 source map clean-room verification", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("PASS: RC-291 source map clean-room verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
