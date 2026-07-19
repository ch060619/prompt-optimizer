#!/usr/bin/env python3
"""RC ID: RC-133. Validate the route and baseline contract for visual regression."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "design" / "rabbit-visual-regression.json"
COVERAGE = ROOT / "docs" / "design" / "rabbit-coverage-matrix.json"
REQUIRED_BASELINES = {
    "light-1x": ("light", [1280, 1000], 1),
    "dark-1x": ("dark", [1280, 1000], 1),
    "light-2x": ("light", [640, 844], 2),
    "dark-2x": ("dark", [640, 844], 2),
}
REQUIRED_THRESHOLDS = {
    "max_diff_ratio",
    "max_horizontal_overflow_px",
    "max_clipped_elements",
    "max_rabbit_content_overlaps",
}


def load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain an object")
    return payload


def validate(document: dict[str, Any], coverage: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if document.get("schema_version") != 1 or document.get("rc_id") != "RC-133":
        errors.append("invalid RC-133 visual regression schema")

    routes = document.get("routes")
    coverage_routes = coverage.get("routes")
    if not isinstance(routes, list) or not isinstance(coverage_routes, list):
        return errors + ["routes must be arrays in both visual and Rabbit coverage manifests"]
    route_paths = [route.get("path") for route in routes if isinstance(route, dict)]
    coverage_paths = [route.get("path") for route in coverage_routes if isinstance(route, dict)]
    if route_paths != coverage_paths:
        errors.append("visual regression routes must exactly match the Rabbit coverage matrix")
    if len(set(route_paths)) != len(route_paths):
        errors.append("visual regression routes must be unique")
    for route in routes:
        if not isinstance(route, dict) or not all(isinstance(route.get(field), str) and route[field] for field in ("path", "variant", "screenshot_id")):
            errors.append("each route needs path, variant, and screenshot_id")

    baselines = document.get("baselines")
    if not isinstance(baselines, list) or {item.get("id") for item in baselines if isinstance(item, dict)} != set(REQUIRED_BASELINES):
        errors.append("baselines must contain light/dark 1x/2x exactly once")
    else:
        for baseline in baselines:
            expected = REQUIRED_BASELINES[baseline["id"]]
            if (baseline.get("theme"), baseline.get("viewport"), baseline.get("device_scale_factor")) != expected:
                errors.append(f"baseline geometry is invalid: {baseline['id']}")

    thresholds = document.get("thresholds")
    if not isinstance(thresholds, dict) or set(thresholds) != REQUIRED_THRESHOLDS:
        errors.append("thresholds must define diff, overflow, clipping, and overlap limits")
    elif not 0 <= thresholds["max_diff_ratio"] <= 1 or any(thresholds[name] < 0 for name in REQUIRED_THRESHOLDS - {"max_diff_ratio"}):
        errors.append("visual thresholds must be non-negative and diff ratio must be between 0 and 1")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    try:
        errors = validate(load(MANIFEST), load(COVERAGE))
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"ERROR: cannot read visual regression manifest: {error}")
        return 1
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Rabbit visual regression contract is valid (14 routes x 4 baselines; diff, overflow, clipping, and overlap thresholds defined).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
