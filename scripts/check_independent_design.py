#!/usr/bin/env python3
"""RC ID: RC-026. Validate an independent design record and provenance."""

from __future__ import annotations

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ADR_PATH = REPOSITORY_ROOT / "docs/adr/0005-independent-agent-event-design.md"
REQUIRED_MARKERS = (
    "RC IDs: RC-026",
    "## 方案 A",
    "## 方案 B",
    "## 决策",
    "## Provenance",
    "docs/research/clean-room-specs/example-agent-event.md",
    "docs/research/codex-source-register.yml",
    "docs/research/opencode-research-register.yml",
    "docs/research/claude-agent-sdk-neutral-spec.md",
    "不引入第三方代码",
)
FORBIDDEN_MARKERS = ("sourcesContent", "claude-code-sourcemap", "source-map 还原源码正文")


def main() -> int:
    if not ADR_PATH.is_file():
        print(f"ERROR: missing independent design ADR: {ADR_PATH.as_posix()}", file=sys.stderr)
        return 1
    content = ADR_PATH.read_text(encoding="utf-8")
    errors = [f"missing ADR marker: {marker}" for marker in REQUIRED_MARKERS if marker not in content]
    errors.extend(f"forbidden copied-material marker: {marker}" for marker in FORBIDDEN_MARKERS if marker in content)
    for relative in (
        "docs/research/clean-room-specs/example-agent-event.md",
        "docs/research/codex-source-register.yml",
        "docs/research/opencode-research-register.yml",
        "docs/research/claude-agent-sdk-neutral-spec.md",
    ):
        if not (REPOSITORY_ROOT / relative).is_file():
            errors.append(f"missing provenance source record: {relative}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Independent design passed: two alternatives, provenance, and no copied-material markers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
