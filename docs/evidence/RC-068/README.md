# RC-068 Execution Evidence

- RC ID: RC-068
- Status: PASS for the observable local Agent state machine and checkpoint boundary
- Owner: Codex
- Implementation commit: uncommitted working tree (HEAD `5610c00`)
- Scope: Define the Agent lifecycle states, reject illegal transitions, persist immutable transition
  events as checkpoints, and replay events into the same session state.

## Delivered

- Added `AgentState` and an explicit transition table for received, context, model, tool pending,
  approval, tool running, continuing, completed, failed, and cancelled states.
- Added frozen `AgentStateEvent` and `AgentCheckpoint` values with read-only payload mappings.
- Added `AgentStateMachine` transition validation and deterministic event replay.
- Added in-memory and atomic JSON checkpoint stores; `AgentCore` persists completed, failed, and
  cancelled runs while preserving the existing AgentEvent stream contract.
- Exported state and checkpoint types from the Agent Core package.
- Added tests for legal/illegal transitions, immutable events, JSON round-trip, completion, failure,
  cancellation, and compatibility with the existing RC-057/059 runtime tests.

## Verification

| Command or check | Result |
| --- | --- |
| `python -m pytest -q backend/tests/test_rc068_agent_state.py` | PASS: 5 passed |
| `python -m pytest -q backend/tests/test_rc057_agent_prototype.py backend/tests/test_rc059_runtime.py backend/tests/test_rc068_agent_state.py` | PASS: 10 passed |
| `python -m ruff check backend scripts` | PASS |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS: 52 source files |
| `python scripts/workspace.py verify` | PASS: drift, traceability, dependency boundaries, delivery plan, Ruff, Mypy, backend 114 passed, frontend 9 passed, Lint and Build |

## Explicit Limits

This RC implements the state/checkpoint boundary for the current local Agent Core. Tool execution,
approval policy, budgets, pause/resume, crash recovery from an in-flight external write, and
cross-process durable session orchestration remain later RC concerns. Existing path-migration
DeprecationWarnings and the frontend jsdom navigation warning remain unchanged.

## Environment

- Time: 2026-07-17 17:41:43 +08:00 (Asia/Shanghai)
- Python: 3.12.10
- Node.js: 24.15.0
- npm: 11.12.1
- Git: 2.54.0.windows.1
