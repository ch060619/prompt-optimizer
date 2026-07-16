#!/usr/bin/env python3
"""RC ID: RC-017. Validate Codex source classification and reuse boundaries."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = REPOSITORY_ROOT / "docs/research/codex-source-register.yml"
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CATEGORIES = {"open-source", "public-doc", "behavior-only"}


def _https_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc) and not parsed.query and not parsed.fragment


def validate(path: Path) -> list[str]:
    if not path.is_file():
        return [f"missing Codex source register: {path.as_posix()}"]

    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [f"cannot read Codex source register: {exc}"]

    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["Codex source register must be a YAML mapping"]
    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if payload.get("rc_id") != "RC-017":
        errors.append("rc_id must be RC-017")
    if not isinstance(payload.get("captured_at"), str) or not DATE_PATTERN.fullmatch(payload["captured_at"]):
        errors.append("captured_at must be YYYY-MM-DD")

    categories = payload.get("categories")
    if set(categories or []) != CATEGORIES:
        errors.append(f"categories must be exactly {sorted(CATEGORIES)}")

    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        return errors + ["sources must be a non-empty list"]

    seen_ids: set[str] = set()
    seen_categories: set[str] = set()
    for index, source in enumerate(sources, start=1):
        prefix = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{prefix} must be a mapping")
            continue
        source_id = source.get("id")
        if not isinstance(source_id, str) or not source_id:
            errors.append(f"{prefix}.id must be non-empty")
        elif source_id in seen_ids:
            errors.append(f"duplicate source id: {source_id}")
        else:
            seen_ids.add(source_id)
        category = source.get("category")
        if category not in CATEGORIES:
            errors.append(f"{prefix}.category is invalid")
        else:
            seen_categories.add(category)

        if category == "open-source":
            if source.get("url") != "https://github.com/openai/codex/tree/78ba047bdae3db0342dee11d8d9ef5582fe8ce49":
                errors.append(f"{prefix}.url must be the pinned openai/codex tree URL")
            if not SHA_PATTERN.fullmatch(str(source.get("immutable_ref"))):
                errors.append(f"{prefix}.immutable_ref must be a 40-character lowercase SHA")
            if source.get("license") != "Apache-2.0":
                errors.append(f"{prefix}.license must be Apache-2.0")
            if source.get("access_status") != "verified":
                errors.append(f"{prefix}.access_status must be verified")
            if source.get("reuse_policy") != "license-review-required":
                errors.append(f"{prefix}.reuse_policy must require license review")
        elif category == "public-doc":
            if not _https_url(source.get("url")):
                errors.append(f"{prefix}.url must be an HTTPS URL")
            if source.get("access_status") not in {"verified", "blocked-403"}:
                errors.append(f"{prefix}.access_status must be verified or blocked-403")
            if source.get("reuse_policy") not in {"facts-only", "no-conclusions"}:
                errors.append(f"{prefix}.reuse_policy must limit use to facts or no conclusions")
        elif category == "behavior-only":
            if source.get("url") is not None or source.get("immutable_ref") is not None:
                errors.append(f"{prefix} behavior-only sources cannot claim an immutable source URL")
            if source.get("access_status") != "observation-boundary":
                errors.append(f"{prefix}.access_status must be observation-boundary")
            if source.get("reuse_policy") != "no-source-or-assets":
                errors.append(f"{prefix}.reuse_policy must prohibit source and asset reuse")
            if source.get("capture_artifact") != "none-retained":
                errors.append(f"{prefix}.capture_artifact must be none-retained")

    missing = CATEGORIES - seen_categories
    if missing:
        errors.append(f"missing source categories: {sorted(missing)}")
    return errors


def main() -> int:
    errors = validate(DEFAULT_PATH)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    payload = yaml.safe_load(DEFAULT_PATH.read_text(encoding="utf-8"))
    print(f"Validated {len(payload['sources'])} Codex source entries captured on {payload['captured_at']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
