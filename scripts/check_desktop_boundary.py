#!/usr/bin/env python3
"""RC ID: RC-060. Validate the desktop shell command boundary."""

from __future__ import annotations

import tomllib
from pathlib import Path

ALLOWLIST = Path("apps/desktop/command-allowlist.toml")
REQUIRED_COMMANDS = {
    "open_window",
    "pick_file",
    "notify",
    "check_update",
    "store_secret",
    "start_sidecar",
}


def validate_desktop_boundary(repository_root: Path) -> list[str]:
    path = repository_root / ALLOWLIST
    if not path.is_file():
        return [f"missing desktop allowlist: {ALLOWLIST.as_posix()}"]
    with path.open("rb") as handle:
        document = tomllib.load(handle)
    desktop = document.get("desktop")
    commands = document.get("commands")
    errors: list[str] = []
    if not isinstance(desktop, dict) or desktop.get("business_logic") is not False:
        errors.append("desktop shell must declare business_logic=false")
    if not isinstance(commands, list):
        return ["desktop allowlist commands must be an array"]
    names = {item.get("name") for item in commands if isinstance(item, dict)}
    missing = REQUIRED_COMMANDS - names
    if missing:
        errors.append(f"desktop allowlist is missing: {', '.join(sorted(missing))}")
    for source_root in (repository_root / "apps" / "desktop",):
        for path in source_root.rglob("*"):
            if path.suffix not in {".py", ".rs", ".ts", ".tsx"}:
                continue
            content = path.read_text(encoding="utf-8")
            if "prompt_optimizer" in content or "Provider" in content or "AgentCore" in content:
                errors.append(f"desktop shell contains business implementation: {path}")
    return errors


def main() -> int:
    repository_root = Path(__file__).resolve().parents[1]
    errors = validate_desktop_boundary(repository_root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Desktop shell boundary and command allowlist are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
