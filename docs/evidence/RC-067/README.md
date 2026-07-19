# RC-067 Execution Evidence

- RC ID: RC-067
- Status: PASS for the local Python App Server lifecycle manager
- Owner: Codex
- Implementation commit: uncommitted working tree (HEAD `5610c00`)
- Scope: Start and supervise the local sidecar with a random loopback port, readiness and protocol
  checks, per-start startup token, restart limits, graceful shutdown, force-kill fallback, and
  exited-process cleanup.

## Delivered

- Added `SidecarManager` and `SidecarConnection` in `backend/rabbit_code/sidecar.py`.
- Added a strict sidecar entry point that reads the supervisor-provided token and protocol version
  from the child environment before constructing the App Server.
- Added random loopback port reservation, health readiness polling, protocol mismatch errors, and
  actionable startup/port failure messages.
- Added a daemon exit monitor with a bounded restart budget, fresh port/token on recovery, graceful
  terminate then timeout kill fallback, and process output reaping.
- Added real subprocess tests for startup/token/health/stop, crash recovery, startup failure,
  occupied port, protocol mismatch, and forced kill with no restart budget.

## Verification

| Command or check | Result |
| --- | --- |
| `python -m pytest -q backend/tests/test_rc067_lifecycle.py` | PASS: 6 passed |
| `python -m ruff check backend scripts` | PASS |
| `python -m mypy backend/src backend/rabbit_code packages/protocol/rabbit_code_protocol` | PASS: 51 source files |
| `python scripts/workspace.py verify` | PASS: drift, traceability, dependency boundaries, delivery plan, Ruff, Mypy, backend 109 passed, frontend 9 passed, Lint and Build |

## Explicit Limits

This RC verifies the local Python/Uvicorn sidecar manager on Windows. Tauri/Rust integration,
Linux packaging, OS-specific process-group semantics, and production installer upgrade behavior
remain dependent on the pending RC-057/RC-060 platform confirmations and later release work.
Existing path-migration DeprecationWarnings and the frontend jsdom navigation warning remain
unchanged.

## Environment

- Time: 2026-07-17 17:33:40 +08:00 (Asia/Shanghai)
- Python: 3.12.10
- Node.js: 24.15.0
- npm: 11.12.1
- Git: 2.54.0.windows.1
