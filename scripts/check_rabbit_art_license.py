#!/usr/bin/env python3
"""RC ID: RC-035. Enforce the temporary rabbit-art release block."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = REPOSITORY_ROOT / "docs/legal/rabbit-art-license.yml"
EXPECTED_HASH = "2C7EDC4488B81533F116B2A908415FCF2063C2F6A51DCDF76E0C59014A057A38"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> int:
    try:
        payload = yaml.safe_load(REGISTER_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR: cannot read RC-035 license register: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    if payload.get("schema_version") != 1 or payload.get("rc_id") != "RC-035":
        errors.append("invalid RC-035 license register schema")
    if payload.get("status") != "user-authorized":
        errors.append("status must record the user's explicit release authorization")

    source = payload.get("source", {})
    if source.get("present_at_capture") is not True or source.get("observed_status") != "user-confirmed-identity":
        errors.append("the repository candidate must remain identified by the user")

    candidate = payload.get("repository_candidate", {})
    candidate_path = REPOSITORY_ROOT / str(candidate.get("path", ""))
    if candidate.get("path") != source.get("requested_path"):
        errors.append("source and repository candidate paths must identify the same asset")
    if not candidate_path.is_file():
        errors.append(f"repository candidate is missing: {candidate.get('path')}")
    else:
        observed_hash = file_sha256(candidate_path)
        if candidate.get("sha256") != EXPECTED_HASH or observed_hash != EXPECTED_HASH:
            errors.append("repository candidate hash does not match the fixed evidence")

    generation = payload.get("generation", {})
    if generation.get("creator_statement") != "user-stated-ai-generated":
        errors.append("the user's AI-generation statement must be recorded as a statement only")
    if generation.get("provider") != "unknown" or generation.get("terms_url") is not None:
        errors.append("generation provider and terms must remain unverified")
    if generation.get("terms_review") != "pending" or generation.get("human_contribution_review") != "pending":
        errors.append("unverified generation terms and human contribution review must remain pending")

    authorization = payload.get("authorization", {})
    permissions = authorization.get("permissions", {})
    if authorization.get("rights_holder") != "user-asserted":
        errors.append("rights holder must be recorded as user-asserted")
    if authorization.get("license") != "rabbit-code-project-release-permission":
        errors.append("license must remain scoped to the Rabbit Code project release")
    if authorization.get("written_statement") != "我允许发布了":
        errors.append("the user's release statement is missing")
    evidence_path = REPOSITORY_ROOT / str(authorization.get("evidence_path", ""))
    if not evidence_path.is_file():
        errors.append("release authorization evidence is missing")
    allowed_permissions = {
        "open_source_use": "allowed-for-rabbit-code",
        "modification": "allowed-for-rabbit-code",
        "derivative_works": "allowed-for-rabbit-code",
        "redistribution": "allowed-for-rabbit-code",
        "attribution": "not-required",
    }
    if any(permissions.get(key) != value for key, value in allowed_permissions.items()):
        errors.append("Rabbit Code release permissions do not match the user authorization")
    if permissions.get("commercial_use") != "pending":
        errors.append("general commercial use must remain pending unless separately authorized")

    release = payload.get("release", {})
    if release.get("allowed") is not True or release.get("status") != "approved-by-user":
        errors.append("Rabbit Code release must remain approved by the user")
    if release.get("block_reason") is not None:
        errors.append("approved release must not retain a block reason")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Validated RC-035 rabbit-art license register: user-authorized Rabbit Code release allowed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
