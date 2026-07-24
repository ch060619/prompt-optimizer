#!/usr/bin/env python3
"""RC ID: RC-235. Check the committed visual regression matrix artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

from check_rabbit_visual_regression import COVERAGE, MANIFEST, load, validate

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = ROOT / "output" / "playwright"
ROUTE_SLUGS = {
    "/": "home",
    "/login": "login",
    "/register": "register",
    "/onboarding": "onboarding",
    "/workspace": "workspace",
    "/workspace/home": "workspace-home",
    "/workspace/task": "workspace-task",
    "/workspace/review": "workspace-review",
    "/workspace/terminal": "workspace-terminal",
    "/workspace/providers": "workspace-providers",
    "/workspace/models": "workspace-models",
    "/workspace/assets": "workspace-assets",
    "/workspace/settings": "workspace-settings",
    "/workspace/diagnostics": "workspace-diagnostics",
}
BASELINE_SUFFIXES = ("light-1x", "dark-1x", "light-2x", "dark-2x")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def main() -> int:
    errors = validate(load(MANIFEST), load(COVERAGE))
    routes = load(MANIFEST).get("routes", [])
    paths = [route.get("path") for route in routes if isinstance(route, dict)]
    if set(paths) != set(ROUTE_SLUGS):
        errors.append("visual matrix route set does not contain all 14 expected paths")

    for path in paths:
        slug = ROUTE_SLUGS.get(path)
        if slug is None:
            continue
        for suffix in BASELINE_SUFFIXES:
            artifact = SCREENSHOTS / f"rc-133-{slug}-{suffix}.png"
            if not artifact.is_file():
                errors.append(f"missing screenshot artifact: {artifact.relative_to(ROOT)}")
            elif artifact.read_bytes()[:8] != PNG_SIGNATURE:
                errors.append(f"invalid PNG screenshot artifact: {artifact.relative_to(ROOT)}")

    state_artifacts = (
        "rc234-onboarding.png",
        "rc234-workspace-home.png",
        "rc234-send-after-adopt.png",
    )
    for name in state_artifacts:
        artifact = SCREENSHOTS / name
        if not artifact.is_file() or artifact.read_bytes()[:8] != PNG_SIGNATURE:
            errors.append(f"missing or invalid workflow screenshot: {artifact.relative_to(ROOT)}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("RC-235 visual matrix valid: 14 routes, 4 PNG baselines, and workflow state captures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
