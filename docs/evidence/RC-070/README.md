# RC-070 Execution Evidence

- RC ID: RC-070
- Status: PASS for the shared local permission policy boundary
- Owner: Codex
- Implementation commit: uncommitted working tree (HEAD `5610c00`)
- Scope: Define Plan, Edit, and high permission modes; enforce read-only/workspace/dangerous-action
  rules; require explicit mode changes and dangerous confirmations; preserve task capability
  snapshots.

## Delivered

- Added shared `PermissionMode`, `PermissionDecision`, `ModeChangeEvent`, and `PermissionPolicy`
  types for CLI, GUI integration, and background task consumers.
- Plan allows read/list/search only; Edit allows workspace-contained writes; high mode permits
  dangerous actions only after explicit per-action approval.
- Normalized paths before workspace checks, defaulted missing write paths to deny, and recorded every
  explicit mode change with actor and sequence.
- Bound background tasks to the mode present at task creation so later session mode changes cannot
  expand their permissions.
- Added matrix tests for all modes, workspace escape, explicit switching, dangerous confirmation,
  task snapshots, and Protocol compatibility.

## Verification

| Command or check | Result |
| --- | --- |
| `python -m pytest -q backend/tests/test_rc070_permissions.py` | PASS: 5 passed |
| `python -m pytest -q backend/tests/test_rc070_permissions.py backend/tests/test_rc068_agent_state.py backend/tests/test_rc069_cli_modes.py` | PASS: 16 passed |
| `python -m ruff check backend scripts` | PASS |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS: 53 source files |
| `python scripts/workspace.py verify` | PASS: drift, traceability, dependency boundaries, delivery plan, Ruff, Mypy, backend 125 passed, frontend 9 passed, Lint and Build |

## Explicit Limits

This RC establishes the shared policy and event boundary. The repository does not yet contain a
GUI Agent tool execution surface, so GUI controls are not claimed as implemented; later tool/UI RCs
must consume this policy instead of defining a second matrix. Tool registry, filesystem operations,
terminal sandboxing, and broader security hardening remain later RCs.

## Environment

- Time: 2026-07-17 17:56:22 +08:00 (Asia/Shanghai)
- Python: 3.12.10
- Node.js: 24.15.0
- npm: 11.12.1
- Git: 2.54.0.windows.1
