# RC-066 Execution Evidence

- RC ID: RC-066
- Status: PASS for replaceable core-module boundaries
- Owner: Codex
- Implementation commit: uncommitted working tree (HEAD `5610c00`)
- Scope: Define Protocol ports for Agent, Provider, Tool, Permission, Storage, and prompt
  optimization; inject replaceable services; block UI and route imports of concrete Providers.

## Delivered

- Added `prompt_optimizer.contracts` with runtime-checkable Protocols for the requested core
  boundaries and diff calculation.
- Added constructor injection to `AppServices`, `VersionService`, `TaskService`, Provider registry,
  offline provider, and Agent runtime consumers.
- Restored `StorageService` in `VersionService` so default storage construction remains available.
- Added `scripts/check_dependency_boundaries.py`, an AST/source check that rejects concrete Provider
  implementation imports and construction from API, CLI, and frontend surfaces.
- Registered the dependency check in root `workspace.py check` and backend CI.
- Added in-memory replacement tests for all requested ports, service injection tests, default storage
  regression coverage, and the repository boundary check.

## Verification

| Command or check | Result |
| --- | --- |
| `python -m pytest -q backend/tests/test_rc066_contracts.py` | PASS: 4 passed |
| `python -m pytest --cov=prompt_optimizer --cov-report=term-missing backend/tests` | PASS: 103 passed |
| `python -m ruff check backend scripts` | PASS |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS: 49 source files |
| `python scripts/check_dependency_boundaries.py` | PASS |
| `python scripts/workspace.py verify` | PASS: drift, traceability, dependency boundaries, delivery plan, Ruff, Mypy, backend 103 passed, frontend 9 passed, Lint and Build |

## Explicit Limits

This RC enforces the current Python/API/CLI/frontend dependency boundary and replaceable ports. It
does not migrate the remaining provider configuration to an OS keychain or complete desktop
process lifecycle behavior; those concerns remain in later migration and RC-067 work. Existing
path-migration DeprecationWarnings and the frontend jsdom navigation warning remain unchanged.

## Environment

- Time: 2026-07-17 17:23:22 +08:00 (Asia/Shanghai)
- Python: 3.12.10
- Node.js: 24.15.0
- npm: 11.12.1
- Git: 2.54.0.windows.1
