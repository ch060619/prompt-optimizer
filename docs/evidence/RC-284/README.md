# RC-284: Preserve Codex/OpenCode Attribution and Modification Declarations

## Status

**Complete** — ADR-0003, research register, module map, NOTICE, and THIRD_PARTY_NOTICES all verified. No unattributed OpenCode code in product source. 29 tests passed.

## What Was Done

1. **Created `scripts/check_rc284_opencode_attribution.py`** with 6 validation groups:
   - `check_adr_0003()`: Verifies ADR-0003 exists, references MIT, states no upstream code, references NOTICE
   - `check_research_register()`: Verifies fixed upstream commit SHA, MIT license, concepts-only policy, repo reference
   - `check_module_map()`: Verifies module map exists and references agent/CLI modules
   - `check_notice_references()`: Verifies NOTICE references OpenCode and ADR-0003
   - `check_no_unattributed_opencode_code()`: Scans backend/src and frontend/src for unattributed OpenCode copyright patterns
   - `check_third_party_reuse_section()`: Verifies THIRD_PARTY_NOTICES has "Reused Source Code" section confirming no approved reuse

2. **Created `backend/tests/test_rc284_opencode_attribution.py`** — 29 tests across 7 classes

## Existing Attribution Infrastructure

| Artifact | Purpose | Status |
| --- | --- | --- |
| `docs/adr/0003-opencode-research-boundary.md` | Documents OpenCode research boundary | ✓ (existing, RC-018) |
| `docs/research/opencode-research-register.yml` | Fixed upstream commit, MIT license, reuse policy | ✓ (existing, RC-018) |
| `docs/research/opencode-module-map.md` | Module boundary mapping | ✓ (existing, RC-018) |
| `NOTICE` | References OpenCode and ADR-0003 | ✓ (created by RC-282) |
| `THIRD_PARTY_NOTICES.md` | "Reused Source Code" section confirms no approved reuse | ✓ (existing, RC-032) |

## Key Facts

- **Upstream repository**: `anomalyco/opencode` at commit `453b61e27b2f6c2752a60dd7d8412bdcf4e0aa3d`
- **Upstream license**: MIT
- **Reuse policy**: `concepts-only-no-upstream-code` — no OpenCode source code is approved for Rabbit Code
- **NOTICE obligation**: If future file-level reuse is needed, a separate source register and license review is required (per ADR-0003)

## Verification Results

- `python scripts/check_rc284_opencode_attribution.py` → PASS
- `pytest backend/tests/test_rc284_opencode_attribution.py -q` → 29 passed

## Limitations

- If future file-level reuse from OpenCode is approved, copyright headers and modification declarations must be added per file
- Automated pre-merge header check is limited to pattern scanning; semantic similarity review remains manual (per RC-024)
