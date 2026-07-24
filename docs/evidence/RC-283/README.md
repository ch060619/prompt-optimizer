# RC-283: Prohibit Mislabeling Claude Code Proprietary Components

## Status

**Complete** — Dedicated check script scans source tree, dependency manifests, documentation, SBOM, and denylist for Claude Code proprietary markers. 36 tests passed. Zero proprietary hits in product source.

## What Was Done

1. **Created `scripts/check_rc283_claude_prohibited.py`** with 6 validation groups:
   - `scan_source_tree()`: Scans backend/src, frontend/src, scripts, docs for Claude proprietary markers
   - `check_dependency_manifests()`: Checks pyproject.toml, package.json, package-lock.json, Cargo.toml
   - `check_documentation_mislabeling()`: Scans docs and README for mislabeling patterns
   - `check_denylist_covers_claude()`: Verifies RC-023 denylist covers Claude Code artifacts
   - `check_external_integration_marking()`: Verifies ADR-0013 and ADR-0004 mark Claude as external
   - `check_sbom_zero_claude()`: If SBOM exists, verifies zero Claude proprietary components

2. **Created `backend/tests/test_rc283_claude_prohibited.py`** — 36 tests across 5 classes:
   - TestCheckScript (7 tests): Validates check script structure
   - TestDenylist (2 tests): Validates denylist covers Claude artifacts
   - TestADRs (3 tests): Validates ADR-0013 and ADR-0004 exist and mark external
   - TestNoProprietaryInDependencies (18 parametrized tests): Scans all dependency manifests
   - TestNoMislabeling (5 parametrized tests): Scans README for mislabeling patterns

3. **Excluded legitimate references**: Check scripts and the execution plan itself reference Claude Code terms for audit purposes — these are excluded from the scan, not flagged as violations.

## Prohibited Markers

The following markers must NOT appear in product source or dependencies:

| Marker | Type |
| --- | --- |
| `claude-code-sourcemap` | Source map restoration artifact |
| `claude-code-rev` | Reverse engineering artifact |
| `claude-code-source-code-deobfuscation` | Deobfuscation artifact |
| `@anthropic-ai/claude-code` | Claude CLI npm package |
| `claude-code/cli` | Claude CLI module |
| `claude-code/sdk` | Claude SDK module |

## Existing Protections (from earlier RCs)

- **RC-023**: `source-map-denylist.yml` blocks Claude Code source map repos
- **RC-024**: `check_proprietary_content_policy.py` scans for forbidden literals
- **RC-026**: `check_independent_design.py` validates independent design provenance
- **RC-028**: `check_mit_analysis_source_audit.py` audits MIT analysis source
- **ADR-0004**: Claude Agent SDK rights boundary
- **ADR-0013**: Claude Code provider boundary (marks as external/official)

## Verification Results

- `python scripts/check_rc283_claude_prohibited.py` → PASS
- `pytest backend/tests/test_rc283_claude_prohibited.py -q` → 36 passed

## Limitations

- Binary artifact scanning (e.g., compiled .exe, .dll) is not performed; SBOM scanning covers declared dependencies
- Full SBOM scan requires `generate_sbom.py` to have been run first
- Network-level scanning (e.g., Claude API calls in runtime) is out of scope for this static check
