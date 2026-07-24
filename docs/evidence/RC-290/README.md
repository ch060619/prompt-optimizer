# RC-290: Post-Release Maintenance Policy and Milestone Tracking

## Status

**Complete** — MAINTENANCE.md created with 7 policy sections. R1-R6 milestone tracking verified. 23 tests passed.

## What Was Done

1. **Created `docs/MAINTENANCE.md`** with 7 sections:
   - **Versioning**: Semantic Versioning (MAJOR.MINOR.PATCH)
   - **Release Cadence**: Stable (2-3 months), Beta (2-4 weeks), Nightly (every push)
   - **Compatibility Policy**: Python 3.10+, Windows 10+, Linux Ubuntu 20.04+, API v1 prefix
   - **Security Patch Policy**: Critical (7d), High (14d), Medium (30d), Low (next release)
   - **Dependency Update Cadence**: Dependabot weekly, major quarterly, security fast-tracked
   - **Deprecation Policy**: Deprecated for one MINOR, removed in next MAJOR
   - **End of Life**: 6 months security patches after next MAJOR

2. **Verified R1-R6 milestone tracking**:
   - **R1**: Execution plan has progress table and completion log ✓
   - **R2**: third-party-register.yml exists (competitive research) ✓
   - **R3**: ADR-0003 (OpenCode boundary) + ADR-0017 (license selection) ✓
   - **R4**: asset-publication-rights.yml exists ✓
   - **R5**: support-matrix.md defines Windows + Linux scope ✓
   - **R6**: Pre-release checklist (RC-289) + CHANGELOG + GOVERNANCE ✓

3. **Created `scripts/check_rc290_maintenance.py`** — 7 validation groups

4. **Created `backend/tests/test_rc290_maintenance.py`** — 23 tests across 8 classes

## Verification Results

- `python scripts/check_rc290_maintenance.py` → PASS
- `pytest backend/tests/test_rc290_maintenance.py -q` → 23 passed

## Limitations

- Actual release cadence depends on maintainer availability
- EOL policy is a commitment, not enforced by code
- Backporting security patches to previous stable requires manual release branch management
