# RC-271 Evidence

<!-- RC ID: RC-271 -->

## Scope

Added `scripts/check_docs.py` and `backend/tests/test_rc271_docs.py`. The gate checks the controlled user/contributor docs for local links, screenshot assets, command script references, required installation markers, and hand-entered performance metrics. It extracts explicitly marked safe Python/pytest smoke blocks and runs them in CI without network, model downloads, or destructive cleanup.

## Verification

- `python scripts/check_docs.py --run`: passed; all controlled documents, links/assets, installation markers, and 3 marked smoke commands passed.
- `python -m pytest backend/tests/test_rc271_docs.py -q`: 2 passed.
- `.github/workflows/ci.yml` runs the gate in the backend job.

## Limits

PowerShell, Docker, cargo, Provider, VM installation, and model-download commands are checked for documented entry points but are not executed by this safe CI gate. Their real execution remains in platform/release jobs with explicit environments.

## RC-230~271 remediation follow-up (2026-07-19)

The documentation gate now includes the Agents navigation, Grok analysis,
cleanup, and remediation reports. All report links resolve locally. Frontend
dependency security uses the explicit `npm run audit:production` command against
the npm advisory service; production and full audits report zero known
vulnerabilities after the Vite 8/Vitest 4 upgrade.
