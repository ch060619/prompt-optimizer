#!/usr/bin/env python3
"""RC ID: RC-242. Validate the Windows/Linux CI matrix and required gates."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
REQUIRED_MARKERS = (
    "ubuntu-latest",
    "windows-latest",
    "python -m compileall -q backend/src",
    "ruff check backend",
    "mypy backend/src",
    "pytest backend/tests",
    "npm ci",
    "npm run lint",
    "npm test",
    "npm run build",
    "check_rabbit_art_license.py",
)


def main() -> int:
    errors: list[str] = []
    try:
        content = WORKFLOW.read_text(encoding="utf-8")
        document = yaml.safe_load(content)
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR: cannot read CI workflow: {exc}", file=sys.stderr)
        return 1
    if not isinstance(document, dict) or not isinstance(document.get("jobs"), dict):
        errors.append("CI workflow must define jobs")
    errors.extend(f"missing CI matrix marker: {marker}" for marker in REQUIRED_MARKERS if marker not in content)
    for job_name in ("backend", "frontend"):
        job = document.get("jobs", {}).get(job_name, {}) if isinstance(document, dict) else {}
        matrix = job.get("strategy", {}).get("matrix", {}) if isinstance(job, dict) else {}
        if set(matrix.get("os", [])) != {"ubuntu-latest", "windows-latest"}:
            errors.append(f"{job_name} must run on Ubuntu and Windows")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("RC-242 CI matrix valid: backend/frontend Windows+Linux jobs and required quality gates present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
