#!/usr/bin/env python3
"""RC ID: RC-037. Validate evidence-calibrated personas and scope coverage."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = REPOSITORY_ROOT / "docs/product/personas.yml"
REQUIRED_PERSONAS = {
    "individual-developer",
    "offline-user",
    "multi-provider-developer",
    "open-source-contributor",
    "team-maintainer",
}
REQUIRED_CAPABILITIES = {
    "repository-and-workspace",
    "agent-plan-edit-test-diff",
    "offline-prompt-optimization",
    "providers-and-models",
    "sessions-history-and-ownership",
    "provenance-license-and-release-gates",
}


def main() -> int:
    try:
        payload = yaml.safe_load(REGISTER_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR: cannot read RC-037 personas: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    if payload.get("schema_version") != 1 or payload.get("rc_id") != "RC-037":
        errors.append("invalid RC-037 persona schema")
    if payload.get("research_status") != "evidence-calibrated-not-interview-validated":
        errors.append("research status must disclose that interviews were not run")
    if payload.get("scope_review_status") != "pending-product-review":
        errors.append("scope review must remain pending-product-review")

    personas = payload.get("personas", [])
    persona_map = {item.get("id"): item for item in personas}
    if set(persona_map) != REQUIRED_PERSONAS:
        errors.append("persona set must contain the five required target groups")
    for persona in personas:
        if not persona.get("goals") or not persona.get("constraints"):
            errors.append(f"persona is missing goals or constraints: {persona.get('id')}")
        tasks = persona.get("high_frequency_tasks", [])
        if len(tasks) < 3:
            errors.append(f"persona needs at least three measurable tasks: {persona.get('id')}")
        for task in tasks:
            if task.get("priority") not in {"P0", "P1", "P2"} or not task.get("measure"):
                errors.append(f"task lacks priority or measure: {persona.get('id')}/{task.get('id')}")

    conflicts = payload.get("conflicts", [])
    if len(conflicts) < 4 or any(not item.get("tension") or not item.get("resolution_direction") for item in conflicts):
        errors.append("at least four conflicts with resolution directions are required")

    capabilities = {item.get("capability") for item in payload.get("core_capability_coverage", [])}
    if capabilities != REQUIRED_CAPABILITIES:
        errors.append("core capability coverage is incomplete")
    if not payload.get("evidence"):
        errors.append("evidence calibration sources must be recorded")
    else:
        for evidence_path in payload["evidence"]:
            if not (REPOSITORY_ROOT / evidence_path).is_file():
                errors.append(f"missing persona evidence: {evidence_path}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Validated RC-037 personas: five target groups, measurable tasks, conflicts, and capability coverage present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
