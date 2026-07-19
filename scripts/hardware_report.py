#!/usr/bin/env python3
"""RC ID: RC-186. Print a stable, best-effort local hardware report as JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from prompt_optimizer.hardware import HardwareDetector


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--override-json", help="JSON object of user-corrected field values")
    args = parser.parse_args()
    try:
        overrides = json.loads(args.override_json) if args.override_json else {}
    except json.JSONDecodeError as exc:
        parser.error(f"--override-json must be valid JSON: {exc.msg}")
    if not isinstance(overrides, dict):
        parser.error("--override-json must be a JSON object")
    print(HardwareDetector(root=args.root).detect(overrides).to_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
