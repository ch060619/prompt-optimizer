# ADR-0008：同步、流式传输和桌面控制边界

- RC ID: RC-063
- Status: Accepted for the current local App Server boundary
- Date: 2026-07-17
- Deciders: Rabbit Code engineering

## Decision

Rabbit Code uses one transport per interaction shape:

| Interaction | Transport | Boundary |
| --- | --- | --- |
| CRUD, health, task submission, task lookup and exports | ordinary HTTP | `/api/v1/*` request/response endpoints |
| Agent and optimization output | SSE | server-to-client events with a monotonic `request_id`-scoped `seq` |
| Native desktop control | JSON-RPC 2.0 | bidirectional shell commands and responses; business logic stays in App Server |
| Future bidirectional Agent interaction | WebSocket | reserved; it must reuse the same `StreamEvent` and cursor semantics |

WebSocket is not used as a replacement for ordinary HTTP or durable stream replay. JSON-RPC is not
used for CRUD or Provider traffic. The desktop shell remains limited to the responsibilities in
ADR-0007.

## Stream Contract

- Every confirmed stream event has a `request_id` and a zero-based, monotonic `seq`.
- SSE emits `id: <seq>` and the serialized `StreamEvent`; idle connections emit the `: heartbeat`
  comment every 15 seconds. WebSocket adapters use ping/pong for the equivalent liveness check.
- A reconnect sends the same request identity and resumes after `Last-Event-ID` (or the equivalent
  `StreamCursor.after_seq`). The server replays events with a greater sequence and never allocates
  a new sequence for the same event key.
- A bounded replay buffer must reject an expired cursor with an explicit resync error; it must not
  silently skip confirmed events.
- Tool calls carry a stable `call_id`. The execution ledger returns a completed result for a
  repeated `(request_id, call_id)` and rejects concurrent duplicate execution. Tool side effects
  that can survive a process crash still require an idempotency key and durable storage in later
  Agent Core/storage work.
- Cancellation is idempotent per request. The first cancellation appends one `cancelled` event;
  later cancellation requests return that event, and no later business event is accepted.

The RC-063 implementation is process-local because the current App Server has no durable event
store. `StreamEventLog`, `ToolExecutionLedger`, the SSE encoder, and JSON-RPC models establish the
shared contract. Durable replay, cross-process delivery, and provider-level cancellation are left
explicitly to RC-064, RC-067, RC-071, and RC-073.

## JSON-RPC Control Contract

Desktop control uses JSON-RPC 2.0 request/response frames. Notifications have a null id and no
response. The initial allowed method families are `window.*`, `sidecar.*`, `update.*`, and
`secret.*`; each method remains subject to the desktop command allowlist and startup-token boundary.
Invalid requests use standard JSON-RPC errors, and a control request has a finite timeout so a
disconnected shell cannot block the App Server.

## Consequences

- Clients can use one event model whether the adapter is SSE today or WebSocket later.
- Reconnect does not rerun a confirmed tool call and does not discard events already accepted by the
  stream log.
- The process-local buffer is not a crash-recovery guarantee. Moving it to SQLite or a durable event
  journal is a separate storage/lifecycle decision and must preserve the same cursor contract.
