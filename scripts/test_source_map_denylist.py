#!/usr/bin/env python3
"""RC ID: RC-023. Verify an injected denylist URL fails the scanner."""

from __future__ import annotations

import tempfile
from pathlib import Path

from check_source_map_denylist import load_denylist, scan_paths


def main() -> int:
    tokens = load_denylist()
    blocked_url = tokens["blocked_urls"][0]
    with tempfile.TemporaryDirectory() as directory:
        fixture = Path(directory) / "injected-pr.txt"
        fixture.write_text(f"dependency = {blocked_url}\n", encoding="utf-8")
        hits = scan_paths([fixture], tokens)
    if not hits:
        raise AssertionError("an injected blocked URL must produce a denylist hit")
    print("Source-map denylist injection test passed: blocked URL produced a failure hit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
