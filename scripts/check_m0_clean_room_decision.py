#!/usr/bin/env python3
"""RC ID: RC-030. Validate the pending M0 clean-room decision record."""

from __future__ import annotations

import sys
from pathlib import Path

DECISION_PATH = Path(__file__).resolve().parents[1] / "docs/legal/claude-source-map-clean-room.md"
REQUIRED_MARKERS = (
    "RC IDs: RC-030",
    "`pending-human-approval`",
    "M0 状态：`blocked`",
    "## 事实依据",
    "## 风险",
    "## 临时允许范围",
    "## 明确禁止范围",
    "## 角色与审计",
    "## 待签署与批准字段",
    "## M0 触发条件",
    "技术负责人：待人工填写",
    "合规负责人：待人工填写",
    "决策编号：待人工填写",
)


def main() -> int:
    if not DECISION_PATH.is_file():
        print(f"ERROR: missing M0 decision record: {DECISION_PATH.as_posix()}", file=sys.stderr)
        return 1
    content = DECISION_PATH.read_text(encoding="utf-8")
    missing = [marker for marker in REQUIRED_MARKERS if marker not in content]
    if missing:
        for marker in missing:
            print(f"ERROR: missing M0 decision marker: {marker}", file=sys.stderr)
        return 1
    print("M0 clean-room decision record validated: pending approval and blocked by design.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
