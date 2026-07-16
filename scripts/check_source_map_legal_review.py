#!/usr/bin/env python3
"""RC ID: RC-022. Ensure source-map legal review remains pending and restrictive."""

from __future__ import annotations

import sys
from pathlib import Path

REVIEW_PATH = Path(__file__).resolve().parents[1] / "docs/legal/claude-source-map-legal-review.md"
REQUIRED_MARKERS = (
    "RC IDs: RC-022",
    "`pending-human-legal-review`",
    "本文件不是法律意见",
    "禁止访问、运行、复制、机械改写或分发",
    "决策编号：待法律顾问填写",
)


def main() -> int:
    if not REVIEW_PATH.is_file():
        print(f"ERROR: missing legal review request: {REVIEW_PATH.as_posix()}", file=sys.stderr)
        return 1
    content = REVIEW_PATH.read_text(encoding="utf-8")
    missing = [marker for marker in REQUIRED_MARKERS if marker not in content]
    if missing:
        for marker in missing:
            print(f"ERROR: missing legal review guard: {marker}", file=sys.stderr)
        return 1
    print("Validated pending source-map legal review with restrictive interim rules.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
