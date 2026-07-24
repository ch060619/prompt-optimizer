#!/usr/bin/env python3
"""RC ID: RC-272. Build desktop installers and generate SHA-256 checksums.

Usage:
    python scripts/build_desktop.py            # build for current platform
    python scripts/build_desktop.py --check     # validate config only, no build

Produces:
    output/desktop/SHA256SUMS  - checksums of all bundle artifacts
    output/desktop/            - installer files from Tauri bundler
"""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESKTOP_DIR = ROOT / "apps" / "desktop" / "src-tauri"
FRONTEND_DIR = ROOT / "frontend"
OUTPUT_DIR = ROOT / "output" / "desktop"
TAURI_CONF = DESKTOP_DIR / "tauri.conf.json"

EXPECTED_TARGETS = {
    "Windows": ["nsis", "msi"],
    "Linux": ["appimage", "deb", "rpm"],
}


def _run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    print(f"  $ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_config() -> list[str]:
    """Validate tauri.conf.json bundle configuration."""
    errors: list[str] = []
    if not TAURI_CONF.is_file():
        errors.append(f"missing {TAURI_CONF.relative_to(ROOT)}")
        return errors

    conf = json.loads(TAURI_CONF.read_text(encoding="utf-8"))
    bundle = conf.get("bundle", {})

    if not bundle.get("active"):
        errors.append("bundle.active must be true")

    if bundle.get("targets") != "all":
        errors.append("bundle.targets must be 'all' to cover Windows and Linux")

    icons = bundle.get("icon", [])
    if not icons:
        errors.append("bundle.icon must list at least icon.ico and icon.png")
    for icon in icons:
        icon_path = DESKTOP_DIR / icon
        if not icon_path.is_file():
            errors.append(f"missing icon file: {icon}")

    if not bundle.get("publisher"):
        errors.append("bundle.publisher must be set")
    if not bundle.get("category"):
        errors.append("bundle.category must be set")
    if not bundle.get("shortDescription"):
        errors.append("bundle.shortDescription must be set")

    identifier = conf.get("identifier", "")
    if not identifier:
        errors.append("identifier must be set")

    return errors


def build_frontend() -> bool:
    """Build the frontend dist that Tauri bundles."""
    print("[1/3] Building frontend...", flush=True)
    npm = shutil.which("npm")
    if not npm:
        print("  ERROR: npm not found in PATH", file=sys.stderr)
        return False
    result = _run([npm, "run", "build"], cwd=FRONTEND_DIR)
    if result.returncode != 0:
        print(f"  ERROR: frontend build failed\n{result.stderr}", file=sys.stderr)
        return False
    dist = FRONTEND_DIR / "dist"
    if not dist.is_dir():
        print(f"  ERROR: {dist.relative_to(ROOT)} not created", file=sys.stderr)
        return False
    print("  frontend build OK", flush=True)
    return True


def build_tauri() -> bool:
    """Run Tauri bundler for the current platform."""
    print("[2/3] Building Tauri bundle...", flush=True)
    cargo = shutil.which("cargo")
    if not cargo:
        print("  ERROR: cargo not found in PATH", file=sys.stderr)
        return False

    # Ensure tauri-cli is available
    result = _run([cargo, "tauri", "--version"], cwd=DESKTOP_DIR)
    if result.returncode != 0:
        print("  Installing tauri-cli...", flush=True)
        result = _run([cargo, "install", "tauri-cli", "--version", "^2"])
        if result.returncode != 0:
            print(f"  ERROR: failed to install tauri-cli\n{result.stderr}", file=sys.stderr)
            return False

    result = _run([cargo, "tauri", "build"], cwd=DESKTOP_DIR)
    if result.returncode != 0:
        print(f"  ERROR: tauri build failed\n{result.stderr}", file=sys.stderr)
        return False
    print("  Tauri build OK", flush=True)
    return True


def collect_artifacts() -> bool:
    """Find bundle outputs, copy to output/desktop, generate SHA256SUMS."""
    print("[3/3] Collecting artifacts and generating checksums...", flush=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Tauri output directory pattern: apps/desktop/src-tauri/target/release/bundle/
    bundle_dir = DESKTOP_DIR / "target" / "release" / "bundle"
    if not bundle_dir.is_dir():
        print(f"  ERROR: bundle output not found at {bundle_dir.relative_to(ROOT)}", file=sys.stderr)
        return False

    artifacts: list[Path] = []
    for ext in ("*.exe", "*.msi", "*.AppImage", "*.deb", "*.rpm"):
        artifacts.extend(bundle_dir.rglob(ext))

    if not artifacts:
        print("  ERROR: no installer artifacts found", file=sys.stderr)
        return False

    lines: list[str] = []
    for art in sorted(artifacts):
        dest = OUTPUT_DIR / art.name
        shutil.copy2(art, dest)
        digest = _sha256(dest)
        lines.append(f"{digest}  {art.name}")
        print(f"  {art.name}  SHA-256: {digest}", flush=True)

    sums_file = OUTPUT_DIR / "SHA256SUMS"
    sums_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  Checksums written to {sums_file.relative_to(ROOT)}", flush=True)
    return True


def main() -> int:
    check_only = "--check" in sys.argv

    errors = validate_config()
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if check_only:
        current_os = platform.system()
        expected = EXPECTED_TARGETS.get(current_os, [])
        print(f"RC-272 config valid. Current OS: {current_os}. Expected targets: {', '.join(expected) or 'unknown'}.")
        return 0

    print("RC-272: Building desktop installers...", flush=True)
    if not build_frontend():
        return 1
    if not build_tauri():
        return 1
    if not collect_artifacts():
        return 1

    print("RC-272: Build complete. Artifacts in output/desktop/.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
