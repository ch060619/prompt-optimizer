#!/usr/bin/env python3
"""RC ID: RC-042. Validate complete feature state acceptance coverage."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = REPOSITORY_ROOT / "docs/product/state-acceptance.yml"
DOCUMENT_PATH = REPOSITORY_ROOT / "docs/product/state-acceptance.md"
CAPABILITY_PATH = REPOSITORY_ROOT / "docs/product/capability-matrix.yml"
REQUIRED_STATES = {
    "success",
    "failure",
    "cancel",
    "retry",
    "degraded",
    "offline",
    "denied",
    "recovery",
}
NON_SUCCESS_STATES = REQUIRED_STATES - {"success"}
REQUIRED_REQUIREMENTS = {f"R{number}" for number in range(1, 7)}


def load_yaml(path: Path) -> object:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def main() -> int:
    try:
        payload = load_yaml(REGISTER_PATH)
        capability_payload = load_yaml(CAPABILITY_PATH)
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR: cannot read RC-042 state acceptance: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    if not isinstance(payload, dict) or not isinstance(capability_payload, dict):
        print("ERROR: RC-042 and RC-040 registers must be YAML mappings", file=sys.stderr)
        return 1
    if payload.get("schema_version") != 1 or payload.get("rc_id") != "RC-042":
        errors.append("invalid RC-042 state acceptance schema")
    if payload.get("status") != "defined-not-implementation-validated":
        errors.append("state acceptance status must disclose pending implementation validation")
    if not DOCUMENT_PATH.is_file():
        errors.append("missing human-readable RC-042 state acceptance document")

    state_contract = payload.get("state_contract", {})
    if set(state_contract) != REQUIRED_STATES:
        errors.append("state contract must contain exactly eight required states")
    error_codes = payload.get("error_codes", {})
    ui_copy = payload.get("ui_copy", {})
    for state, contract in state_contract.items():
        if not contract.get("label") or not contract.get("ui_copy_key"):
            errors.append(f"state contract is incomplete: {state}")
        copy_key = contract.get("ui_copy_key")
        if copy_key not in ui_copy or not ui_copy.get(copy_key):
            errors.append(f"missing UI copy for state: {state}")
        code = contract.get("error_code")
        if state == "success" and code is not None:
            errors.append("success must not use an error code")
        if state in NON_SUCCESS_STATES and code not in error_codes:
            errors.append(f"missing error code for state: {state}")

    capability_ids = {item.get("id") for item in capability_payload.get("capabilities", [])}
    features = payload.get("features", [])
    feature_map = {item.get("id"): item for item in features}
    if set(feature_map) != capability_ids:
        errors.append("state acceptance features must exactly match RC-040 capabilities")
    if len(features) != len(feature_map):
        errors.append("state acceptance feature IDs must be unique")

    for feature in features:
        feature_id = feature.get("id")
        if not feature.get("requirement_ids") or not set(feature.get("requirement_ids", [])).issubset(REQUIRED_REQUIREMENTS):
            errors.append(f"feature requirement mapping is incomplete: {feature_id}")
        if not feature.get("scenario_ids") or feature.get("critical") is not True:
            errors.append(f"feature needs scenarios and critical marker: {feature_id}")
        acceptance = feature.get("acceptance", {})
        if set(acceptance) != REQUIRED_STATES:
            errors.append(f"feature state coverage is incomplete: {feature_id}")
        for state, entry in acceptance.items():
            if not isinstance(entry, dict) or not entry.get("expected"):
                errors.append(f"feature state expectation is incomplete: {feature_id}/{state}")

    parameters = payload.get("test_parameters", [])
    parameter_map = {item.get("id"): item for item in parameters}
    if len(parameters) != len(parameter_map):
        errors.append("test parameter IDs must be unique")
    parameter_features: set[str] = set()
    for parameter in parameters:
        parameter_id = parameter.get("id")
        feature_id = parameter.get("feature_id")
        state = parameter.get("expected_state")
        parameter_features.add(feature_id)
        if feature_id not in feature_map:
            errors.append(f"test parameter references unknown feature: {parameter_id}")
        if parameter.get("branch") not in NON_SUCCESS_STATES or state not in NON_SUCCESS_STATES:
            errors.append(f"test parameter must exercise a non-success state: {parameter_id}")
        contract = state_contract.get(state, {})
        if parameter.get("expected_error_code") != contract.get("error_code"):
            errors.append(f"test parameter error code does not match state contract: {parameter_id}")
        if parameter.get("expected_ui_copy_key") != contract.get("ui_copy_key"):
            errors.append(f"test parameter UI copy does not match state contract: {parameter_id}")
        if not parameter.get("fixture"):
            errors.append(f"test parameter fixture is missing: {parameter_id}")
    if parameter_features != set(feature_map):
        errors.append("every critical feature needs at least one non-success test parameter")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Validated RC-042 state acceptance: 17 RC-040 capabilities, eight states, unified errors/UI copy, and non-success test parameters complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
