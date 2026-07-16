#!/usr/bin/env python3
"""RC ID: RC-034. Validate name/channel audit without claiming legal clearance."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = REPOSITORY_ROOT / "docs/legal/product-name-channel-audit.yml"
REQUIRED_CHANNELS = {"github-repository-candidate", "pypi-candidate", "npm-candidate", "domain"}
REQUIRED_TRADEMARK_DATABASES = {"uspto", "euipo", "cnipa"}


def main() -> int:
    try:
        payload = yaml.safe_load(REGISTER_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR: cannot read RC-034 audit: {exc}", file=sys.stderr)
        return 1
    errors: list[str] = []
    if payload.get("schema_version") != 1 or payload.get("rc_id") != "RC-034":
        errors.append("invalid RC-034 audit schema")
    if payload.get("primary_name") != "Rabbit Code" or payload.get("distribution_identifier") != "rabbit-code":
        errors.append("primary name or distribution identifier is invalid")
    if payload.get("signoff", {}).get("status") != "pending-human-legal-review":
        errors.append("signoff must remain pending-human-legal-review")
    channels = payload.get("channels", [])
    channel_ids = {item.get("channel") for item in channels}
    if not REQUIRED_CHANNELS.issubset(channel_ids):
        errors.append(f"missing required channel classes: {sorted(REQUIRED_CHANNELS - channel_ids)}")
    for item in channels:
        risk = str(item.get("risk", ""))
        if item.get("observed_status") in {"404", 404} and not any(
            marker in risk for marker in ("not-found", "manual-store-search-required")
        ):
            errors.append(f"404 result must not claim availability: {item.get('identifier')}")
    trademark_databases = payload.get("trademark_databases", [])
    trademark_ids = {item.get("id") for item in trademark_databases}
    if not REQUIRED_TRADEMARK_DATABASES.issubset(trademark_ids):
        errors.append(f"missing required trademark databases: {sorted(REQUIRED_TRADEMARK_DATABASES - trademark_ids)}")
    for item in trademark_databases:
        if item.get("search_status") != "not-run":
            errors.append(f"trademark search must remain not-run until manually completed: {item.get('id')}")
    if not payload.get("backup_names"):
        errors.append("backup_names must be present")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Validated RC-034 name/channel audit: public checks recorded, legal clearance pending.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
