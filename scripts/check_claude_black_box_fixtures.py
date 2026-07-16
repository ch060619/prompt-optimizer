#!/usr/bin/env python3
"""RC ID: RC-027. Validate and optionally run self-generated black-box assertions."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPOSITORY_ROOT / "docs/research/black-box-fixtures/rc027-claude-cli-help.yml"


def load_fixture() -> dict:
    payload = yaml.safe_load(FIXTURE_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1 or payload.get("rc_id") != "RC-027":
        raise ValueError("invalid RC-027 fixture")
    assertions = payload.get("assertions")
    if not isinstance(assertions, list) or not assertions:
        raise ValueError("fixture assertions must be non-empty")
    for assertion in assertions:
        if not isinstance(assertion, dict) or not assertion.get("id") or not assertion.get("contains") or not assertion.get("abstract"):
            raise ValueError("each assertion needs id, contains, and abstract")
    if payload.get("raw_output_retained") is not False:
        raise ValueError("raw official output must not be retained")
    if len(payload.get("observed_output_sha256", "")) != 64:
        raise ValueError("observed_output_sha256 must be a SHA-256 value")
    return payload


def run_official(fixture: dict) -> int:
    executable = shutil.which("claude")
    if executable is None:
        print("PENDING CONFIRMATION: official Claude Code executable is not installed.")
        return 0
    version = subprocess.run(
        [executable, "--version"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.strip()
    output = subprocess.run(
        [executable, "--help"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout
    for assertion in fixture["assertions"]:
        if assertion["contains"] not in output:
            print(f"ERROR: missing official assertion {assertion['id']}", file=sys.stderr)
            return 1
    output_hash = hashlib.sha256(output.encode("utf-8")).hexdigest()
    print(f"Official black-box assertions passed for {version}; output sha256={output_hash}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-official", action="store_true")
    args = parser.parse_args()
    try:
        fixture = load_fixture()
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: invalid RC-027 fixture: {exc}", file=sys.stderr)
        return 1
    if args.run_official:
        return run_official(fixture)
    print(f"Validated RC-027 self-generated fixture: {len(fixture['assertions'])} abstract assertions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
