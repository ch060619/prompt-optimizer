#!/usr/bin/env python3
"""RC ID: RC-023. Block source-map artifacts from supply-chain inputs."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Iterable

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DENYLIST_PATH = REPOSITORY_ROOT / "docs/research/source-map-denylist.yml"


def load_denylist() -> dict[str, list[str]]:
    payload = yaml.safe_load(DENYLIST_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1 or payload.get("rc_id") != "RC-023":
        raise ValueError("invalid RC-023 source-map denylist")
    tokens: dict[str, list[str]] = {}
    for field in ("blocked_urls", "blocked_repositories", "blocked_artifact_names", "blocked_hashes"):
        values = payload.get(field)
        if not isinstance(values, list) or not values or not all(isinstance(value, str) for value in values):
            raise ValueError(f"{field} must be a non-empty string list")
        tokens[field] = values
    evidence_only_files = payload.get("evidence_only_files", [])
    if not isinstance(evidence_only_files, list) or not all(isinstance(value, str) for value in evidence_only_files):
        raise ValueError("evidence_only_files must be a string list")
    tokens["evidence_only_files"] = evidence_only_files
    return tokens


def scan_paths(paths: Iterable[Path], tokens: dict[str, list[str]]) -> list[tuple[str, str]]:
    hits: list[tuple[str, str]] = []
    blocked = [
        token
        for field, values in tokens.items()
        if field != "evidence_only_files"
        for token in values
    ]
    for path in paths:
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for token in blocked:
            if token in content:
                hits.append((path.as_posix(), token))
    return hits


def tracked_supply_chain_paths() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
    )
    excluded = {
        "docs/research/",
        "docs/evidence/",
        "docs/legal/",
        "docs/rabbit-code-310-detailed-execution.md",
        "docs/traceability/",
    }
    evidence_only_files = set(load_denylist()["evidence_only_files"])
    paths: list[Path] = []
    for raw_path in result.stdout.decode("utf-8").split("\0"):
        if (
            not raw_path
            or any(raw_path.startswith(prefix) for prefix in excluded)
            or raw_path in evidence_only_files
        ):
            continue
        paths.append(REPOSITORY_ROOT / raw_path)
    return paths


def main() -> int:
    try:
        tokens = load_denylist()
        paths = tracked_supply_chain_paths()
        hits = scan_paths(paths, tokens)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: denylist scan failed: {exc}", file=sys.stderr)
        return 1
    if hits:
        for path, token in hits:
            print(f"BLOCKED: {token} in {path}", file=sys.stderr)
        return 1
    print(f"Source-map denylist passed: {len(paths)} supply-chain inputs scanned, zero hits.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
