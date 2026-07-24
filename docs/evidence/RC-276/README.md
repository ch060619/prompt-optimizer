# RC-276: Secure Update Check and Rollback

## Status

**Complete** — Update checker, rollback manager, version compatibility, CLI command, manifest template all implemented and tested.

## What Was Done

1. **Update checker module** (`backend/src/prompt_optimizer/update_checker.py`):
   - `UpdateChecker` class: HTTPS-based update check via manifest URL
   - `UpdateInfo` dataclass: version, download URL, SHA-256, release notes, channel, rollout percentage, breaking changes
   - `verify_download()`: SHA-256 hash verification of downloaded data
   - `should_offer_update()`: staged rollout based on user rollout ID and percentage
   - `_fetch_manifest()`: HTTPS fetch with User-Agent header and timeout

2. **Rollback manager** (`RollbackManager` class):
   - `backup_current()`: backs up current installation before update
   - `list_backups()`: lists available rollback versions
   - `rollback_to()`: restores from a previous backup

3. **Version compatibility** (`check_version_compatibility()`):
   - Checks minimum required version
   - Warns on major version jumps (>1 major version)
   - Returns `VersionCompatibility` with `is_compatible` and `warnings`

4. **CLI command** (`rabbit check-update`):
   - Added to `backend/src/prompt_optimizer/cli/app.py`
   - Shows update info, compatibility warnings, breaking changes
   - Supports `--channel` option (stable/beta/nightly)

5. **Update manifest template** (`scripts/install/update-manifest.json`):
   - Three channels: stable (100%), beta (25%), nightly (10%)
   - Per-platform download URLs and SHA-256 hashes
   - Breaking changes and min required version per channel

6. **Validation script** (`scripts/check_rc276_update_rollback.py`) and **test** (26 tests)

## Verification

- `python scripts/check_rc276_update_rollback.py` → PASS
- `.venv\Scripts\python.exe -m pytest backend/tests/test_rc276_update_rollback.py -q` → 26 passed
