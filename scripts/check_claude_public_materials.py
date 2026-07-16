#!/usr/bin/env python3
"""RC ID: RC-019. Validate public-material and behavior-spec boundaries."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = REPOSITORY_ROOT / "docs/research/claude-code-public-materials.yml"
SHA = "c39cb0f14bfe8bb519bae5bfc55add6867c5e2ab"
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
EVIDENCE_CLASSES = {"document-fact", "black-box-observation", "speculation"}


def validate() -> list[str]:
    if not REGISTER_PATH.is_file():
        return [f"missing register: {REGISTER_PATH.as_posix()}"]
    try:
        payload = yaml.safe_load(REGISTER_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [f"cannot read register: {exc}"]

    errors: list[str] = []
    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if payload.get("rc_id") != "RC-019":
        errors.append("rc_id must be RC-019")
    source = payload.get("source")
    if not isinstance(source, dict):
        return errors + ["source must be a mapping"]
    if source.get("repo") != "anthropics/claude-code":
        errors.append("source.repo must be anthropics/claude-code")
    if source.get("head_sha") != SHA or not SHA_PATTERN.fullmatch(str(source.get("head_sha"))):
        errors.append("source.head_sha must be the pinned 40-character SHA")
    if source.get("license_spdx") is not None:
        errors.append("source.license_spdx must remain null")
    if source.get("category") != "behavior-only":
        errors.append("source.category must be behavior-only")
    if source.get("reuse_policy") != "no-core-code-no-commercial-materials":
        errors.append("source.reuse_policy must prohibit core code and commercial materials")

    materials = payload.get("materials")
    if not isinstance(materials, list) or not materials:
        errors.append("materials must be a non-empty list")
    for material in materials or []:
        if not isinstance(material, dict):
            errors.append("each material must be a mapping")
            continue
        if material.get("evidence_class") not in EVIDENCE_CLASSES:
            errors.append(f"invalid evidence class: {material.get('id')}")
        if material.get("access_status") not in {"verified-200", "verified-tree", "pending-confirmation-404"}:
            errors.append(f"invalid access status: {material.get('id')}")
        if material.get("access_status") == "pending-confirmation-404" and material.get("statement") is not None:
            errors.append(f"blocked material must not have a statement: {material.get('id')}")

    observations = payload.get("observations")
    statuses = {item.get("evidence_class"): item.get("status") for item in observations or []}
    if statuses.get("black-box-observation") != "not-run":
        errors.append("black-box observation must remain not-run")
    if statuses.get("speculation") != "not-approved":
        errors.append("speculation must remain not-approved")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Validated Claude Code public materials: document facts, pending links, and observation boundaries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
