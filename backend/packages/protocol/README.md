# Protocol Boundary

`packages/protocol` owns versioned request, response, event, error, and capability schemas shared
by the desktop shell, CLI, App Server, and future Agent Core.

RC-063 transport rules use HTTP for CRUD and health, SSE for server-to-client Agent/optimization
streams, and JSON-RPC for bidirectional desktop control. `StreamEventLog` provides the process-local
cursor/replay contract used by both SSE and a future WebSocket adapter; persistent replay storage and
cross-process delivery are intentionally deferred to later storage and lifecycle tasks.
