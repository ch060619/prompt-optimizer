# RC-238 Evidence

## Scope

Added `scripts/check_rc238_installation.py` and
`backend/tests/test_rc238_installation.py`. The checks keep the container release input
lockfile-based, build the frontend before runtime packaging, run as non-root `rabbit`,
disclose inactive native Tauri bundling, and keep a deterministic SHA-256 probe.

## Verification

```text
python scripts/check_rc238_installation.py
python -m pytest backend/tests/test_rc238_installation.py -q
.venv\Scripts\ruff.exe check scripts/check_rc238_installation.py backend/tests/test_rc238_installation.py
npm run build
```

Results: installation contract passed; `2 passed`; Ruff passed; Vite production build
passed with the existing chunk-size warning.

## Limits

This Windows workspace has no `cargo` executable in PATH, and the Tauri configuration
sets `bundle.active` to false. No clean Windows/Linux VM, real installer, upgrade,
downgrade-block, uninstall, or scheduled-service residue test was claimed. Those remain
required platform/release-candidate validation.

## RC-230~271 remediation follow-up (2026-07-19)

The Docker failure found during the remediation audit was fixed by copying
`packages/ui/` into the frontend build stage. `scripts/check_rc238_installation.py`
and `backend/tests/test_rc238_installation.py` now assert that shared token input
exists. `docker build --progress=plain -t rabbit-code:rc271-audit .` completed;
the resulting image keeps the non-root `rabbit` runtime boundary. Native Tauri
bundling remains inactive by policy.
