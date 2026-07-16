#!/usr/bin/env python3
"""RC ID: RC-029. Validate and optionally run the quarterly authorization monitor."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = REPOSITORY_ROOT / "docs/research/anthropic-authorization-monitor.yml"
REVIEW_LOG = REPOSITORY_ROOT / "docs/research/anthropic-authorization-review-log.md"


def load_register() -> dict:
    payload = yaml.safe_load(REGISTER_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1 or payload.get("rc_id") != "RC-029":
        raise ValueError("invalid RC-029 monitor register")
    if not REVIEW_LOG.is_file():
        raise ValueError("missing RC-029 review log")
    return payload


def validate_static(payload: dict) -> list[str]:
    errors: list[str] = []
    sources = payload.get("sources")
    if not isinstance(sources, list) or len(sources) != 2:
        errors.append("monitor must contain two Anthropic sources")
    for source in sources or []:
        if source.get("on_change") != "create-adr-and-keep-restrictions":
            errors.append(f"invalid on_change policy for {source.get('id')}")
        if not source.get("repo") or not source.get("baseline_head_sha"):
            errors.append(f"missing baseline for {source.get('id')}")
    for url in payload.get("watch_urls", []):
        if url.get("status") != "pending-confirmation":
            errors.append(f"unverified URL must remain pending: {url.get('id')}")
        if url.get("on_change") != "create-adr-and-keep-restrictions":
            errors.append(f"invalid URL change policy for {url.get('id')}")
    if payload.get("default_policy") != "keep-restrictions-until-reviewed":
        errors.append("default policy must keep restrictions until reviewed")
    if payload.get("monitor_interval") != "quarterly":
        errors.append("monitor interval must be quarterly")
    return errors


def fetch_repo(repo: str) -> dict:
    request = Request(
        f"https://api.github.com/repos/{repo}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "rabbit-code-research"},
    )
    with urlopen(request, timeout=20) as response:
        result = json.load(response)
    branch = result.get("default_branch")
    commit_request = Request(
        f"https://api.github.com/repos/{repo}/commits/{branch}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "rabbit-code-research"},
    )
    with urlopen(commit_request, timeout=20) as response:
        result["_head_sha"] = json.load(response).get("sha")
    return result


def run_live(payload: dict) -> int:
    changes: list[str] = []
    for source in payload["sources"]:
        try:
            current = fetch_repo(source["repo"])
        except Exception as exc:  # noqa: BLE001 - monitor must report external failures
            print(f"PENDING CONFIRMATION: cannot query {source['repo']}: {exc}")
            continue
        observed = {
            "default_branch": current.get("default_branch"),
            "head_sha": current.get("_head_sha"),
            "license_spdx": (current.get("license") or {}).get("spdx_id"),
            "archived": current.get("archived"),
            "disabled": current.get("disabled"),
        }
        expected = {
            "default_branch": source["baseline_default_branch"],
            "head_sha": source["baseline_head_sha"],
            "license_spdx": source["baseline_license_spdx"],
            "archived": source["baseline_archived"],
            "disabled": source["baseline_disabled"],
        }
        for field, value in expected.items():
            if observed[field] != value:
                changes.append(f"{source['repo']} {field}: expected {value!r}, observed {observed[field]!r}")
        if current.get("html_url") is None:
            changes.append(f"{source['repo']} missing html_url")
        print(f"Observed {source['repo']}: {json.dumps(observed, ensure_ascii=False)}")
    if changes:
        for change in changes:
            print(f"CHANGE DETECTED: {change}", file=sys.stderr)
        return 1
    print("Anthropic authorization monitor passed: no metadata changes detected.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="query current GitHub repository metadata")
    args = parser.parse_args()
    try:
        payload = load_register()
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: invalid RC-029 monitor: {exc}", file=sys.stderr)
        return 1
    errors = validate_static(payload)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if args.live:
        return run_live(payload)
    print("Validated quarterly Anthropic authorization monitor register.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
