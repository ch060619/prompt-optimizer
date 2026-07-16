#!/usr/bin/env python3
"""RC ID: RC-020. Validate the SDK and bundled-CLI rights boundary."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = REPOSITORY_ROOT / "docs/research/claude-agent-sdk-research.yml"
SHA = "02782876a00afbcab584d501e8851b5109907077"
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
COMPONENTS = {
    "messages-and-query",
    "interactive-client",
    "custom-tools-and-mcp",
    "hooks",
    "permissions",
    "sessions-and-forking",
    "cli-transport",
    "official-documentation",
}


def validate() -> list[str]:
    if not REGISTER_PATH.is_file():
        return [f"missing register: {REGISTER_PATH.as_posix()}"]
    try:
        payload = yaml.safe_load(REGISTER_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [f"cannot read register: {exc}"]

    errors: list[str] = []
    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if payload.get("rc_id") != "RC-020":
        errors.append("rc_id must be RC-020")
    source = payload.get("source")
    if not isinstance(source, dict):
        return errors + ["source must be a mapping"]
    if source.get("repo") != "anthropics/claude-agent-sdk-python":
        errors.append("source.repo must be the Python SDK repository")
    if source.get("head_sha") != SHA or not SHA_PATTERN.fullmatch(str(source.get("head_sha"))):
        errors.append("source.head_sha must be the pinned 40-character SHA")
    if source.get("sdk_license") != "MIT":
        errors.append("source.sdk_license must be MIT")
    if source.get("bundled_cli_status") != "declared-by-readme":
        errors.append("bundled_cli_status must preserve the README declaration")
    if source.get("bundled_cli_rights") != "separate-and-not-approved-for-distribution":
        errors.append("bundled_cli_rights must remain separate and not approved")

    components = payload.get("components")
    names = {component.get("id") for component in components or [] if isinstance(component, dict)}
    if names != COMPONENTS or len(components or []) != len(COMPONENTS):
        errors.append(f"components must contain exactly {sorted(COMPONENTS)}")
    for component in components or []:
        if not isinstance(component, dict) or not isinstance(component.get("paths"), list):
            errors.append("each component must provide a paths list")
    rights = payload.get("rights_boundary")
    if not isinstance(rights, dict) or rights.get("bundled_cli") != "not-covered-by-sdk-license-assumption":
        errors.append("rights_boundary must keep the bundled CLI separate")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Validated Claude Agent SDK research boundary: {len(COMPONENTS)} components at {SHA}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
