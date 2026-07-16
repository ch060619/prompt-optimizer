#!/usr/bin/env python3
"""RC ID: RC-018. Validate the isolated OpenCode research register."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = REPOSITORY_ROOT / "docs/research/opencode-research-register.yml"
SHA = "453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d"
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
MODULES = {"agent", "cli", "tui", "desktop", "app", "server", "protocol", "llm", "plugin", "sdk", "ui"}


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
    if payload.get("rc_id") != "RC-018":
        errors.append("rc_id must be RC-018")
    source = payload.get("source")
    if not isinstance(source, dict):
        return errors + ["source must be a mapping"]
    if source.get("repo") != "anomalyco/opencode":
        errors.append("source.repo must be anomalyco/opencode")
    if source.get("default_branch") != "dev":
        errors.append("source.default_branch must be dev")
    if source.get("head_sha") != SHA or not SHA_PATTERN.fullmatch(str(source.get("head_sha"))):
        errors.append("source.head_sha must be the pinned 40-character SHA")
    if source.get("license") != "MIT":
        errors.append("source.license must be MIT")
    if source.get("reuse_policy") != "concepts-only-no-upstream-code":
        errors.append("source.reuse_policy must prohibit upstream code reuse")

    modules = payload.get("modules")
    names = {module.get("name") for module in modules or [] if isinstance(module, dict)}
    if names != MODULES or len(modules or []) != len(MODULES):
        errors.append(f"modules must contain exactly {sorted(MODULES)}")
    for module in modules or []:
        if not isinstance(module, dict):
            errors.append("each module must be a mapping")
            continue
        if module.get("decision") not in {"adopt-concept", "skip"}:
            errors.append(f"invalid decision for {module.get('name')}")
        if not isinstance(module.get("paths"), list) or not module["paths"]:
            errors.append(f"paths required for {module.get('name')}")

    prototype = payload.get("prototype")
    if not isinstance(prototype, dict) or prototype.get("reuses_upstream_code") is not False:
        errors.append("prototype must explicitly reject upstream code reuse")
    elif not (REPOSITORY_ROOT / prototype.get("path", "")).is_file():
        errors.append("prototype path must point to a repository file")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Validated OpenCode research register: {len(MODULES)} modules at {SHA}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
