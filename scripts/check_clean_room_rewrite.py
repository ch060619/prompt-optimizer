#!/usr/bin/env python3
"""RC ID: RC-033. Validate the clean-room rewrite workflow record."""

from __future__ import annotations

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
RECORD_PATH = REPOSITORY_ROOT / "docs/research/clean-room-rewrite-record.md"
REQUIRED_MARKERS = (
    "RC IDs: RC-033",
    "`pending-implementation-pr`",
    "## 输入规格",
    "## 独立候选方案",
    "## 实现与测试门禁",
    "受限材料访问：`false`",
    "生产实现：`not-started`",
    "docs/templates/clean-room-behavior-spec.md",
    "docs/adr/0005-independent-agent-event-design.md",
)
REQUIRED_FILES = (
    "docs/research/clean-room-specs/example-agent-event.md",
    "docs/templates/clean-room-behavior-spec.md",
    "docs/adr/0005-independent-agent-event-design.md",
    "scripts/check_clean_room_boundary.py",
)


def main() -> int:
    if not RECORD_PATH.is_file():
        print(f"ERROR: missing clean-room rewrite record: {RECORD_PATH.as_posix()}", file=sys.stderr)
        return 1
    content = RECORD_PATH.read_text(encoding="utf-8")
    errors = [f"missing marker: {marker}" for marker in REQUIRED_MARKERS if marker not in content]
    errors.extend(f"missing clean-room input: {path}" for path in REQUIRED_FILES if not (REPOSITORY_ROOT / path).is_file())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Clean-room rewrite workflow passed: pending implementation, restricted access false, independent inputs present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
