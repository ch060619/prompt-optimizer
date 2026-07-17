#!/usr/bin/env python3
"""RC ID: RC-036. Validate the research delivery summary and M0 gate."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = REPOSITORY_ROOT / "docs/research/rc036-research-delivery-summary.yml"
REQUIRED_FEATURES = {
    "codex",
    "opencode",
    "claude-code",
    "claude-agent-sdk",
    "local-models-and-runners",
    "rabbit-artwork",
}
REQUIRED_RULES = {
    "codex-desktop",
    "opencode-implementation",
    "claude-code-materials",
    "claude-cli",
    "source-map-content",
    "model-weights",
    "rabbit-artwork",
}


def main() -> int:
    try:
        payload = yaml.safe_load(REGISTER_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR: cannot read RC-036 summary: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    if payload.get("schema_version") != 1 or payload.get("rc_id") != "RC-036":
        errors.append("invalid RC-036 summary schema")
    if payload.get("status") != "submitted-pending-m0-review":
        errors.append("RC-036 must remain submitted-pending-m0-review until signed")

    features = payload.get("feature_comparison", [])
    feature_map = {item.get("id"): item for item in features}
    if set(feature_map) != REQUIRED_FEATURES:
        errors.append("feature comparison must cover exactly the six required source groups")
    for item in features:
        if not item.get("evidence") or not item.get("decision") or not item.get("reuse_boundary"):
            errors.append(f"feature row is incomplete: {item.get('id')}")
        for evidence_path in item.get("evidence", []):
            if not (REPOSITORY_ROOT / evidence_path).is_file():
                errors.append(f"missing feature evidence: {evidence_path}")

    rules = {item.get("id"): item for item in payload.get("non_reuse_rules", [])}
    if set(rules) != REQUIRED_RULES:
        errors.append("non-reuse list must cover all seven protected boundaries")
    for item in payload.get("non_reuse_rules", []):
        if not item.get("rule") or not item.get("evidence"):
            errors.append(f"non-reuse rule is incomplete: {item.get('id')}")
        elif not (REPOSITORY_ROOT / item["evidence"]).is_file():
            errors.append(f"missing non-reuse evidence: {item['evidence']}")

    for item in payload.get("adr_index", []):
        if not (REPOSITORY_ROOT / str(item.get("path", ""))).is_file():
            errors.append(f"missing ADR or decision record: {item.get('path')}")
    if payload.get("adr_index", []) == []:
        errors.append("ADR index must not be empty")

    review = payload.get("cross_module_review", {})
    if review.get("status") != "pending-human-m0-review" or review.get("m0_approved") is not False:
        errors.append("cross-module review must remain pending and M0 must remain unapproved")
    if not review.get("signoff") or not review.get("blockers"):
        errors.append("cross-module signoff and blockers must be recorded")
    issue_gate = review.get("architecture_issue_gate", {})
    if issue_gate.get("required") is not True or issue_gate.get("approval_status") != "blocked":
        errors.append("future architecture Issue gate must be required and blocked until approval")
    if not issue_gate.get("required_fields") or issue_gate.get("current_mapping") != []:
        errors.append("architecture Issue gate must define fields and record an empty current mapping")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Validated RC-036 research summary: evidence indexed, M0 review pending, Issue gate blocked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
