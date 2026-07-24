# RC-277: SBOM, Artifact Hashes, Supply Chain Manifest

## Status

**Complete** — SBOM generation script, validation, and tests in place.

## What Was Done

1. **Supply chain generation script** (`scripts/generate_sbom.py`):
   - **Build provenance**: git commit/branch/remote, tool versions (Python, Node, npm, cargo, rustc), platform, build time
   - **SBOM** (CycloneDX 1.4 format): all Python (pip list) and npm (package-lock.json) dependencies as components with PURL references
   - **License report**: dependency count, license summary, flagged non-standard licenses
   - **Artifact hashes**: SHA-256 for frontend dist, desktop binary, backend Python files
   - **Vulnerability scan**: pip-audit integration (graceful skip if not installed)
   - **Combined manifest**: `output/supply-chain/manifest.json` linking all artifacts

2. **Validation script** (`scripts/check_rc277_sbom.py`) and **test** (13 tests)

## Output Artifacts

- `output/supply-chain/provenance.json` — build provenance
- `output/supply-chain/sbom.json` — CycloneDX SBOM
- `output/supply-chain/licenses.json` — license report
- `output/supply-chain/artifacts.json` — artifact SHA-256 hashes
- `output/supply-chain/scan-report.json` — vulnerability scan
- `output/supply-chain/manifest.json` — combined manifest

## Verification

- `python scripts/check_rc277_sbom.py` → PASS
- `.venv\Scripts\python.exe -m pytest backend/tests/test_rc277_sbom.py -q` → 13 passed

## Limitations

- pip-audit not installed; vulnerability scan gracefully skips
- npm license info comes from package-lock.json (may be incomplete)
- Actual SBOM generation requires running the script (which requires pip/npm tools)
