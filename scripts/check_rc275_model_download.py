#!/usr/bin/env python3
"""RC ID: RC-275. Validate local model on-demand download policy.

Ensures:
1. No model weight files are bundled in Tauri config or PyInstaller spec
2. The local_install.py module has checksum verification
3. Download failures are handled with retry/status
4. Model weights are excluded from build artifacts
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAURI_CONF = ROOT / "apps" / "desktop" / "src-tauri" / "tauri.conf.json"
SIDECAR_SPEC = ROOT / "apps" / "desktop" / "sidecar.spec"
BUILD_DESKTOP = ROOT / "scripts" / "build_desktop.py"
BUILD_REPRODUCIBLE = ROOT / "scripts" / "build_reproducible.py"
LOCAL_INSTALL = ROOT / "backend" / "src" / "prompt_optimizer" / "local_install.py"

MODEL_WEIGHT_EXTS = {".gguf", ".safetensors", ".pt", ".pth", ".onnx", ".tflite", ".ckpt"}


def main() -> int:
    errors: list[str] = []

    # 1. Tauri config must not reference model files
    tauri_conf = TAURI_CONF.read_text(encoding="utf-8") if TAURI_CONF.is_file() else ""
    for ext in MODEL_WEIGHT_EXTS:
        if ext in tauri_conf.lower():
            errors.append(f"tauri.conf.json references model weight file ({ext})")

    # 2. PyInstaller spec must not include model files
    sidecar = SIDECAR_SPEC.read_text(encoding="utf-8") if SIDECAR_SPEC.is_file() else ""
    for ext in MODEL_WEIGHT_EXTS:
        if ext in sidecar.lower():
            errors.append(f"sidecar.spec references model weight file ({ext})")
    if "model" in sidecar.lower() and "weight" in sidecar.lower():
        errors.append("sidecar.spec may reference model weights")

    # 3. Build scripts must not copy model files
    for script_path in [BUILD_DESKTOP, BUILD_REPRODUCIBLE]:
        if not script_path.is_file():
            continue
        content = script_path.read_text(encoding="utf-8")
        for ext in MODEL_WEIGHT_EXTS:
            if ext in content.lower():
                errors.append(f"{script_path.name} references model weight file ({ext})")

    # 4. local_install.py must have checksum verification
    if not LOCAL_INSTALL.is_file():
        errors.append("missing local_install.py")
    else:
        install_code = LOCAL_INSTALL.read_text(encoding="utf-8")
        if "checksum" not in install_code:
            errors.append("local_install.py must have checksum verification")
        if "sha256" not in install_code.lower() and "hashlib" not in install_code:
            errors.append("local_install.py must use hashlib for checksums")
        if "failed" not in install_code:
            errors.append("local_install.py must handle download failures")
        if "retr" not in install_code.lower():
            errors.append("local_install.py must have retry logic")
        if "download" not in install_code.lower():
            errors.append("local_install.py must have download logic")

    # 5. No model weight files in source tree (excluding venv, node_modules)
    for pattern in ["*.gguf", "*.safetensors", "*.onnx", "*.tflite", "*.ckpt"]:
        for f in ROOT.rglob(pattern):
            rel = str(f.relative_to(ROOT))
            if ".venv" not in rel and "node_modules" not in rel:
                errors.append(f"model weight file found in source: {rel}")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print("RC-275 local model on-demand download policy valid: no weights in build configs, checksum+retry in installer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
