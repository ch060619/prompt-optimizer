#!/usr/bin/env python3
"""RC ID: RC-279. Generate GitHub Release notes from CHANGELOG and git log.

Produces a structured release note with sections for:
    - Summary
    - Installers and CLI
    - Checksums
    - SBOM and supply chain
    - Licenses
    - Known issues
    - Upgrade instructions

Usage:
    python scripts/generate_release_notes.py --version 3.0.0 --channel stable
    python scripts/generate_release_notes.py --version 3.0.0 --channel stable --output RELEASE_NOTES.md
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = ROOT / "CHANGELOG.md"

KNOWN_ISSUES_TEMPLATE = """\
### Known Issues

- NSIS/MSI installer packaging may require pre-downloaded Tauri tools on restricted networks.
- Linux AppImage/deb/rpm must be built on a Linux runner; cross-compilation is not supported.
- Installers are unsigned (code signing is explicitly excluded per project policy).
- Local model download requires a one-time network connection; offline mode works without models.
"""

UPGRADE_INSTRUCTIONS = """\
### Upgrade Instructions

#### CLI (pip)
```bash
pip install --upgrade rabbit-code=={version}
rabbit --version
```

#### Desktop (Windows)
Download the `.exe` (NSIS) or `.msi` installer, verify its SHA-256 against `SHA256SUMS-desktop-windows.txt`, then run it.

#### Desktop (Linux)
Download the `.deb` / `.AppImage` / `.rpm`, verify its SHA-256 against `SHA256SUMS-desktop-linux.txt`, then install with your package manager.

#### Verify Download Integrity
```bash
sha256sum rabbit-code-{version}-*.whl
# Compare with the value in SHA256SUMS-cli.txt
```

#### Rollback
```bash
pip install rabbit-code==<previous-version>
```
"""


def extract_changelog_entry(version: str) -> str:
    """Extract the changelog section for the given version."""
    if not CHANGELOG.is_file():
        return f"See git log for changes in v{version}."
    text = CHANGELOG.read_text(encoding="utf-8")
    # Match [version] or ## [version] headers
    pattern = rf"##\s*\[{re.escape(version)}\].*?(?=\n##\s*\[|\Z)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(0).strip()
    return f"See CHANGELOG.md for changes in v{version}."


def get_git_log_summary(version: str) -> str:
    """Get a summary of commits since the last tag."""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--no-decorate", "-20", f"v{version}~1..HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=ROOT,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "(git log unavailable)"


def generate_release_notes(version: str, channel: str) -> str:
    """Generate the full release notes document."""
    changelog_entry = extract_changelog_entry(version)
    git_log = get_git_log_summary(version)

    lines = [
        f"# Rabbit Code v{version} ({channel})",
        "",
        "## Summary",
        "",
        changelog_entry,
        "",
        "### Recent Commits",
        "```",
        git_log,
        "```",
        "",
        "### Installers and CLI",
        "",
        "| Artifact | Platform | Description |",
        "| --- | --- | --- |",
        "| `*.whl` | Cross-platform | Python CLI wheel (pip install) |",
        "| `*.exe` / `*.msi` | Windows | Desktop installer (NSIS/WiX) |",
        "| `*.deb` / `*.AppImage` / `*.rpm` | Linux | Desktop installer |",
        "",
        "### Checksums",
        "",
        "- `SHA256SUMS-cli.txt` — CLI wheel SHA-256",
        "- `SHA256SUMS-desktop-windows.txt` — Windows installer SHA-256",
        "- `SHA256SUMS-desktop-linux.txt` — Linux installer SHA-256",
        "",
        "### SBOM and Supply Chain",
        "",
        "- `sbom.json` — CycloneDX 1.4 Software Bill of Materials",
        "- `provenance.json` — Build provenance (git commit, tools, platform)",
        "- `artifacts.json` — Artifact SHA-256 hashes",
        "- `licenses.json` — Dependency license report",
        "",
        "### Licenses",
        "",
        "- `LICENSE` — Rabbit Code primary license",
        "- `NOTICE` — Attribution notices",
        "- `THIRD_PARTY_NOTICES` — Third-party license obligations",
        "",
        KNOWN_ISSUES_TEMPLATE,
        UPGRADE_INSTRUCTIONS.format(version=version),
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate GitHub Release notes")
    parser.add_argument("--version", required=True, help="Release version (e.g. 3.0.0)")
    parser.add_argument("--channel", required=True, choices=["stable", "beta", "nightly"])
    parser.add_argument("--output", default="-", help="Output file or '-' for stdout")
    args = parser.parse_args()

    notes = generate_release_notes(args.version, args.channel)

    if args.output == "-":
        print(notes)
    else:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(notes, encoding="utf-8")
        print(f"Release notes written to {args.output}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
