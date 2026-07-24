# RC-282: Maintain All License Files

## Status

**Complete** — NOTICE file created, model/asset license directories created, THIRD_PARTY_NOTICES.md validated, 25 tests passed.

## What Was Done

1. **Created `NOTICE`** file at root:
   - MIT copyright notice
   - Attribution for Python dependencies (FastAPI, Pydantic, Typer, Uvicorn, HTTPX, Rich, PyYAML)
   - Attribution for Node.js dependencies (React, Vite, TypeScript, Vitest, ESLint)
   - Attribution for local models (Gemma, Qwen) with license references
   - Reference to THIRD_PARTY_NOTICES.md and ADR-0003 (OpenCode boundary)

2. **Created `docs/licenses/models/README.md`**:
   - Gemma 3 1B IT: LicenseRef-Gemma-Terms (gated, requires acceptance)
   - Qwen2.5-Coder 1.5B Instruct: Apache-2.0
   - References to manifest.yml and LocalInstallCore enforcement

3. **Created `docs/licenses/assets/README.md`**:
   - Rabbit artwork license (RC-035)
   - Application icons
   - References to check_rabbit_art_license.py

4. **Validated `THIRD_PARTY_NOTICES.md`** (existing, auto-generated):
   - Has pypi, npm, and Reused Source Code sections
   - References license URLs
   - No third-party source code approved as reused

5. **Created `scripts/check_rc282_license_files.py`** — 5 validation groups

6. **Created `backend/tests/test_rc282_license_files.py`** — 25 tests across 6 classes

## License File Inventory

| File | Purpose | Status |
| --- | --- | --- |
| `LICENSE` | MIT primary license | ✓ (existing) |
| `NOTICE` | Attribution notices | ✓ (created by RC-282) |
| `THIRD_PARTY_NOTICES.md` | Auto-generated dependency list | ✓ (existing) |
| `docs/licenses/models/README.md` | Model license references | ✓ (created by RC-282) |
| `docs/licenses/assets/README.md` | Asset license references | ✓ (created by RC-282) |

## Verification Results

- `python scripts/check_rc282_license_files.py` → PASS
- `pytest backend/tests/test_rc282_license_files.py -q` → 25 passed

## Limitations

- THIRD_PARTY_NOTICES.md is auto-generated from third-party-register.yml; some PyPI packages show `UNKNOWN` license and require registry verification
- Full license text for each dependency is not bundled; only SPDX identifiers and URLs are referenced
- Legal review of NOTICE and THIRD_PARTY_NOTICES is recommended before production release
