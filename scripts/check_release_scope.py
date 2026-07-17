#!/usr/bin/env python3
"""RC ID: RC-041. Validate release scope and stable-version coverage."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REGISTER_PATH = REPOSITORY_ROOT / "docs/product/release-scope.yml"
DOCUMENT_PATH = REPOSITORY_ROOT / "docs/product/release-scope.md"
REQUIRED_REQUIREMENTS = {f"R{number}" for number in range(1, 7)}
REQUIRED_RC_IDS = set(range(1, 311))
REQUIRED_WAVES = {f"W{number}" for number in range(13)}
EXPECTED_CATEGORIES = {
    "项目前期准备",
    "开源调研",
    "架构设计",
    "核心功能开发",
    "GUI 设计",
    "提示词优化",
    "API 接入",
    "本地模型集成",
    "整合测试",
    "文档部署",
    "优化迭代",
    "开源发布",
}
RANGE_PATTERN = re.compile(r"^RC-(\d{3})\.\.RC-(\d{3})$")
INDEFINITE_WORDS = ("indefinite", "永久后续", "无限期")


def expand_rc_ranges(values: object) -> set[int]:
    if not isinstance(values, list):
        return set()
    expanded: set[int] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        match = RANGE_PATTERN.fullmatch(value)
        if not match:
            continue
        start, end = (int(part) for part in match.groups())
        expanded.update(range(start, end + 1))
    return expanded


def contains_indefinite_text(value: object) -> bool:
    if isinstance(value, str):
        return any(word in value.lower() for word in INDEFINITE_WORDS)
    if isinstance(value, list):
        return any(contains_indefinite_text(item) for item in value)
    if isinstance(value, dict):
        return any(contains_indefinite_text(item) for item in value.values())
    return False


def main() -> int:
    try:
        payload = yaml.safe_load(REGISTER_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        print(f"ERROR: cannot read RC-041 release scope: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    if not isinstance(payload, dict):
        print("ERROR: RC-041 release scope must be a YAML mapping", file=sys.stderr)
        return 1
    if payload.get("schema_version") != 1 or payload.get("rc_id") != "RC-041":
        errors.append("invalid RC-041 release scope schema")
    if payload.get("status") != "defined-not-release-validated":
        errors.append("scope status must disclose that release validation is pending")
    if not DOCUMENT_PATH.is_file():
        errors.append("missing human-readable RC-041 release scope document")

    tracks = payload.get("release_tracks", {})
    mvp = tracks.get("mvp", {}) if isinstance(tracks, dict) else {}
    stable = tracks.get("first_stable", {}) if isinstance(tracks, dict) else {}
    if not mvp.get("capability_ids") or not mvp.get("entry_conditions") or not mvp.get("exit_conditions"):
        errors.append("MVP needs capabilities, entry conditions, and exit conditions")
    if set(mvp.get("requirement_ids", [])) - REQUIRED_REQUIREMENTS:
        errors.append("MVP references unknown requirements")
    if set(mvp.get("requirement_ids", [])) - set(stable.get("requirement_ids", [])):
        errors.append("MVP requirements must remain inside the stable requirement set")

    if stable.get("status") != "required":
        errors.append("first stable track must be required")
    if set(stable.get("requirement_ids", [])) != REQUIRED_REQUIREMENTS:
        errors.append("first stable track must include exactly R1 through R6")
    if set(stable.get("wave_ids", [])) != REQUIRED_WAVES:
        errors.append("first stable track must include W0 through W12")
    stable_rc_ids = expand_rc_ranges(stable.get("rc_ranges"))
    if stable_rc_ids != REQUIRED_RC_IDS:
        errors.append("first stable track must cover every RC-001 through RC-310 exactly")
    if set(stable.get("plan_categories", [])) != EXPECTED_CATEGORIES:
        errors.append("first stable track must retain all original twelve plan categories")
    if len(stable.get("release_gates", [])) < 6:
        errors.append("first stable track needs release gates for R1 through R6 and publishing")

    requirements = payload.get("requirements", {})
    if set(requirements) != REQUIRED_REQUIREMENTS:
        errors.append("requirement register must contain exactly R1 through R6")
    for requirement_id, item in requirements.items():
        if item.get("stable") is not True:
            errors.append(f"requirement must be stable: {requirement_id}")
        if not item.get("acceptance") or not item.get("dependency_waves"):
            errors.append(f"requirement acceptance/dependencies are incomplete: {requirement_id}")
        if not set(item.get("dependency_waves", [])).issubset(REQUIRED_WAVES):
            errors.append(f"requirement references unknown dependency wave: {requirement_id}")

    deferred = payload.get("deferred_items", [])
    deferred_ids: set[str] = set()
    if not deferred:
        errors.append("at least one explicit post-stable enhancement boundary is required")
    for item in deferred:
        item_id = item.get("id")
        if not item_id or item_id in deferred_ids:
            errors.append(f"deferred item ID is missing or duplicated: {item_id}")
        deferred_ids.add(item_id)
        if item.get("status") != "deferred-post-stable":
            errors.append(f"deferred item must be explicitly post-stable: {item_id}")
        if set(item.get("requirement_ids", [])) & REQUIRED_REQUIREMENTS:
            errors.append(f"deferred item cannot move an original requirement out of stable: {item_id}")
        if item.get("rc_ids"):
            errors.append(f"deferred item cannot defer current RC tasks: {item_id}")
        if not item.get("rationale") or not item.get("entry_conditions") or not item.get("review_trigger"):
            errors.append(f"deferred item needs rationale, entry conditions, and review trigger: {item_id}")

    if contains_indefinite_text(payload):
        errors.append("release scope contains an indefinite/postponed-forever marker")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Validated RC-041 scope: MVP, required stable coverage for R1-R6/RC-001..RC-310, twelve plan categories, and explicit post-stable entry conditions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
