#!/usr/bin/env python3
"""RC ID: RC-040. Validate one CLI/GUI/headless capability contract matrix."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = REPOSITORY_ROOT / "docs/product/capability-matrix.yml"
DOCUMENT_PATH = REPOSITORY_ROOT / "docs/product/capability-matrix.md"
SURFACES = {"cli", "gui", "headless"}
SURFACE_STATUSES = {"shared-core", "not-applicable", "gui-only"}
REQUIRED_CAPABILITIES = {
    "workspace-discovery",
    "context-assembly",
    "agent-loop",
    "plan-edit-permission",
    "tool-and-approval",
    "terminal-process",
    "git-diff-checkpoint",
    "session-history-recovery",
    "task-progress-cancel",
    "provider-model",
    "prompt-optimization",
    "offline-local-model",
    "diagnostics",
    "export-audit",
    "window-management",
    "drag-drop",
    "system-notifications",
}
REQUIRED_EVENTS = {"agent-event-v1", "content-block-v1", "optimization-event-v1"}
REQUIRED_STORAGE = {
    "workspace-v1",
    "session-v1",
    "provider-v1",
    "prompt-optimization-v1",
    "settings-v1",
}


def main() -> int:
    try:
        payload = yaml.safe_load(REGISTER_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR: cannot read RC-040 matrix: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    if payload.get("schema_version") != 1 or payload.get("rc_id") != "RC-040":
        errors.append("invalid RC-040 capability matrix schema")
    if payload.get("status") != "defined-not-implementation-validated":
        errors.append("matrix status must disclose that implementation validation is pending")
    if not DOCUMENT_PATH.is_file():
        errors.append("missing human-readable RC-040 matrix document")

    surfaces = {item.get("id") for item in payload.get("surfaces", [])}
    if surfaces != SURFACES:
        errors.append("matrix must define exactly cli, gui, and headless surfaces")
    rules = payload.get("contract_rules", [])
    if len(rules) < 5 or any(not item.get("id") or not item.get("rule") for item in rules):
        errors.append("shared contract rules must include five complete rules")

    events = {item.get("id") for item in payload.get("shared_contracts", {}).get("event_schemas", [])}
    storage = {item.get("id") for item in payload.get("shared_contracts", {}).get("storage_schemas", [])}
    if not REQUIRED_EVENTS.issubset(events):
        errors.append("required shared event schemas are incomplete")
    if storage != REQUIRED_STORAGE:
        errors.append("storage schemas must contain exactly the five shared schemas")

    capabilities = payload.get("capabilities", [])
    capability_map = {item.get("id"): item for item in capabilities}
    if set(capability_map) != REQUIRED_CAPABILITIES:
        errors.append("capability set is incomplete or contains unknown capabilities")

    for capability in capabilities:
        capability_id = capability.get("id")
        surface_map = capability.get("surfaces", {})
        if set(surface_map) != SURFACES:
            errors.append(f"surface entries are incomplete: {capability_id}")
        gui_only = capability.get("surfaces", {}).get("gui", {}).get("status") == "gui-only"
        if (not capability.get("shared_contract") and not gui_only) or not capability.get("difference_reason"):
            errors.append(f"shared contract or difference reason is missing: {capability_id}")
        event_schema = capability.get("event_schema")
        storage_schema = capability.get("storage_schema")
        if event_schema is not None and event_schema not in events:
            errors.append(f"unknown event schema: {capability_id}/{event_schema}")
        if storage_schema is not None and storage_schema not in storage:
            errors.append(f"unknown storage schema: {capability_id}/{storage_schema}")
        for surface_id, surface in surface_map.items():
            if surface.get("status") not in SURFACE_STATUSES or not surface.get("behavior"):
                errors.append(f"surface status/behavior is incomplete: {capability_id}/{surface_id}")
        gui_only = surface_map.get("gui", {}).get("status") == "gui-only"
        if gui_only and not (surface_map.get("cli", {}).get("status") == "not-applicable" and surface_map.get("headless", {}).get("status") == "not-applicable"):
            errors.append(f"GUI-only capability must be not-applicable to CLI/headless: {capability_id}")
        if not capability.get("dependencies"):
            errors.append(f"capability dependencies are missing: {capability_id}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Validated RC-040 matrix: one shared contract set across CLI, GUI, and headless with explicit GUI-only differences.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
