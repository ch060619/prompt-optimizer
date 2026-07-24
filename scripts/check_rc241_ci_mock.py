#!/usr/bin/env python3
"""RC ID: RC-241. Validate that ordinary CI defaults to Provider/runner mocks."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def main() -> int:
    errors: list[str] = []
    content = WORKFLOW.read_text(encoding="utf-8") if WORKFLOW.is_file() else ""
    if not WORKFLOW.is_file():
        errors.append("missing CI workflow")
    if 'RABBIT_CODE_REAL_PROVIDER_TESTS: "0"' not in content:
        errors.append("backend CI job must disable real Provider tests by default")
    if 'RABBIT_CODE_REAL_PROVIDER_TESTS: "1"' in content:
        errors.append("ordinary CI must not enable real Provider tests")
    if "Provider Mock contract" not in content or "test_rc173_provider_contracts.py" not in content:
        errors.append("CI must run the deterministic Provider Mock contract")
    if "httpx.MockTransport" not in (ROOT / "backend" / "tests" / "test_rc231_provider_contracts.py").read_text(encoding="utf-8"):
        errors.append("Provider contract suite must use httpx.MockTransport")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("RC-241 CI policy valid: ordinary backend jobs disable real Provider tests and run Mock contracts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
