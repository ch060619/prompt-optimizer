#!/usr/bin/env python3
"""RC ID: RC-045. Validate RC schedule, ownership, dependencies, and buffers."""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = REPOSITORY_ROOT / "docs/planning/rc-045-delivery-plan.yml"
DOCUMENT_PATH = REPOSITORY_ROOT / "docs/planning/rc-045-delivery-plan.md"
REQUIRED_RC_IDS = set(range(1, 311))
RANGE_PATTERN = re.compile(r"^RC-(\d{3})\.\.?(?:RC-)?(\d{3})$")


def expand_ranges(values: object) -> set[int]:
    if not isinstance(values, list):
        return set()
    expanded: set[int] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        match = RANGE_PATTERN.fullmatch(value)
        if not match:
            continue
        start, end = (int(part) for part in match.groups())
        expanded.update(range(start, end + 1))
    return expanded


def parse_date(value: object) -> date | None:
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def contains_percentage(value: object) -> bool:
    if isinstance(value, str):
        return "%" in value or "百分比" in value or "percent" in value.lower()
    if isinstance(value, list):
        return any(contains_percentage(item) for item in value)
    if isinstance(value, dict):
        return any(contains_percentage(item) for item in value.values())
    return False


def main() -> int:
    try:
        payload = yaml.safe_load(PLAN_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR: cannot read RC-045 delivery plan: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    if not isinstance(payload, dict):
        print("ERROR: RC-045 delivery plan must be a YAML mapping", file=sys.stderr)
        return 1
    if payload.get("schema_version") != 1 or payload.get("rc_id") != "RC-045":
        errors.append("invalid RC-045 delivery plan schema")
    if payload.get("status") != "target-baseline-not-commitment":
        errors.append("schedule status must disclose that dates are targets, not commitments")
    if not DOCUMENT_PATH.is_file():
        errors.append("missing human-readable RC-045 delivery plan")
    baseline = payload.get("planning_baseline", {})
    for field in ("as_of", "execution_owner", "default_reviewer", "planning_unit", "capacity", "update_cadence", "completion_rule"):
        if not baseline.get(field):
            errors.append(f"planning baseline field is missing: {field}")
    if baseline.get("update_cadence") != "weekly":
        errors.append("schedule updates must be weekly")
    if contains_percentage(payload):
        errors.append("schedule must not use subjective percentage completion")

    packages = payload.get("work_packages", [])
    package_map = {item.get("id"): item for item in packages}
    if len(package_map) != len(packages) or len(packages) < 2:
        errors.append("work package IDs must be unique and the schedule must have multiple packages")
    assigned: set[int] = set()
    package_dates: dict[str, tuple[date, date]] = {}
    for package in packages:
        package_id = package.get("id")
        rc_ids = expand_ranges(package.get("rc_ranges"))
        if not rc_ids:
            errors.append(f"work package has no valid RC range: {package_id}")
        overlap = assigned & rc_ids
        if overlap:
            errors.append(f"RC ranges overlap in {package_id}: {sorted(overlap)[:3]}")
        assigned.update(rc_ids)
        if not isinstance(package.get("effort_days"), int) or package.get("effort_days") <= 0:
            errors.append(f"work package effort must be positive: {package_id}")
        if not isinstance(package.get("buffer_days"), int) or package.get("buffer_days") < 3:
            errors.append(f"work package needs at least three buffer days: {package_id}")
        start = parse_date(package.get("start"))
        target = parse_date(package.get("target"))
        if start is None or target is None or start > target:
            errors.append(f"work package dates are invalid: {package_id}")
        else:
            package_dates[package_id] = (start, target)
        for field in ("owner_role", "reviewer_role", "milestone", "acceptance"):
            if not package.get(field):
                errors.append(f"work package field is missing: {package_id}/{field}")
        dependencies = package.get("depends_on", [])
        if not isinstance(dependencies, list) or any(dependency not in package_map for dependency in dependencies):
            errors.append(f"work package has unknown dependency: {package_id}")
        if package_id in dependencies:
            errors.append(f"work package cannot depend on itself: {package_id}")

    if assigned != REQUIRED_RC_IDS:
        errors.append("RC ranges must cover every RC-001 through RC-310 exactly once")
    for package in packages:
        package_id = package.get("id")
        start_target = package_dates.get(package_id)
        if start_target is None:
            continue
        for dependency in package.get("depends_on", []):
            dependency_dates = package_dates.get(dependency)
            if dependency_dates and dependency_dates[1] >= start_target[0]:
                errors.append(f"dependency target must precede package start: {dependency} -> {package_id}")

    evidence = payload.get("weekly_evidence", {})
    required_fields = set(evidence.get("required_fields", []))
    if evidence.get("review_rule") is None or required_fields != {
        "completed_rc_ids",
        "commit_ids",
        "verification_commands",
        "blockers",
        "next_week_target",
    }:
        errors.append("weekly evidence must require completed IDs, commits, commands, blockers, and next target")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Validated RC-045 plan: RC-001..RC-310 assigned once with effort, buffers, dependencies, owners, reviewers, milestones, and weekly evidence fields.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
