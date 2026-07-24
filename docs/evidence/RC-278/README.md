# RC-278: Release Channels (nightly/beta/stable)

## Status

**Complete** — Channel management, changelog, migration gates all implemented and tested.

## What Was Done

1. **CHANGELOG.md** (project root):
   - Keep a Changelog format with Semantic Versioning reference
   - Release channels table: nightly (10%), beta (25%), stable (100%)
   - Version patterns: `X.Y.Z` (stable), `X.Y.0-beta.N` (beta), `X.Y.Z-dev.YYYYMMDD` (nightly)
   - [3.0.0] release entry with breaking changes and database migration notes

2. **Release channels module** (`backend/src/prompt_optimizer/release_channels.py`):
   - `ChannelConfig` dataclass with version pattern, rollout %, min schema version
   - `MigrationGate` class: `can_start()`, `needs_migration()`, `is_incompatible()`, `get_status()`
   - `parse_channel_from_version()`: determines channel from version string
   - `validate_version_for_channel()`: validates version matches channel pattern
   - Three channel configs with different rollout percentages and schema requirements

3. **Migration gate**:
   - Refuses startup if DB schema is newer than app supports
   - Allows startup with migration if DB is older
   - Integrates with existing `TARGET_SCHEMA_VERSION` from `migrations.py`

4. **Validation script** and **25 tests** (all pass)

## Verification

- `python scripts/check_rc278_release_channels.py` → PASS
- `.venv\Scripts\python.exe -m pytest backend/tests/test_rc278_release_channels.py -q` → 25 passed
