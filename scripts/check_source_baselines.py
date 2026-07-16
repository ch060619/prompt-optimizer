#!/usr/bin/env python3
"""RC ID: RC-015. Validate immutable GitHub source baseline metadata."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = REPOSITORY_ROOT / "docs/research/source-baselines.yml"
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
CATEGORIES = {"open-source", "behavior-only", "research-only"}


def _is_github_repository_url(value: object, repository: str) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return (
        parsed.scheme == "https"
        and parsed.netloc == "github.com"
        and parsed.path.strip("/") == repository
        and not parsed.query
        and not parsed.fragment
    )


def _is_timestamp(value: object) -> bool:
    return isinstance(value, str) and bool(TIMESTAMP_PATTERN.fullmatch(value))


def validate(path: Path) -> list[str]:
    if not path.is_file():
        return [f"missing source baseline: {path.as_posix()}"]

    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [f"cannot read source baseline: {exc}"]

    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["source baseline must be a YAML mapping"]
    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if payload.get("rc_id") != "RC-015":
        errors.append("rc_id must be RC-015")
    captured_at = payload.get("captured_at")
    if not isinstance(captured_at, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", captured_at):
        errors.append("captured_at must be YYYY-MM-DD")

    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        return errors + ["sources must be a non-empty list"]

    seen_ids: set[str] = set()
    seen_repositories: set[str] = set()
    for index, source in enumerate(sources, start=1):
        prefix = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{prefix} must be a mapping")
            continue
        source_id = source.get("id")
        repository = source.get("repo")
        if not isinstance(source_id, str) or not source_id:
            errors.append(f"{prefix}.id must be non-empty")
        elif source_id in seen_ids:
            errors.append(f"duplicate source id: {source_id}")
        else:
            seen_ids.add(source_id)
        if not isinstance(repository, str) or repository.count("/") != 1:
            errors.append(f"{prefix}.repo must be owner/name")
        elif repository in seen_repositories:
            errors.append(f"duplicate repository: {repository}")
        else:
            seen_repositories.add(repository)

        if not _is_github_repository_url(source.get("url"), repository or ""):
            errors.append(f"{prefix}.url must be the canonical GitHub URL")
        branch = source.get("default_branch")
        if not isinstance(branch, str) or not branch:
            errors.append(f"{prefix}.default_branch must be non-empty")
        sha = source.get("head_sha")
        if not isinstance(sha, str) or not SHA_PATTERN.fullmatch(sha):
            errors.append(f"{prefix}.head_sha must be a 40-character lowercase SHA")
        commit_url = source.get("commit_url")
        expected_commit_url = f"https://github.com/{repository}/commit/{sha}"
        if commit_url != expected_commit_url:
            errors.append(f"{prefix}.commit_url must point to head_sha")
        if source.get("observed_at") != captured_at:
            errors.append(f"{prefix}.observed_at must equal captured_at")
        for field in ("last_updated", "last_pushed"):
            if not _is_timestamp(source.get(field)):
                errors.append(f"{prefix}.{field} must be an ISO-8601 UTC timestamp")
        license_info = source.get("license")
        if not isinstance(license_info, dict) or "spdx" not in license_info or "name" not in license_info:
            errors.append(f"{prefix}.license must include spdx and name, including null values")
        for field in ("archived", "disabled"):
            if not isinstance(source.get(field), bool):
                errors.append(f"{prefix}.{field} must be boolean")
        if source.get("category") not in CATEGORIES:
            errors.append(f"{prefix}.category must be one of {sorted(CATEGORIES)}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate source baseline metadata")
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    errors = validate(args.path.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    payload = yaml.safe_load(args.path.read_text(encoding="utf-8"))
    print(f"Validated {len(payload['sources'])} source baselines captured on {payload['captured_at']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
