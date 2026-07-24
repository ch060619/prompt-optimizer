#!/usr/bin/env python3
"""RC ID: RC-274. Reproducible packaging of sidecar and desktop resources.

Builds all components (frontend, sidecar, Tauri shell) with deterministic
settings and generates a manifest with component versions and hashes.

Usage:
    python scripts/build_reproducible.py            # full build
    python scripts/build_reproducible.py --check     # validate setup only
"""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
DESKTOP_DIR = ROOT / "apps" / "desktop"
SIDECAR_SPEC = DESKTOP_DIR / "sidecar.spec"
MANIFEST_PATH = ROOT / "output" / "desktop" / "build-manifest.json"
LOCK_FILES = {
    "frontend": FRONTEND_DIR / "package-lock.json",
    "backend": BACKEND_DIR / "uv.lock" if (BACKEND_DIR / "uv.lock").is_file() else None,
    "rust": DESKTOP_DIR / "src-tauri" / "Cargo.lock" if (DESKTOP_DIR / "src-tauri" / "Cargo.lock").is_file() else None,
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


def _tool_versions() -> dict[str, str]:
    """Collect pinned tool versions for reproducibility."""
    versions: dict[str, str] = {}

    python = shutil.which("python") or shutil.which("python3")
    if python:
        r = subprocess.run([python, "--version"], capture_output=True, text=True)
        versions["python"] = r.stdout.strip()

    node = shutil.which("node")
    if node:
        r = subprocess.run([node, "--version"], capture_output=True, text=True)
        versions["node"] = r.stdout.strip()

    npm = shutil.which("npm")
    if npm:
        r = subprocess.run([npm, "--version"], capture_output=True, text=True)
        versions["npm"] = r.stdout.strip()

    cargo = shutil.which("cargo")
    if cargo:
        r = subprocess.run([cargo, "--version"], capture_output=True, text=True)
        versions["cargo"] = r.stdout.strip()

    rustc = shutil.which("rustc")
    if rustc:
        r = subprocess.run([rustc, "--version"], capture_output=True, text=True)
        versions["rustc"] = r.stdout.strip()

    return versions


def validate_setup() -> list[str]:
    """Validate that all lock files and build configs exist."""
    errors: list[str] = []

    if not SIDECAR_SPEC.is_file():
        errors.append(f"missing sidecar spec: {SIDECAR_SPEC.relative_to(ROOT)}")

    frontend_lock = LOCK_FILES.get("frontend")
    if not frontend_lock or not frontend_lock.is_file():
        errors.append("missing frontend/package-lock.json for reproducible builds")

    # Cargo.lock is auto-generated; check if it exists
    cargo_lock = DESKTOP_DIR / "src-tauri" / "Cargo.lock"
    if not cargo_lock.is_file():
        errors.append("missing Cargo.lock — run 'cargo generate-lockfile' in src-tauri")

    return errors


def build_frontend() -> dict[str, str]:
    """Build frontend dist deterministically."""
    print("[1/3] Building frontend...", flush=True)
    npm = shutil.which("npm")
    if not npm:
        raise RuntimeError("npm not found")

    # Set SOURCE_DATE_EPOCH for deterministic builds
    env = dict(**__import__("os").environ, SOURCE_DATE_EPOCH="1700000000")
    r = subprocess.run([npm, "run", "build"], cwd=FRONTEND_DIR, capture_output=True, text=True, env=env)
    if r.returncode != 0:
        raise RuntimeError(f"frontend build failed: {r.stderr}")

    dist = FRONTEND_DIR / "dist"
    if not dist.is_dir():
        raise RuntimeError("frontend/dist not created")

    # Hash all dist files
    artifacts: dict[str, str] = {}
    for f in sorted(dist.rglob("*")):
        if f.is_file():
            rel = str(f.relative_to(dist))
            artifacts[rel] = _sha256(f)
    print(f"  frontend dist: {len(artifacts)} files", flush=True)
    return artifacts


def build_sidecar() -> dict[str, str]:
    """Build sidecar with PyInstaller."""
    print("[2/3] Building sidecar...", flush=True)
    python = shutil.which("python") or shutil.which("python3")
    if not python:
        raise RuntimeError("python not found")

    # Check PyInstaller is available
    r = subprocess.run([python, "-c", "import PyInstaller"], capture_output=True, text=True)
    if r.returncode != 0:
        print("  Installing PyInstaller...", flush=True)
        r = subprocess.run([python, "-m", "pip", "install", "pyinstaller"], capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"failed to install PyInstaller: {r.stderr}")

    distpath = ROOT / "output" / "desktop" / "sidecar"
    r = subprocess.run(
        [python, "-m", "PyInstaller", str(SIDECAR_SPEC),
         "--distpath", str(distpath),
         "--workpath", str(ROOT / "output" / ".pyinstaller"),
         "--clean", "--noconfirm"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(f"sidecar build failed: {r.stderr}")

    # Hash sidecar output
    artifacts: dict[str, str] = {}
    sidecar_dir = distpath / "rabbit-sidecar"
    if sidecar_dir.is_dir():
        for f in sorted(sidecar_dir.rglob("*")):
            if f.is_file():
                rel = str(f.relative_to(sidecar_dir))
                artifacts[rel] = _sha256(f)
    print(f"  sidecar: {len(artifacts)} files", flush=True)
    return artifacts


def build_tauri() -> dict[str, str]:
    """Build Tauri shell (cargo build --release)."""
    print("[3/3] Building Tauri shell...", flush=True)
    cargo = shutil.which("cargo")
    if not cargo:
        raise RuntimeError("cargo not found")

    tauri_dir = DESKTOP_DIR / "src-tauri"
    r = subprocess.run([cargo, "build", "--release"], cwd=tauri_dir, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"tauri build failed: {r.stderr}")

    # Hash the binary
    binary_name = "rabbit-code-desktop.exe" if platform.system() == "Windows" else "rabbit-code-desktop"
    binary = tauri_dir / "target" / "release" / binary_name
    artifacts: dict[str, str] = {}
    if binary.is_file():
        artifacts[binary.name] = _sha256(binary)
    print(f"  tauri shell: {len(artifacts)} files", flush=True)
    return artifacts


def write_manifest(
    frontend_hashes: dict[str, str],
    sidecar_hashes: dict[str, str],
    tauri_hashes: dict[str, str],
) -> None:
    """Write build manifest with all component info."""
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "version": "3.0.0",
        "build_time": datetime.now(timezone.utc).isoformat(),
        "platform": platform.system(),
        "machine": platform.machine(),
        "tools": _tool_versions(),
        "components": {
            "frontend": {"file_count": len(frontend_hashes), "hashes": frontend_hashes},
            "sidecar": {"file_count": len(sidecar_hashes), "hashes": sidecar_hashes},
            "tauri_shell": {"file_count": len(tauri_hashes), "hashes": tauri_hashes},
        },
        "reproducibility": {
            "source_date_epoch": "1700000000",
            "upx_disabled": True,
            "strip_disabled": True,
            "note": "Two builds from the same source and toolchain should produce identical hashes.",
        },
    }

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(f"  manifest written to {MANIFEST_PATH.relative_to(ROOT)}", flush=True)


def main() -> int:
    check_only = "--check" in sys.argv

    errors = validate_setup()
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if check_only:
        print(f"RC-274 setup valid. Tools: {json.dumps(_tool_versions(), indent=2)}")
        return 0

    print("RC-274: Reproducible packaging...", flush=True)
    try:
        fe = build_frontend()
        sc = build_sidecar()
        ta = build_tauri()
        write_manifest(fe, sc, ta)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print("RC-274: Build complete. Manifest at output/desktop/build-manifest.json", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
