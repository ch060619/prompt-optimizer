#!/usr/bin/env python3
"""RC ID: RC-024. Validate provenance policy and current product-input audit."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = REPOSITORY_ROOT / "docs/research/proprietary-content-policy.md"
PROVENANCE_TEMPLATE = REPOSITORY_ROOT / "docs/templates/provenance-template.md"
PULL_REQUEST_TEMPLATE = REPOSITORY_ROOT / ".github/pull_request_template.md"
REQUIRED_POLICY_MARKERS = (
    "RC IDs: RC-024",
    "System Prompt",
    "source-map 还原",
    "每个相关 PR 的 Provenance",
    "相似性人工复核",
)
REQUIRED_TEMPLATE_MARKERS = (
    "external sources",
    "license and notice review",
    "originality statement",
    "string scan",
    "similarity review",
)
FORBIDDEN_LITERALS = (
    "sourcesContent",
    "private_system_prompt",
    "INTERNAL_ENDPOINT",
    "claude-code-sourcemap",
    "claude-code-rev",
)
PRODUCT_PATHS = ("backend/src", "frontend/src", "scripts", ".github", "Dockerfile", "package.json")
EXCLUDED_FILES = {
    "scripts/check_proprietary_content_policy.py",
    "scripts/check_source_map_denylist.py",
    "scripts/test_source_map_denylist.py",
    "scripts/check_source_map_evidence.py",
    "scripts/check_clean_room_boundary.py",
    "scripts/check_independent_design.py",
}


def _tracked_paths() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", *PRODUCT_PATHS],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
    )
    return [
        REPOSITORY_ROOT / raw
        for raw in result.stdout.decode("utf-8").split("\0")
        if raw and raw not in EXCLUDED_FILES
    ]


def main() -> int:
    errors: list[str] = []
    policy = POLICY_PATH.read_text(encoding="utf-8") if POLICY_PATH.is_file() else ""
    if any(marker not in policy for marker in REQUIRED_POLICY_MARKERS):
        errors.append("proprietary-content policy is incomplete")
    for path in (PROVENANCE_TEMPLATE, PULL_REQUEST_TEMPLATE):
        content = path.read_text(encoding="utf-8").casefold() if path.is_file() else ""
        if any(marker not in content for marker in REQUIRED_TEMPLATE_MARKERS):
            errors.append(f"provenance template is incomplete: {path.as_posix()}")

    try:
        paths = _tracked_paths()
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: cannot enumerate product inputs: {exc}", file=sys.stderr)
        return 1
    hits: list[tuple[str, str]] = []
    for path in paths:
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for literal in FORBIDDEN_LITERALS:
            if literal in content:
                hits.append((path.as_posix(), literal))
    if hits:
        errors.extend(f"forbidden literal {literal!r} in {path}" for path, literal in hits)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Proprietary-content policy passed: {len(paths)} product inputs, zero forbidden literal hits.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
