# RC-281: Primary License Selection

## Status

**Complete** — MIT license confirmed as primary, ADR-0017 documents the decision, all package metadata declares MIT consistently, 21 tests passed.

## What Was Done

1. **Created ADR-0017** `docs/adr/0017-primary-license-selection.md`:
   - Compares MIT vs Apache-2.0 across 8 criteria
   - Documents why MIT was chosen (simplicity, dependency compatibility, Codex/OpenCode reuse, no patents)
   - Lists third-party license obligations (BSD-3-Clause, MPL-2.0, Apache-2.0, 0BSD)
   - Confirms third-party obligations not overridden by MIT primary license

2. **Added license declarations** for consistency:
   - `frontend/package.json`: Added `"license": "MIT"`
   - `apps/desktop/src-tauri/tauri.conf.json`: Added `"license": "MIT"` to bundle config
   - `apps/desktop/src-tauri/Cargo.toml`: Added `license = "MIT"`
   - `backend/pyproject.toml`: Already had `license = { text = "MIT" }` ✓
   - `LICENSE`: Already had MIT text ✓

3. **Created `scripts/check_rc281_license.py`** — 8 validation checks

4. **Created `backend/tests/test_rc281_license.py`** — 21 tests across 7 classes

## License Consistency Matrix

| File | License | Status |
| --- | --- | --- |
| `LICENSE` | MIT | ✓ (existing) |
| `backend/pyproject.toml` | MIT | ✓ (existing) |
| `frontend/package.json` | MIT | ✓ (added by RC-281) |
| `tauri.conf.json` | MIT | ✓ (added by RC-281) |
| `Cargo.toml` | MIT | ✓ (added by RC-281) |

## Verification Results

- `python scripts/check_rc281_license.py` → PASS
- `pytest backend/tests/test_rc281_license.py -q` → 21 passed

## Limitations

- Legal review of ADR-0017 by a qualified attorney is recommended before production use
- Dependency license scan (pip-audit, npm audit) covers known vulnerabilities but not full license compliance; THIRD_PARTY_NOTICES (RC-282) will handle detailed attribution
