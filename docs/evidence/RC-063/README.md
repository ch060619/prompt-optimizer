# RC-063 Execution Evidence

- RC ID: RC-063
- Status: PASS for the accepted local transport boundary
- Owner: Codex
- Implementation commit: `300e450`
- Scope: Define HTTP/SSE/WebSocket/JSON-RPC boundaries and verify cursor replay, cancellation,
  heartbeat, JSON-RPC validation, event-key idempotency, and duplicate tool-call protection.

## Delivered

- Added `docs/adr/0008-transport-boundaries-and-reconnect.md` with Accepted status and explicit
  transport ownership, heartbeat, cursor, reconnect, cancellation, and desktop-control rules.
- Added versioned JSON-RPC request/response/error models and a `progress` stream event type to the
  shared protocol package.
- Added the process-local `StreamEventLog`, SSE encoder, cancellation semantics, and
  `ToolExecutionLedger`. The event log replays only events after the supplied cursor, preserves
  event keys across retries, and reports expired cursors instead of dropping events.
- Added deterministic tests covering reconnection after a confirmed tool event, no duplicate tool
  execution, cancellation retries, SSE ids/heartbeats, bounded cursor failure, and JSON-RPC
  round-trip/validation.

## Verification

| Command or check | Result |
| --- | --- |
| `python -m pytest backend/tests/test_rc063_transport.py -q` | PASS: 5 passed |
| `python -m ruff check packages/protocol/rabbit_code_protocol backend/tests/test_rc063_transport.py` | PASS |
| `python -m mypy packages/protocol/rabbit_code_protocol` | PASS |
| `python scripts/workspace.py verify` | PASS: drift, traceability, delivery plan, Ruff, Mypy, backend 88 passed, frontend 9 passed, Lint and Build |

## Explicit Limits

The event log and tool ledger are process-local. They prove the transport contract and reconnect
behavior for the current local boundary, but do not claim crash recovery or cross-process durable
replay. Those guarantees remain part of later SQLite, lifecycle, and Agent Core work. Existing
migration and frontend jsdom warnings remain unrelated repository conditions.

## Environment

- Time: 2026-07-17 16:39:48 +08:00 (Asia/Shanghai)
- Python: 3.12.10
- Node.js: 24.15.0
- npm: 11.12.1
- Git: 2.54.0.windows.1
