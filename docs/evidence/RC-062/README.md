# RC-062 Execution Evidence

- RC ID: RC-062
- Status: PASS
- Owner: Codex
- Implementation commit: `1da1f5e`
- Prerequisites: RC-061 protocol package and RC-048 versioned OpenAPI baseline
- Scope: Generate TypeScript schemas and a typed `/api/v1` client from the live FastAPI OpenAPI contract; wire generation and drift checking into root tasks and CI.

## Delivered

- Added `scripts/generate_api.py`, which reads the live `app.openapi()` result, checks it against `docs/api/openapi-v1.json`, and deterministically generates `frontend/src/generated/schema.ts` and `frontend/src/generated/client.ts`.
- Added `scripts/generate-api.ps1` and the `generate-api` workspace task for the documented Windows generation path.
- Added `--check` drift validation to the root `check`/`verify` task and CI. A stale OpenAPI baseline or generated file fails the check.
- Replaced the hand-maintained frontend DTO declarations with a type-only re-export from the generated schema. The frontend API facade now delegates HTTP CRUD calls to the generated client.
- Kept SSE event parsing in `frontend/src/api.ts` because the current OpenAPI stream response has no event schema; the next transport-boundary task owns that contract.

## Verification

| Command or check | Result |
| --- | --- |
| Before implementation: `pytest backend/tests/test_rc062_codegen.py -q` | FAIL as expected: generator module and generated type export were absent |
| `pytest backend/tests/test_rc062_codegen.py -q` | PASS: 2 passed |
| `python scripts/generate_api.py --check` | PASS: generated API artifacts are up to date |
| `scripts/generate-api.ps1` | PASS: regenerated both TypeScript artifacts |
| `python scripts/check_rc_traceability.py --rc RC-062` | PASS: RC-062 is GREEN |
| `python scripts/workspace.py verify` | PASS: workspace check, drift check, traceability, delivery plan, Ruff, Mypy, backend 83 passed, frontend 9 passed, lint, and build |

The full verification retained the existing data-directory migration `DeprecationWarning` and the existing jsdom navigation warning. No real Provider request, API key, or paid resource was used.

## Remaining Work

- RC-063 owns the broader synchronization/SSE/WebSocket/JSON-RPC transport boundary and reconnection semantics.
- RC-057 Linux/Tauri/TypeScript and RC-060 Rust/Tauri/Keychain confirmations remain pending because those external toolchains are unavailable; they do not block this local generation chain.

## Environment

- Time: 2026-07-17 16:22:05 +08:00 (Asia/Shanghai)
- Python: 3.12.10
- Node.js: 24.15.0
- npm: 11.12.1
- Git: 2.54.0.windows.1
