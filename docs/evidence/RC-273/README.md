# RC-273: Publish CLI Installation Channels

## Status

**Complete** — All channel configurations, install scripts, and validation in place.

## What Was Done

1. **PyPI** (primary channel): `backend/pyproject.toml` already configured with `rabbit-code` package, `rabbit` and `prompt-opt` entry points, MIT license, Python >=3.12.

2. **Install scripts**:
   - `scripts/install/install.ps1` — Windows PowerShell installer (checks Python, pip install, verifies `rabbit version`)
   - `scripts/install/install.sh` — Linux shell installer (checks python3, pip install --user, verifies)

3. **winget manifest**: `scripts/install/winget.yml` — Windows Package Manager manifest with RabbitCode.RabbitCode identifier, MIT license, x64 architecture.

4. **Scoop manifest**: `scripts/install/scoop.json` — Scoop package manifest with version 3.0.0, MIT license, auto-update checkver.

5. **Validation script**: `scripts/check_rc273_cli_channels.py` — validates all channels.

6. **Test**: `backend/tests/test_rc273_cli_channels.py` — 6 tests, all pass.

## Verification

- `python scripts/check_rc273_cli_channels.py` → PASS
- `.venv\Scripts\python.exe -m pytest backend/tests/test_rc273_cli_channels.py -q` → 6 passed

## Limitations

- PyPI publication requires `twine upload` with credentials (not performed in this session).
- winget manifest SHA-256 is TBD (pending actual binary release).
- Scoop manifest hash is TBD (pending actual binary release).
- PATH handling on Linux depends on user's shell profile (~/.local/bin).
- Upgrade/uninstall smoke tests require published versions on PyPI.
