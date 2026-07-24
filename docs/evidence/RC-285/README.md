# RC-285: Automated License Risk Scanning

## Status

**Complete** — License risk policy, scanner script, CI integration, and 22 tests all pass. Scanner covers npm, Python, and model dependencies.

## What Was Done

1. **Created `docs/research/license-risk-policy.yml`**:
   - `allow`: MIT, ISC, BSD-2/3-Clause, 0BSD, Apache-2.0, MPL-2.0, Unlicense, Zlib, Python-2.0
   - `review`: UNKNOWN, null, custom, LicenseRef-Gemma-Terms
   - `deny`: GPL-2.0/3.0, AGPL-3.0, LGPL-2.1/3.0, SSPL, BUSL-1.1, CC-BY-SA-4.0, CC-BY-NC-4.0
   - `exceptions`: gsap (Standard license, dev-only), Gemma 3 (LicenseRef-Gemma-Terms, on-demand download)
   - Categories are mutually exclusive (verified by tests)

2. **Created `scripts/scan_license_risks.py`**:
   - `classify_license()`: Maps license string to allow/review/deny/exception
   - `scan_npm_deps()`: Scans package-lock.json
   - `scan_python_deps_from_notices()`: Scans THIRD_PARTY_NOTICES.md
   - `scan_model_deps()`: Scans manifest.yml
   - `scan_all()`: Aggregates all sources into categorized report
   - CLI: `--check` (exit 1 on denied), `--json` (JSON output)

3. **Added CI license-scan job** to `ci.yml`:
   - Runs on every push/PR
   - Installs pyyaml
   - Runs `python scripts/scan_license_risks.py --check`
   - Fails CI if denied licenses found

4. **Created `scripts/check_rc285_license_risk.py`** — 3 validation groups

5. **Created `backend/tests/test_rc285_license_risk.py`** — 22 tests across 5 classes

## Verification Results

- `python scripts/check_rc285_license_risk.py` → PASS
- `pytest backend/tests/test_rc285_license_risk.py -q` → 22 passed

## Limitations

- Python dependency scanning uses THIRD_PARTY_NOTICES.md (auto-generated) rather than direct pip metadata; some packages may show UNKNOWN license
- Cargo dependencies are not yet scanned (Tauri Cargo.toml has minimal deps; can be added)
- Full pip-audit integration is in `generate_sbom.py` (RC-277); this scanner focuses on license classification
