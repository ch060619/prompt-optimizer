# RC-291: Claude Code Source Map Exposure Repository List and Clean-Room Verification

## Status

**Complete** — All existing infrastructure from RC-023/025/028/030 verified and formalized. 27 tests passed.

## What Was Done

1. **Created `scripts/check_rc291_source_map.py`** with 5 validation groups:
   - `check_denylist()`: Verifies 5 blocked repositories, URLs, and hashes
   - `check_legal_assessment()`: Verifies risk evaluation covers copyright, trade secret, usage scope
   - `check_role_register()`: Verifies researcher/implementer/reviewer roles with allowed_inputs and prohibited
   - `check_info_boundary()`: Verifies information boundary references all three roles
   - `check_boundary_scripts()`: Verifies check_clean_room_boundary.py and check_clean_room_rewrite.py exist

2. **Fixed `clean-room-role-register.yml`**: Added "prohibited" field to reviewer role

3. **Fixed `clean-room-information-boundary.md`**: Added English role names (researcher/implementer/reviewer) alongside Chinese terms

4. **Created `backend/tests/test_rc291_source_map.py`** — 27 tests across 6 classes

## Existing Infrastructure (from earlier RCs)

| Artifact | RC | Purpose |
| --- | --- | --- |
| `docs/research/source-map-denylist.yml` | RC-023 | 5 blocked repos, URLs, hashes, artifact names |
| `docs/legal/claude-source-map-clean-room.md` | RC-030 | Legal assessment with risk table, usage scope |
| `docs/legal/clean-room-role-register.yml` | RC-025 | Researcher/implementer/reviewer roles |
| `docs/legal/clean-room-information-boundary.md` | RC-025 | Information flow and audit rules |
| `scripts/check_clean_room_boundary.py` | RC-025 | Boundary enforcement check |
| `scripts/check_clean_room_rewrite.py` | RC-026 | Mechanical rewrite detection |

## Verification Results

- `python scripts/check_rc291_source_map.py` → PASS
- `pytest backend/tests/test_rc291_source_map.py -q` → 27 passed

## Limitations

- Clean-room role register status remains `pending-human-signoff` — actual human assignment required
- Legal assessment is not a legal opinion; qualified attorney review recommended before production
- Source map repositories may change or new ones may appear; denylist requires periodic updates
