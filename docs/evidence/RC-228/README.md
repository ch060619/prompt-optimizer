# RC-228 Evidence

<!-- RC ID: RC-228 -->

## Scope

Completed the local model resource-control boundary:

- `LocalRunnerGateway` derives conservative defaults from a hardware report,
  passes the resulting `RunnerResourceConfig` to runner creation, and keeps
  concurrency bounded by a semaphore.
- Queue status reports active, pending, capacity, and available slots; requests
  beyond the configured queue remain finite `runner_busy` failures with a
  `wait_and_retry` action.
- Idle gateways accept an explicit lower resource configuration for threads,
  GPU layers, context, concurrency, idle timeout, and temperature limit. Active
  work rejects reconfiguration until it is safe.
- Optional runner temperature and out-of-memory signals are surfaced without
  inventing unavailable hardware readings; API routes expose resource config,
  queue state, and the signal to the client.

## Verification

- `.venv\Scripts\python.exe -m pytest backend/tests/test_rc228_resources.py backend/tests/test_rc196_runner_resources.py backend/tests/test_rc198_runner_gateway.py backend/tests/test_rc193_health.py backend/tests/test_rc194_local_model_state.py backend/tests/test_rc227_resilience.py backend/tests/test_rc151_routing_resilience.py backend/tests/test_rc171_network_resilience.py backend/tests/test_rc225_recovery.py backend/tests/test_api_contract.py -q`: 52 passed.
- Targeted Ruff check: passed.
- Strict Mypy for runner resources, local Provider, and Gateway: passed.
- Generated OpenAPI artifacts and API contract tests: passed.

## Residual limits

Temperature and OOM values are optional signals supplied by a real runner; the
in-memory fixture reports no fabricated temperature or memory values. No real
Ollama/llama.cpp process, GPU telemetry, thermal throttling, or cross-platform
hardware stress run was available. The queue and resource controls are process
local and do not claim to manage an external runner's own scheduler.
