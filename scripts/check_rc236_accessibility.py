#!/usr/bin/env python3
"""RC ID: RC-236. Check the repository accessibility test contract."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLE_PATH = ROOT / "frontend" / "src" / "styles.css"
TEST_PATH = ROOT / "frontend" / "tests" / "Rc236Accessibility.test.tsx"
REQUIRED_STYLE_MARKERS = (
    ":focus-visible",
    "@media (prefers-reduced-motion: reduce)",
    "@media (forced-colors: active)",
)


def main() -> int:
    errors: list[str] = []
    styles = STYLE_PATH.read_text(encoding="utf-8") if STYLE_PATH.is_file() else ""
    test = TEST_PATH.read_text(encoding="utf-8") if TEST_PATH.is_file() else ""
    if not STYLE_PATH.is_file():
        errors.append("missing frontend focus/reduced-motion stylesheet")
    if not TEST_PATH.is_file():
        errors.append("missing RC-236 axe test")
    errors.extend(f"missing style marker: {marker}" for marker in REQUIRED_STYLE_MARKERS if marker not in styles)
    for marker in ("axe.run", "aria-modal", "aria-describedby"):
        if marker not in test:
            errors.append(f"missing accessibility assertion: {marker}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("RC-236 accessibility contract present: axe, focus semantics, reduced motion, and forced colors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
