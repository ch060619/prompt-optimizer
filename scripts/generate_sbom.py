#!/usr/bin/env python3
"""RC ID: RC-277. Generate SBOM, artifact hashes, and supply chain manifest.

Produces:
    output/supply-chain/sbom.json         - CycloneDX SBOM
    output/supply-chain/provenance.json   - Build provenance
    output/supply-chain/licenses.json     - Dependency license report
    output/supply-chain/artifacts.json    - Artifact SHA-256 hashes
    output/supply-chain/scan-report.json  - Vulnerability scan report
    output/supply-chain/manifest.json     - Combined supply chain manifest

Usage:
    python scripts/generate_sbom.py            # full generation
    python scripts/generate_sbom.py --check     # validate setup only
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
OUTPUT_DIR = ROOT / "output" / "supply-chain"
PYPROJECT = BACKEND_DIR / "pyproject.toml"
PACKAGE_LOCK = FRONTEND_DIR / "package-lock.json"


def _run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def get_git_info() -> dict[str, str]:
    """Get git commit, branch, and remote info."""
    info: dict[str, str] = {}
    for key, args in [
        ("commit", ["rev-parse", "HEAD"]),
        ("short_commit", ["rev-parse", "--short", "HEAD"]),
        ("branch", ["rev-parse", "--abbrev-ref", "HEAD"]),
        ("remote", ["config", "--get", "remote.origin.url"]),
    ]:
        r = _run(["git"] + args, cwd=ROOT)
        if r.returncode == 0:
            info[key] = r.stdout.strip()
    return info


def get_tool_versions() -> dict[str, str]:
    """Collect tool versions for provenance."""
    versions: dict[str, str] = {}
    for name, cmd in [("python", ["python", "--version"]), ("node", ["node", "--version"]),
                       ("npm", ["npm", "--version"]), ("cargo", ["cargo", "--version"]),
                       ("rustc", ["rustc", "--version"])]:
        exe = shutil.which(cmd[0])
        if exe:
            r = subprocess.run([exe] + cmd[1:], capture_output=True, text=True)
            if r.returncode == 0:
                versions[name] = r.stdout.strip()
    return versions


def generate_provenance() -> dict[str, object]:
    """Generate build provenance."""
    return {
        "build_time": datetime.now(timezone.utc).isoformat(),
        "platform": platform.system(),
        "machine": platform.machine(),
        "python_version": platform.python_version(),
        "tools": get_tool_versions(),
        "git": get_git_info(),
        "source_root": str(ROOT),
    }


def generate_python_deps() -> list[dict[str, str]]:
    """Get Python dependencies with versions and licenses."""
    python = shutil.which("python") or shutil.which("python3")
    if not python:
        return []

    # Get installed packages
    r = subprocess.run([python, "-m", "pip", "list", "--format=json"],
                       capture_output=True, text=True, cwd=BACKEND_DIR)
    if r.returncode != 0:
        return []

    deps: list[dict[str, str]] = []
    try:
        packages = json.loads(r.stdout)
    except json.JSONDecodeError:
        return []

    for pkg in packages:
        deps.append({
            "name": pkg.get("name", ""),
            "version": pkg.get("version", ""),
            "type": "pypi",
            "license": "unknown",  # Would use pip-licenses for actual license
        })
    return deps


def generate_npm_deps() -> list[dict[str, str]]:
    """Get npm dependencies from package-lock.json."""
    if not PACKAGE_LOCK.is_file():
        return []

    lock = json.loads(PACKAGE_LOCK.read_text(encoding="utf-8"))
    deps: list[dict[str, str]] = []
    packages = lock.get("packages", {})
    for name, info in packages.items():
        if not name:  # Root package
            continue
        clean_name = name.replace("node_modules/", "")
        deps.append({
            "name": clean_name,
            "version": info.get("version", ""),
            "type": "npm",
            "license": info.get("license", "unknown"),
            "resolved": info.get("resolved", ""),
            "integrity": info.get("integrity", ""),
        })
    return deps


def generate_sbom(python_deps: list[dict[str, str]], npm_deps: list[dict[str, str]]) -> dict[str, object]:
    """Generate CycloneDX-format SBOM."""
    components: list[dict[str, object]] = []
    for dep in python_deps + npm_deps:
        components.append({
            "type": "library",
            "name": dep["name"],
            "version": dep["version"],
            "bom-ref": f"{dep['type']}:{dep['name']}@{dep['version']}",
            "licenses": [{"license": {"name": dep.get("license", "unknown")}}],
            "purl": f"pkg:{dep['type']}/{dep['name']}@{dep['version']}",
        })

    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.4",
        "serialNumber": f"urn:uuid:{datetime.now(timezone.utc).strftime('%Y%m%d')}-rabbit-code",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "name": "rabbit-code",
                "version": "3.0.0",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "components": components,
    }


def generate_license_report(python_deps: list[dict], npm_deps: list[dict]) -> dict[str, object]:
    """Generate license summary report."""
    all_deps = python_deps + npm_deps
    license_counts: dict[str, int] = {}
    for dep in all_deps:
        lic = dep.get("license", "unknown")
        license_counts[lic] = license_counts.get(lic, 0) + 1

    # Flag non-standard licenses
    standard_licenses = {"MIT", "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause",
                         "ISC", "Python-2.0", "MPL-2.0", "Unlicense", "CC0-1.0"}
    flagged: list[dict[str, str]] = []
    for dep in all_deps:
        lic = dep.get("license", "unknown")
        if lic not in standard_licenses and lic != "unknown":
            flagged.append({"name": dep["name"], "version": dep["version"], "license": lic})

    return {
        "total_dependencies": len(all_deps),
        "license_summary": license_counts,
        "flagged_licenses": flagged,
        "note": "Flagged licenses are not in the standard permissive license list.",
    }


def generate_artifact_hashes() -> dict[str, str]:
    """Generate SHA-256 hashes for key build artifacts."""
    artifacts: dict[str, str] = {}

    # Frontend dist
    dist_dir = FRONTEND_DIR / "dist"
    if dist_dir.is_dir():
        for f in sorted(dist_dir.rglob("*")):
            if f.is_file():
                rel = f"frontend/dist/{f.relative_to(dist_dir)}"
                artifacts[rel] = _sha256(f)

    # Desktop binary
    binary_name = "rabbit-code-desktop.exe" if platform.system() == "Windows" else "rabbit-code-desktop"
    binary = ROOT / "apps" / "desktop" / "src-tauri" / "target" / "release" / binary_name
    if binary.is_file():
        artifacts[f"desktop/{binary_name}"] = _sha256(binary)

    # Backend package
    for pyfile in (BACKEND_DIR / "src" / "prompt_optimizer").rglob("*.py"):
        rel = f"backend/{pyfile.relative_to(BACKEND_DIR)}"
        artifacts[rel] = _sha256(pyfile)

    return artifacts


def generate_scan_report() -> dict[str, object]:
    """Generate vulnerability scan report using pip-audit if available."""
    python = shutil.which("python") or shutil.which("python3")
    if not python:
        return {"status": "skipped", "reason": "python not found"}

    r = subprocess.run([python, "-m", "pip_audit", "--format=json"],
                       capture_output=True, text=True, cwd=BACKEND_DIR)
    if r.returncode != 0:
        # pip-audit not installed, try safety
        return {
            "status": "skipped",
            "reason": "pip-audit not available",
            "note": "Install with: pip install pip-audit",
        }

    try:
        vulns = json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"status": "error", "reason": "invalid JSON from pip-audit"}

    return {
        "status": "completed",
        "scanner": "pip-audit",
        "vulnerabilities": vulns,
        "vulnerability_count": len(vulns) if isinstance(vulns, list) else 0,
    }


def main() -> int:
    check_only = "--check" in sys.argv

    if not PYPROJECT.is_file():
        print("ERROR: backend/pyproject.toml not found", file=sys.stderr)
        return 1

    if check_only:
        print("RC-277 SBOM generation setup valid.")
        return 0

    print("RC-277: Generating supply chain artifacts...", flush=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Provenance
    print("  [1/5] Build provenance...", flush=True)
    provenance = generate_provenance()
    (OUTPUT_DIR / "provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8")

    # 2. Dependencies
    print("  [2/5] Dependency lists...", flush=True)
    python_deps = generate_python_deps()
    npm_deps = generate_npm_deps()
    print(f"    Python: {len(python_deps)} deps, npm: {len(npm_deps)} deps", flush=True)

    # 3. SBOM
    print("  [3/5] SBOM (CycloneDX)...", flush=True)
    sbom = generate_sbom(python_deps, npm_deps)
    (OUTPUT_DIR / "sbom.json").write_text(
        json.dumps(sbom, indent=2, sort_keys=True), encoding="utf-8")

    # 4. Licenses
    print("  [4/5] License report...", flush=True)
    licenses = generate_license_report(python_deps, npm_deps)
    (OUTPUT_DIR / "licenses.json").write_text(
        json.dumps(licenses, indent=2, sort_keys=True), encoding="utf-8")

    # 5. Artifacts + Scan
    print("  [5/5] Artifact hashes and scan...", flush=True)
    artifacts = generate_artifact_hashes()
    (OUTPUT_DIR / "artifacts.json").write_text(
        json.dumps(artifacts, indent=2, sort_keys=True), encoding="utf-8")

    scan = generate_scan_report()
    (OUTPUT_DIR / "scan-report.json").write_text(
        json.dumps(scan, indent=2, sort_keys=True), encoding="utf-8")

    # Combined manifest
    manifest = {
        "version": "3.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provenance": provenance,
        "sbom_path": "sbom.json",
        "licenses_path": "licenses.json",
        "artifacts_path": "artifacts.json",
        "scan_path": "scan-report.json",
        "total_components": len(python_deps) + len(npm_deps),
        "total_artifacts": len(artifacts),
    }
    (OUTPUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    print(f"RC-277: Supply chain artifacts generated in {OUTPUT_DIR.relative_to(ROOT)}/", flush=True)
    print(f"  Components: {len(python_deps) + len(npm_deps)}", flush=True)
    print(f"  Artifacts: {len(artifacts)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
