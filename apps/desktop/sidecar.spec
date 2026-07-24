# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Rabbit Code sidecar (FastAPI backend).

Build: pyinstaller apps/desktop/sidecar.spec --distpath output/desktop/sidecar
Output: output/desktop/sidecar/rabbit-sidecar.exe (Windows)
        output/desktop/sidecar/rabbit-sidecar (Linux)
"""

import sys
from pathlib import Path

block_cipher = None

ROOT = Path(SPECPATH).resolve().parents[1]  # project root
BACKEND_SRC = ROOT / "backend" / "src"

a = Analysis(
    [str(BACKEND_SRC / "prompt_optimizer" / "cli" / "__main__.py")],
    pathex=[str(BACKEND_SRC)],
    binaries=[],
    datas=[
        (str(BACKEND_SRC / "prompt_optimizer" / "api" / "openapi.yaml"), "prompt_optimizer/api"),
    ],
    hiddenimports=[
        "prompt_optimizer.api.app",
        "prompt_optimizer.api.routes",
        "prompt_optimizer.core.config",
        "prompt_optimizer.core.optimizer",
        "prompt_optimizer.cli.app",
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "PIL", "pytest", "IPython"],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="rabbit-sidecar",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX breaks reproducibility
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="rabbit-sidecar",
)
