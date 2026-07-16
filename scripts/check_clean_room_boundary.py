#!/usr/bin/env python3
"""RC ID: RC-025. Validate clean-room roles and neutral specification content."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = REPOSITORY_ROOT / "docs/legal/clean-room-role-register.yml"
SPEC_ROOT = REPOSITORY_ROOT / "docs/research/clean-room-specs"
REQUIRED_ROLES = {"researcher", "implementer", "reviewer"}
FORBIDDEN_SPEC_MARKERS = (
    "sourcesContent",
    "source-map",
    "system_prompt",
    "private prompt",
    "claude-code",
    "anthropic",
    "openai",
)
SOURCE_PATH_PATTERN = re.compile(r"(?:^|[/\\])(?:src|packages|plugins|examples)[/\\][^\s`]+")


def main() -> int:
    errors: list[str] = []
    try:
        payload = yaml.safe_load(REGISTER_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR: cannot read clean-room role register: {exc}", file=sys.stderr)
        return 1
    if payload.get("schema_version") != 1 or payload.get("rc_id") != "RC-025":
        errors.append("role register schema or RC ID is invalid")
    if payload.get("status") != "pending-human-signoff":
        errors.append("role register must remain pending-human-signoff")
    roles = {role.get("id") for role in payload.get("roles", []) if isinstance(role, dict)}
    if roles != REQUIRED_ROLES:
        errors.append(f"role register must contain exactly {sorted(REQUIRED_ROLES)}")
    signoffs = payload.get("signoffs")
    if not isinstance(signoffs, dict) or any(signoffs.get(role) != "pending-human-assignment" for role in REQUIRED_ROLES):
        errors.append("all role signoffs must remain pending-human-assignment")
    if not SPEC_ROOT.is_dir():
        errors.append("clean-room specification directory is missing")
    else:
        for path in SPEC_ROOT.rglob("*.md"):
            content = path.read_text(encoding="utf-8").casefold()
            for marker in FORBIDDEN_SPEC_MARKERS:
                if marker.casefold() in content:
                    errors.append(f"forbidden clean-room spec marker {marker!r} in {path.as_posix()}")
            if SOURCE_PATH_PATTERN.search(content):
                errors.append(f"source-like path in clean-room spec: {path.as_posix()}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Clean-room boundary passed: roles pending signoff and neutral specs contain no restricted markers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
