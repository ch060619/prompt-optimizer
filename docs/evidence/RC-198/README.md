# RC-198 Evidence

## Scope

Added `LocalRunnerGateway` as the FastAPI boundary for Ollama and llama.cpp adapters. The gateway provides model listing, capabilities, health, generate, stream, cancel, load, and unload operations without runner-specific command construction in the API layer. Request IDs own cancellation events, bounded concurrency provides a queue/rejection contract, health responses use a TTL cache, and runner failures become structured retry/recovery errors. Streaming emits `started`, `delta`, `completed`, `cancelled`, or `error` events.

## Verification

- `python -m pytest backend/tests/test_rc198_runner_gateway.py -q`: 5 passed, 6 existing path-migration warnings.
- RC-187/RC-193/RC-196/RC-198 association regression: 12 passed, 6 existing warnings.
- Broader RC-149/RC-173/RC-187/RC-193/RC-196/RC-198 association: 38 passed, 1 skipped, 17 existing warnings.
- Frontend full suite: 22 test files, 102 passed.
- Frontend ESLint and TypeScript/Vite build: passed.
- RC-198 backend Ruff, strict Mypy, compileall, and `python scripts/generate_api.py --check`: passed.
- `python scripts/workspace.py check`: passed during the preceding RC-197/RC-198 gate.

The FastAPI contract test injects the gateway, loads an in-memory model through the adapter, exercises generate and SSE stream routes, and unloads the model. The gateway tests cover TTL reuse/expiry, cancellation as a terminal stream event, and rejection beyond the configured concurrency capacity.

## Residual limits

Real Ollama/llama.cpp processes, runner HTTP APIs, model weights, GPU hardware, and cross-process queue fault injection were not run. A full `workspace.py verify` remains blocked by the pre-existing Ruff `I001` import-order issue at `backend/tests/test_rc153_system_prompt.py:1`; that unrelated file remains untouched. Existing path migration and frontend jsdom navigation warnings remain non-blocking.
