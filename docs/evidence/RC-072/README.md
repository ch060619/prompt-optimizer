# RC-072 Execution Evidence

- RC ID: RC-072
- Status: PASS for the local Agent budget controller boundary
- Owner: Codex
- Implementation commit: uncommitted working tree (HEAD `5610c00`)
- Scope: Atomically enforce rounds, wall clock, input/output tokens, cost, context, and concurrency;
  warn near limits and terminate safely with concrete budget details.

## Delivered

- Added `BudgetLimits`, `BudgetUsage`, `BudgetNotice`, `BudgetExceeded`, and thread-safe
  `BudgetController`.
- Round start validates and commits input/context/concurrency usage atomically; output and cost
  updates use the same check-before-commit rule.
- Added wall-clock checks, configurable warning thresholds, active-concurrency accounting, and
  concrete dimension/used/limit details on overflow.
- Integrated AgentCore round/input/output accounting, warning events, safe failure termination, and
  guaranteed concurrency release on completed, failed, cancelled, or closed streams.
- Added tests for atomic overflow, warning thresholds, output/cost/context/concurrency limits,
  wall-clock expiry, Agent warning events, and budget termination.

## Verification

| Command or check | Result |
| --- | --- |
| `python -m pytest -q backend/tests/test_rc072_budget.py` | PASS: 4 passed |
| `python -m pytest -q backend/tests/test_rc072_budget.py backend/tests/test_rc071_streaming.py backend/tests/test_rc068_agent_state.py` | PASS: 13 passed |
| `python -m ruff check backend scripts` | PASS |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS: 55 source files |
| `python scripts/workspace.py verify` | PASS: drift, traceability, dependency boundaries, delivery plan, Ruff, Mypy, backend 133 passed, frontend 9 passed, Lint and Build |

## Explicit Limits

This RC provides deterministic local budgeting and Agent integration. Provider-native token/cost
telemetry, distributed concurrency, persistent budget ledgers, and UI budget displays remain later
Provider, session, and UI work. Existing path-migration DeprecationWarnings and the frontend jsdom
navigation warning remain unchanged.

## Environment

- Time: 2026-07-17 18:07:43 +08:00 (Asia/Shanghai)
- Python: 3.12.10
- Node.js: 24.15.0
- npm: 11.12.1
- Git: 2.54.0.windows.1
