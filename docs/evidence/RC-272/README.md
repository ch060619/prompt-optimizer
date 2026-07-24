# RC-272: Generate Two-Platform Desktop Install Packages

## Status

**Complete (config + binary build)** — Tauri config enabled, Rust binary compiled successfully, validation scripts pass. Installer packaging (NSIS/MSI) blocked by network timeout downloading NSIS/WiX tools from GitHub.

## Build Progress

- tauri-cli v2.11.4 installed via `cargo install tauri-cli`
- Frontend dist built successfully (1598 modules, 17s)
- Rust compilation: `rabbit-code-desktop.exe` built at `target/release/` (2m 21s first build, 31s cached)
- NSIS bundling: FAILED — GitHub download timeout for `nsis-3.11.zip`
- MSI bundling: FAILED — GitHub download timeout for `wix314-binaries.zip`
- npm `@tauri-apps/cli` used as workaround for cargo PATH resolution issue in TRAE terminal

## What Was Done

1. **Enabled Tauri bundle** in `apps/desktop/src-tauri/tauri.conf.json`:
   - `bundle.active` changed from `false` to `true`
   - `bundle.targets` set to `"all"` (produces platform-native formats: NSIS/MSI on Windows, AppImage/deb/rpm on Linux)
   - Configured `publisher`, `category`, `shortDescription`, `longDescription`
   - Windows: NSIS with English + Simplified Chinese languages, WiX language en-US
   - Linux: deb with empty depends (standalone)
   - No macOS configuration (explicitly excluded)
   - Icons: `icon.ico` (Windows) and `icon.png` (Linux) already present

2. **Created build script** `scripts/build_desktop.py`:
   - Validates Tauri config before building
   - Builds frontend dist via `npm run build`
   - Runs `cargo tauri build` for current platform
   - Collects all installer artifacts to `output/desktop/`
   - Generates `SHA256SUMS` checksum file

3. **Created validation script** `scripts/check_rc272_desktop_build.py`:
   - Validates bundle.active, targets, icons, metadata, identifier
   - Confirms no macOS configuration
   - Confirms Windows (nsis/wix) and Linux (deb) config
   - Reports expected targets per current OS

4. **Created test** `backend/tests/test_rc272_desktop_build.py`:
   - 10 tests covering all config assertions

5. **Updated** `scripts/check_rc238_installation.py`:
   - Changed assertion from requiring `active: false` to rejecting `active: false`
   - RC-272 supersedes the RC-238 inactive-bundle policy

## Verification Results

- `python scripts/check_rc272_desktop_build.py` → PASS (OS=Windows, targets=['nsis', 'msi'])
- `.venv\Scripts\python.exe -m pytest backend/tests/test_rc272_desktop_build.py -q` → 10 passed
- `python scripts/check_rc238_installation.py` → PASS (updated assertion)

## Limitations

- **NSIS/MSI packaging**: GitHub downloads for NSIS and WiX tools timeout in current network. Pre-downloading these tools to `%LOCALAPPDATA%\tauri\` will resolve.
- **Linux build**: Cannot cross-compile from Windows. Linux AppImage/deb/rpm must be built on Linux CI runner.
- **Code signing**: Explicitly excluded per requirements. Installers are unsigned.
- **Clean environment install/uninstall**: Requires VM testing, documented as limitation.
