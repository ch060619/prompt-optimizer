# ADR-0006：候选 Agent 架构基线

- RC ID: RC-057
- Status: Proposed；Windows prototype passed，Linux/Tauri/package validation pending
- Date: 2026-07-17
- Deciders: Rabbit Code engineering

## Context

RC-056 established the workspace boundary. The repository still needs one small vertical proof that
the Python Agent Core, local App Server, CLI event consumer, and React/Tauri boundary can share one
stream contract. This ADR is a candidate baseline, not a claim that the production Agent Core or
desktop shell is complete.

## Candidate

The prototype uses the following flow:

```text
ProviderEvent -> AgentCore -> AgentEvent -> prototype App Server SSE
                                  +-> CLI JSON lines
                                  +-> React/Tauri consumer boundary
```

- `backend/rabbit_code/agent.py` maps the RC-049 Provider event stream and checks a shared
  cancellation event between provider events.
- `backend/rabbit_code/prototype_app.py` exposes `/health` and `/agent/stream` without changing the
  existing FastAPI compatibility surface.
- `backend/rabbit_code/cli.py` prints the same Agent event sequence as JSON lines.
- The existing React/Vite product remains the current GUI implementation; Tauri is still a shell
  boundary and has no production code in this prototype.

The candidate keeps Python/FastAPI as the core/server path and React/TypeScript as the GUI path,
consistent with ADR-0002. A separate TypeScript Agent Core was not built, so no cross-language
performance conclusion is claimed.

## Evidence

The deterministic Agent Core, prototype App Server, and CLI tests pass. The Windows-only process
probe starts the prototype App Server, receives `started`, `delta`, and `completed` SSE events, and
leaves no process after termination. Cancellation is verified in-process before `completed`.
Machine-readable measurements are in `docs/benchmarks/rc-057-windows.json`.

## Decision Status

Keep this as the candidate baseline for subsequent RC-058 and RC-059 work, subject to the following
required confirmations:

- run the same startup, event, cancellation, and packaging probe on a supported Linux machine;
- build and inspect the Tauri desktop shell with the React assets;
- add a reproducible TypeScript alternative benchmark only if a real alternative implementation is
  authorized and needed for the decision.

Until those checks exist, RC-057 remains pending and this document must not be read as a completed
cross-platform release decision.
