#!/usr/bin/env python3
"""RC ID: RC-039. Validate core journey definitions and manual test cards."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = REPOSITORY_ROOT / "docs/product/core-scenarios.yml"
SCENARIO_DOC_PATH = REPOSITORY_ROOT / "docs/product/core-scenarios.md"
REQUIRED_SCENARIOS = {
    "open-repository",
    "coding-task",
    "read-code",
    "plan-task",
    "edit-files",
    "run-command",
    "run-tests",
    "review-diff",
    "restore-session",
    "switch-model",
    "optimize-prompt",
    "offline-conversation",
}
REQUIRED_REQUIREMENTS = {f"R{number}" for number in range(1, 7)}


def main() -> int:
    try:
        payload = yaml.safe_load(REGISTER_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR: cannot read RC-039 scenarios: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    if payload.get("schema_version") != 1 or payload.get("rc_id") != "RC-039":
        errors.append("invalid RC-039 scenario schema")
    if payload.get("status") != "defined-not-e2e-validated":
        errors.append("scenario status must disclose that E2E validation is pending")
    if not SCENARIO_DOC_PATH.is_file():
        errors.append("missing human-readable RC-039 scenario document")

    coverage = payload.get("requirement_coverage", {})
    if set(coverage) != REQUIRED_REQUIREMENTS:
        errors.append("R1 through R6 coverage must each be declared")

    scenarios = payload.get("scenarios", [])
    scenario_map = {item.get("id"): item for item in scenarios}
    if set(scenario_map) != REQUIRED_SCENARIOS:
        errors.append("scenario set must contain the twelve required core journeys")

    cards: set[str] = set()
    covered_requirements: set[str] = set()
    for scenario in scenarios:
        scenario_id = scenario.get("id")
        covered_requirements.update(scenario.get("requirement_ids", []))
        if scenario.get("status") != "planned":
            errors.append(f"scenario must remain planned until implementation verification: {scenario_id}")
        if not scenario.get("preconditions") or len(scenario.get("main_flow", [])) < 3:
            errors.append(f"scenario needs preconditions and at least three main-flow steps: {scenario_id}")
        branches = scenario.get("failure_branches", [])
        if len(branches) < 2:
            errors.append(f"scenario needs at least two failure branches: {scenario_id}")
        for branch in branches:
            if not all(branch.get(field) for field in ("trigger", "expected", "recovery")):
                errors.append(f"failure branch is incomplete: {scenario_id}/{branch.get('id')}")

        dependencies = scenario.get("feature_dependencies", [])
        if not dependencies or any(not item.get("rc_ids") for item in dependencies):
            errors.append(f"scenario needs feature dependencies with RC IDs: {scenario_id}")

        verification = scenario.get("verification", {})
        card_id = verification.get("card_id")
        if verification.get("mode") != "manual-test-card" or not card_id:
            errors.append(f"scenario needs a manual test card: {scenario_id}")
        elif card_id in cards:
            errors.append(f"duplicate manual test card: {card_id}")
        else:
            cards.add(card_id)
        if len(verification.get("steps", [])) < 2 or not verification.get("pass_criteria"):
            errors.append(f"manual test card needs steps and pass criteria: {scenario_id}")

    if covered_requirements != REQUIRED_REQUIREMENTS:
        errors.append("scenario requirement IDs must cover all R1 through R6")
    for requirement_id, item in coverage.items():
        if not item.get("scenario_ids") or not item.get("rationale"):
            errors.append(f"requirement coverage is incomplete: {requirement_id}")
        missing = set(item.get("scenario_ids", [])) - REQUIRED_SCENARIOS
        if missing:
            errors.append(f"requirement coverage references unknown scenarios: {requirement_id}/{sorted(missing)}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Validated RC-039 scenarios: twelve journeys, R1-R6 coverage, failure branches, dependencies, and manual test cards present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
