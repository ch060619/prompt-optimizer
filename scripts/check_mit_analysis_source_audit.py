#!/usr/bin/env python3
"""RC ID: RC-028. Validate MIT analysis-source audit restrictions."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = REPOSITORY_ROOT / "docs/research/mit-analysis-source-audit.yml"
EXPECTED = {
    "comeonoliver-claude-code-analysis",
    "dadiaomengmeimei-claude-code-sourcemap-learning-notebook",
}


def main() -> int:
    try:
        payload = yaml.safe_load(REGISTER_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR: cannot read RC-028 audit: {exc}", file=sys.stderr)
        return 1
    errors: list[str] = []
    if payload.get("schema_version") != 1 or payload.get("rc_id") != "RC-028":
        errors.append("invalid RC-028 audit schema")
    policy = payload.get("policy", {})
    if any(policy.get(field) is not False for field in ("source_body_accessed", "source_body_retained", "implementation_reuse_approved")):
        errors.append("RC-028 policy must prohibit source-body access, retention, and implementation reuse")
    sources = payload.get("sources", [])
    ids = {source.get("id") for source in sources if isinstance(source, dict)}
    if ids != EXPECTED or len(sources) != len(EXPECTED):
        errors.append(f"RC-028 must contain exactly {sorted(EXPECTED)}")
    for source in sources:
        if source.get("license_status") != "verified-200" or source.get("license_spdx_metadata") != "MIT":
            errors.append(f"{source.get('id')} must retain verified MIT metadata")
        if source.get("readme_status") != "verified-200":
            errors.append(f"{source.get('id')} README must be verified")
        if source.get("content_decision") != "restricted":
            errors.append(f"{source.get('id')} must be restricted")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Validated RC-028 MIT analysis audit: 2 sources restricted, zero implementation approvals.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
