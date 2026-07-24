# RC-286: Confirm Asset Publication Rights

## Status

**Complete** — All 6 asset categories confirmed with publication rights. 23 tests passed.

## What Was Done

1. **Created `docs/legal/asset-publication-rights.yml`** — Comprehensive register covering:
   - **Rabbit artwork**: user-authorized, links to RC-035 evidence
   - **App icons**: project-created, MIT, covers icon.ico/icon.png/favicon.svg
   - **Fonts**: not-applicable (no custom fonts bundled)
   - **Screenshots**: project-created, MIT
   - **Doc images**: project-created, MIT
   - **Demo repo**: project-created, MIT

2. **Created `scripts/check_rc286_asset_rights.py`** — 6 validation groups:
   - Register exists with all required categories
   - Each category has status/license/rights_holder/notes
   - all_categories_confirmed is true, blocking_categories is empty
   - Rabbit artwork links to RC-035 evidence
   - Icon files exist on disk
   - Fonts category is not-applicable

3. **Created `backend/tests/test_rc286_asset_rights.py`** — 23 tests across 8 classes

## Asset Categories Summary

| Category | Status | License | Evidence |
| --- | --- | --- | --- |
| Rabbit artwork | user-authorized | rabbit-code-project-release-permission | RC-035 (rabbit-art-license.yml) |
| App icons | project-created | MIT | docs/licenses/assets/README.md |
| Fonts | not-applicable | N/A | No custom fonts bundled |
| Screenshots | project-created | MIT | docs/screenshots/ |
| Doc images | project-created | MIT | docs/ |
| Demo repo | project-created | MIT | README.md |

## Verification Results

- `python scripts/check_rc286_asset_rights.py` → PASS
- `pytest backend/tests/test_rc286_asset_rights.py -q` → 23 passed

## Limitations

- Rabbit artwork commercial use remains "pending" in RC-035 register; open-source use is allowed
- Screenshot directory is empty (screenshots will be generated before first public release)
- Font licensing could change if a web font is added in the future
