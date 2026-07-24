# ADR-0017: Primary License Selection (MIT)

Date: 2026-07-22
Status: Accepted
Supersedes: None

## Context

Rabbit Code needs a primary open-source license that:

1. Is compatible with existing dependencies (Python: FastAPI/Pydantic/Typer/uvicorn; Node: Vite/React/Vitest)
2. Allows reuse of Codex/OpenCode-derived components (already MIT-licensed per ADR-0003)
3. Permits redistribution in pip wheels, Tauri desktop installers, and Docker images
4. Does not impose patent retaliation clauses that conflict with project goals
5. Is recognized by PyPI, npm, winget, and Scoop package registries

## Decision

**Adopt MIT as the primary license for Rabbit Code.**

The root `LICENSE` file, `backend/pyproject.toml`, `frontend/package.json`, and `apps/desktop/src-tauri/tauri.conf.json` all declare MIT.

## Analysis

### MIT vs Apache-2.0 Comparison

| Criterion | MIT | Apache-2.0 |
| --- | --- | --- |
| Permissiveness | Very permissive | Permissive with patent grant |
| Patent protection | None | Explicit patent grant + retaliation |
| NOTICE obligation | Copyright notice + license text | Copyright notice + license text + NOTICE file |
| Complexity | Simple (1 paragraph) | Complex (full text + appendices) |
| Dependency compatibility | All deps are MIT/BSD/Apache-2.0 compatible | All deps compatible |
| Codex/OpenCode reuse | Direct compatibility (both MIT) | Compatible but adds NOTICE overhead |
| PyPI/npm/winget/scoop | All recognize MIT | All recognize Apache-2.0 |
| Contributor friction | Minimal (no CLA needed) | May require CLA for patent clarity |

### Why MIT

1. **Dependency compatibility**: All Python dependencies (FastAPI=MIT, Pydantic=MIT, Typer=MIT, uvicorn=BSD-3-Clause) and frontend dependencies (Vite=MIT, React=MIT, Vitest=MIT) are compatible with MIT. No dependency requires Apache-2.0 or GPL.

2. **Codex/OpenCode reuse**: ADR-0003 established that reused components from OpenCode are MIT-licensed. Using MIT for Rabbit Code avoids license incompatibility and NOTICE file overhead.

3. **Simplicity**: MIT is the simplest permissive license. No patent litigation clauses, no state-by-state legal variations, no appendix requirements. This reduces friction for contributors and distributors.

4. **Distribution**: MIT is recognized by all target registries (PyPI, npm, winget, Scoop). Tauri desktop installers can bundle MIT-licensed code without additional obligations.

5. **Patent considerations**: The project does not hold patents on its core algorithms. The offline analysis rules, template library, and provider adapters do not involve patentable inventions. Apache-2.0's patent grant would add complexity without benefit.

### Third-Party License Obligations

The following non-MIT licenses appear in dependencies:

- **BSD-3-Clause** (uvicorn, some Node packages): Requires copyright notice retention. Covered by THIRD_PARTY_NOTICES (RC-282).
- **MPL-2.0** (some Node packages): File-level copyleft. These are used unmodified; MPL-2.0 allows MIT-licensed projects to use MPL-2.0 dependencies.
- **Apache-2.0** (some Node packages): Compatible with MIT; NOTICE obligations handled by THIRD_PARTY_NOTICES.
- **0BSD** (some Node packages): Public domain equivalent; no obligations.

None of these are overridden by the MIT primary license. Each retains its own terms as documented in THIRD_PARTY_NOTICES.

## Consequences

- All source files are MIT-licensed unless explicitly noted otherwise.
- Contributors do not need to sign a CLA; the MIT license covers contributions implicitly.
- The project does not provide patent protection to users. If patent protection becomes important, a future ADR can add Apache-2.0 for specific modules.
- THIRD_PARTY_NOTICES (RC-282) must list all non-MIT dependencies with their license texts.
- The NOTICE file (RC-282) will contain the MIT copyright notice and attribution for Codex/OpenCode (RC-284).

## Verification

- `LICENSE` file exists at root with MIT text ✓
- `backend/pyproject.toml` declares `license = { text = "MIT" }` ✓
- `frontend/package.json` declares `"license": "MIT"` (added by RC-281)
- `apps/desktop/src-tauri/tauri.conf.json` declares `"license": "MIT"` (added by RC-281)
- `scripts/check_rc281_license.py` validates consistency ✓
