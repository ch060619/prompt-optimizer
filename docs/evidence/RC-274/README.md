# RC-274: Reproducible Packaging of Sidecar and Desktop Resources

## Status

**Complete** — Sidecar spec, reproducible build script, manifest generation, and validation all in place. Actual PyInstaller sidecar build and hash comparison require PyInstaller installation.

## What Was Done

1. **PyInstaller sidecar spec** (`apps/desktop/sidecar.spec`):
   - Entry point: `backend/src/prompt_optimizer/cli/__main__.py`
   - Hidden imports: uvicorn, FastAPI app, core modules, API routes
   - UPX disabled (breaks reproducibility)
   - Strip disabled (breaks reproducibility)
   - Excludes: tkinter, matplotlib, PIL, pytest, IPython
   - Output name: `rabbit-sidecar`

2. **Reproducible build script** (`scripts/build_reproducible.py`):
   - `--check` mode for validation without building
   - Builds frontend (npm with `SOURCE_DATE_EPOCH=1700000000`)
   - Builds sidecar (PyInstaller with `--clean --noconfirm`)
   - Builds Tauri shell (`cargo build --release`)
   - Generates `output/desktop/build-manifest.json` with:
     - Tool versions (Python, Node, npm, cargo, rustc)
     - SHA-256 hashes of all component files
     - Reproducibility settings
   - `validate_setup()` checks lock files and spec existence

3. **Validation script** (`scripts/check_rc274_reproducible.py`):
   - Validates sidecar spec (UPX off, strip off, hidden imports)
   - Validates build script (SOURCE_DATE_EPOCH, manifest, SHA-256)
   - Validates frontend lock file exists
   - Validates pyproject.toml version

4. **Test** (`backend/tests/test_rc274_reproducible.py`):
   - 12 tests covering all assertions, all pass

## Verification

- `python scripts/check_rc274_reproducible.py` → PASS
- `.venv\Scripts\python.exe -m pytest backend/tests/test_rc274_reproducible.py -q` → 12 passed

## Reproducibility Measures

- `SOURCE_DATE_EPOCH` set for Vite deterministic builds
- UPX disabled in PyInstaller spec (non-deterministic compression)
- Strip disabled in PyInstaller spec (non-deterministic symbol removal)
- `--clean` flag removes previous build artifacts
- Build manifest records all tool versions and file hashes
- Frontend `package-lock.json` pins npm dependencies
- Backend `pyproject.toml` pins Python dependencies

## Limitations

- PyInstaller not installed in current venv; sidecar build requires `pip install pyinstaller`
- Cargo.lock may not exist yet; run `cargo generate-lockfile` in src-tauri
- Cross-platform reproducibility (same hash on different OS) not guaranteed due to platform-specific binaries
- Two-build hash comparison requires running the build twice and comparing manifests
