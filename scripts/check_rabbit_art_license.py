#!/usr/bin/env python3
"""RC ID: RC-035. Enforce the temporary rabbit-art release block."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = REPOSITORY_ROOT / "docs/legal/rabbit-art-license.yml"
EXPECTED_HASH = "1DDE71742091C82D85EDB403449AF8DE843D5F61DCA8CBF65B59AEBD9B90E599"


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
    if payload.get("status") != "pending-human-confirmation":
        errors.append("status must remain pending-human-confirmation until authorization is verified")

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
        errors.append("generation terms and human contribution review must remain pending")

    authorization = payload.get("authorization", {})
    permissions = authorization.get("permissions", {})
    if authorization.get("rights_holder") != "unknown" or authorization.get("license") != "unknown":
        errors.append("rights holder and license must remain unknown until evidence is supplied")
    if authorization.get("written_statement") is not None or authorization.get("evidence_path") is not None:
        errors.append("authorization evidence must not be invented")
    if any(value != "pending" for value in permissions.values()):
        errors.append("all material permissions must remain pending")

    release = payload.get("release", {})
    if release.get("allowed") is not False or release.get("status") != "blocked":
        errors.append("release must remain blocked until authorization is verified")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Validated RC-035 rabbit-art license register: authorization missing, release blocked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
