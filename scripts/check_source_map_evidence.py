#!/usr/bin/env python3
"""RC ID: RC-021. Validate source-map metadata-only evidence."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REGISTER_PATH = Path(__file__).resolve().parents[1] / "docs/research/source-map-evidence.yml"
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
EXPECTED = {
    "chinasiro-claude-code-sourcemap",
    "oboard-claude-code-rev",
    "ghuntley-claude-code-source-code-deobfuscation",
    "comeonoliver-claude-code-analysis",
    "dadiaomengmeimei-claude-code-sourcemap-learning-notebook",
}


def validate() -> list[str]:
    if not REGISTER_PATH.is_file():
        return [f"missing source-map evidence: {REGISTER_PATH.as_posix()}"]
    try:
        payload = yaml.safe_load(REGISTER_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [f"cannot read source-map evidence: {exc}"]

    errors: list[str] = []
    if payload.get("schema_version") != 1 or payload.get("rc_id") != "RC-021":
        errors.append("schema_version must be 1 and rc_id must be RC-021")
    policy = payload.get("policy")
    if not isinstance(policy, dict) or any(policy.get(key) is not False for key in ("source_body_accessed", "source_body_retained", "source_body_run")):
        errors.append("policy must prohibit source body access, retention, and execution")
    repositories = payload.get("repositories")
    ids = {item.get("id") for item in repositories or [] if isinstance(item, dict)}
    if ids != EXPECTED or len(repositories or []) != len(EXPECTED):
        errors.append(f"repositories must contain exactly {sorted(EXPECTED)}")
    for item in repositories or []:
        if not isinstance(item, dict):
            errors.append("each repository must be a mapping")
            continue
        prefix = item.get("id", "unknown")
        if not SHA_PATTERN.fullmatch(str(item.get("head_sha"))):
            errors.append(f"{prefix}.head_sha must be a 40-character lowercase SHA")
        if item.get("api_status") != 200 or item.get("commit_url_status") != 200 or item.get("readme_status") != 200:
            errors.append(f"{prefix} must have API, commit, and README status 200")
        if item.get("dmca_or_deletion_check") != "not-observed":
            errors.append(f"{prefix} must not claim DMCA/deletion status")
        if item.get("risk") != "high" or item.get("reuse") != "prohibited":
            errors.append(f"{prefix} must remain high risk and prohibited")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Validated metadata-only source-map evidence for {len(EXPECTED)} repositories.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
