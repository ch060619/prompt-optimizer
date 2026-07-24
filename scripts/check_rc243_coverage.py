#!/usr/bin/env python3
"""RC ID: RC-243. Enforce coverage thresholds and critical-path test presence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "docs" / "testing" / "coverage-policy.yml"


def _path(value: str) -> Path:
    return ROOT / value


def _coverage_percent(report: dict[str, Any], path: str) -> float | None:
    file_report = report.get("files", {}).get(path.replace("/", "\\"))
    if file_report is None:
        file_report = report.get("files", {}).get(path)
    if not isinstance(file_report, dict):
        return None
    summary = file_report.get("summary")
    if not isinstance(summary, dict):
        return None
    value = summary.get("percent_covered")
    return float(value) if isinstance(value, int | float) else None


def validate(policy: dict[str, Any], report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if policy.get("schema_version") != 1 or policy.get("rc_id") != "RC-243":
        errors.append("invalid RC-243 coverage policy")
    thresholds = policy.get("thresholds", {})
    totals = report.get("totals", {})
    overall = totals.get("percent_covered")
    if not isinstance(overall, int | float):
        errors.append("coverage report has no total percentage")
    elif overall < float(thresholds.get("overall_percent", 0)):
        errors.append(f"overall coverage {overall:.2f}% is below policy")
    changed_values = [
        _coverage_percent(report, path)
        for path in policy.get("changed_files", [])
    ]
    if any(value is None for value in changed_values):
        errors.append("coverage report is missing a changed file")
    elif changed_values and min(changed_values) < float(thresholds.get("changed_files_percent", 0)):
        errors.append(f"changed-file coverage {min(changed_values):.2f}% is below policy")
    for category, paths in policy.get("critical_paths", {}).items():
        if not paths:
            errors.append(f"critical path has no tests: {category}")
        for path in paths:
            if not _path(path).is_file():
                errors.append(f"critical path test is missing: {path}")
    for path in policy.get("mutation_checks", []):
        if not _path(path).is_file():
            errors.append(f"mutation/fault check is missing: {path}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args(argv)
    del args
    try:
        policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
        report_path = _path(policy["report"])
        report = json.loads(report_path.read_text(encoding="utf-8"))
        errors = validate(policy, report)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"ERROR: cannot read RC-243 policy/report: {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        "RC-243 coverage gate passed: "
        f"overall {report['totals']['percent_covered']:.2f}%, "
        f"changed files >= {policy['thresholds']['changed_files_percent']:.2f}%, "
        f"critical paths {sum(len(paths) for paths in policy['critical_paths'].values())}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
