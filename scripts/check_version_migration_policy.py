#!/usr/bin/env python3
"""RC ID: RC-044. Validate version and migration policy coverage."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = REPOSITORY_ROOT / "docs/migrations/version-migration-policy.yml"
ADR_PATH = REPOSITORY_ROOT / "docs/adr/0006-version-and-migration-policy.md"
REQUIRED_WINDOWS = {"api", "configuration", "database", "cli"}
REQUIRED_VERSIONS = {0, 1}


def main() -> int:
    try:
        payload = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
        adr = ADR_PATH.read_text(encoding="utf-8")
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR: cannot read RC-044 migration policy: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    if not isinstance(payload, dict):
        print("ERROR: RC-044 policy must be a YAML mapping", file=sys.stderr)
        return 1
    if payload.get("schema_version") != 1 or payload.get("rc_id") != "RC-044":
        errors.append("invalid RC-044 policy schema")
    if payload.get("status") != "accepted" or not ADR_PATH.is_file():
        errors.append("RC-044 needs an accepted ADR")
    for marker in ("RC-044", "Status: Accepted", "## Decision", "## Consequences"):
        if marker not in adr:
            errors.append(f"ADR is missing required decision marker: {marker}")

    semver = payload.get("semver", {})
    if set(semver) != {"major", "minor", "patch"} or any(not value for value in semver.values()):
        errors.append("SemVer major/minor/patch rules are incomplete")

    windows = payload.get("compatibility_windows", {})
    if set(windows) != REQUIRED_WINDOWS:
        errors.append("API, configuration, database, and CLI compatibility windows are required")
    for window_id, window in windows.items():
        if not all(window.get(field) for field in ("window", "deprecation")):
            errors.append(f"compatibility window/deprecation rule is incomplete: {window_id}")
    database = windows.get("database", {})
    if database.get("current_schema") != 1 or set(database.get("supported_source_versions", [])) != REQUIRED_VERSIONS:
        errors.append("database window must cover source/current schema versions 0 and 1")

    contract = payload.get("migration_contract", {})
    for section in ("preflight", "forward_migration", "rollback"):
        if len(contract.get(section, [])) < 2:
            errors.append(f"migration contract section is incomplete: {section}")
    if not contract.get("evidence_command"):
        errors.append("migration evidence command is missing")

    versions = payload.get("test_data_versions", [])
    version_ids = {item.get("id") for item in versions}
    schema_versions = {item.get("schema_version") for item in versions}
    if len(versions) < 2 or len(version_ids) != len(versions) or not REQUIRED_VERSIONS.issubset(schema_versions):
        errors.append("at least two distinct v0/v1 test data versions are required")
    for item in versions:
        records = item.get("records", {})
        if not item.get("purpose") or not records or any(value < 0 for value in records.values()):
            errors.append(f"test data version is incomplete: {item.get('id')}")
        if item.get("secret_fields"):
            errors.append(f"test data fixture must not contain secret fields: {item.get('id')}")

    rollback = payload.get("controlled_rollback", {})
    if not rollback.get("trigger") or len(rollback.get("steps", [])) < 3 or len(rollback.get("acceptance", [])) < 3:
        errors.append("controlled rollback needs trigger, steps, and acceptance criteria")
    if not rollback.get("evidence_command"):
        errors.append("controlled rollback evidence command is missing")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Validated RC-044 policy: SemVer, API/config/database/CLI windows, v0/v1 migration data, and controlled rollback criteria complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
